# Python + Angular on Google Cloud Platform (App Engine)

It's a simple full stack project with Angular frontend and Python backend
deployable in Goggle Cloud Platform (App Engine).

## Copy ap-basic project into new ap-gcp project

```bash
git clone https://github.com/leliw/ap-basic.git ap-gcp
cd ap-gcp
rm -R -f .git
git init
git branch -m main
```

## Restore development environment

```bash
cd frontend
npm install
cd ..
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
cd ..
```

## Run development instance

```bash
cd backend
uvicorn main:app --reload &
cd ../frontend
ng serve -o
cd ..
```

## Angular static files

GCP App Engine **Standard** can serve static files
independently from python service. It is faster
especially when python service is restarting.

By default, Angular files are compiled into directory
`frontend/dist/frontend/browser/` but I have changed it
to `backend/static` in `frontend\angular.json` file.
So there is only one deployable service (`backend`)
within static files. `app.yaml` file has to reflect that change.

## GCP app.yaml

GCP requires `app.yaml` file in service root directory.
It provides similar information as `Dockerfile` and `nginx.conf`.

- runtime - some kind of base image
- entrypoint - how to run service
- handlers - requests routing

```yaml
runtime: python311
entrypoint: gunicorn -b :$PORT -k uvicorn.workers.UvicornWorker main:app

handlers:

- url: /api/.*
  script: auto

- url: /
  static_files: static/browser/index.html
  upload: static/browser/index.html

- url: /(.+)
  static_files: static/browser/\1
  upload: static/browser/(.+)
```

## GCP .gcloudignore

The second important file is `.gcloudignore`.
It is like `.dockerignore` or `.gitignore`,
specify which files shouldn't be send to GCP.

```text
.gcloudignore
.git
.gitignore

__pycache__/
/setup.cfg

**/.venv
**/__pycache__/
```

## Deployment

First, build Angular project.

```bash
cd frontend
ng build
cd ..
```

Create GCP project as described in
<https://cloud.google.com/appengine/docs/standard/python3/building-app/creating-gcp-project>.

```bash
gcloud init
gcloud app create
```

Then beploy Python project into GCP:

```bash
gcloud app deploy backend/app.yaml
```

## GCP access key

While local development you will have to access some cloud services.
To do that, you have to be authorized. You can do it with a access key.

### Get default service's access key

Go to [IAM & Admin -> Service accounts](https://console.cloud.google.com/iam-admin/serviceaccounts) and
select your project. There shoult be already created `Default compute service account`. Select
`Manage keys` from `Actions` column. Click `Add key` and `Create new key`. Leave `JSON` selected and
click `Create` and save json file in safe place. I used to store keys in `.keys/` project's directory.

**Remeber to add `.keys/*` in `.gitignore` file!!!**

### Apoint saved key to use

To authorize with this saved key you have to set environment variable.

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/home/user/Downloads/service-account-file.json"
```

You can set this variable globally in the `~/.bashrc` or `~/.profile file` but if you develop
several projects it is a problem. You can also set it manually each time but I prefer to set
VSC `RUN AND DEBUG` configuration for each project / workspace. Add something like this to
`*.code-workspace` file.

```json
    "launch": {
        "version": "0.2.0",
        "configurations": [
            {
                "name": "Python: FastAPI",
                "type": "debugpy",
                "request": "launch",
                "module": "uvicorn",
                "env": {
                    "GOOGLE_APPLICATION_CREDENTIALS": "../.keys/ap-gcp.json"
                },
                "args": [
                    "main:app",
                    "--reload",
                ]
            }
        ]
    }
```

or just write `backend/.env` file.

```text
GOOGLE_APPLICATION_CREDENTIALS=../.keys/ap-gcp.json
```

## GCP secrets

When you have to deliver some secret data to the program, you should use
`Secret Manger`. It is designed to store configuration data as passwords, API keys and
certificates. Each secret is identified by `project_id`, `secret_id` and `version_id`.

<https://cloud.google.com/secret-manager/docs/create-secret-quickstart#secretmanager-quickstart-python>

Install the client library

```bash
pip install google-cloud-secret-manager
```

Usually secret is set manulally but also can be set with code.

```python
from google.cloud import secretmanager


class GcpSecrets:

    def __init__(self, project_id: str = None):
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT", project_id)
        if self.project_id is None:
            raise ValueError("GOOGLE_CLOUD_PROJECT environment variable not set.")
        self.client = secretmanager.SecretManagerServiceClient()
        self.parent = f"projects/{self.project_id}"


    def create_secret(self, secret_id: str):
        secret = self.client.create_secret(
            request={
                "parent": self.parent,
                "secret_id": secret_id,
                "secret": {"replication": {"automatic": {}}},
            }
        )
        return secret
```

Project_id defines project in GCP. It is usually set as an evironment variable
(`GOOGLE_CLOUD_PROJECT` or `GCLOUD_PROJECT`).
Secret_id is defined by developer but the secret doesn't have any value.
 You have to add version with specified value. Changing value means adding new version.

```python
    def add_secret_version(self, secret_id: str, payload: str):
        secret_name = f"{self.parent}/secrets/{secret_id}"
        response = self.client.add_secret_version(
            request={"parent": secret_name, "payload": {"data": payload.encode('utf-8')}}
        )
        return response
```

When you want to read the secret value, you have to read sepecified version.
Fortunately, you can list all avaliable versions.

```python
    def list_secret_versions(self, secret_id: str):
        secret_name = f"{self.parent}/secrets/{secret_id}"
        secrets = self.client.list_secret_versions(request={"parent": secret_name})
        return secrets

    def access_secret_version(self, secret_id: str, version_id: str):
        version = f"{self.parent}/secrets/{secret_id}/versions/{version_id}"
        response = self.client.access_secret_version(request={"name": version})
        return response    
```

But usually reading last version of secret is enough.

```python
    def get_secret(self, secret_id: str) -> str:
        version = f"{self.parent}/secrets/{secret_id}/versions/latest"
        response = self.client.access_secret_version(request={"name": version})
        return response.payload.data.decode("utf-8")
```

Remember to add `Secret Manager Secret Accessor` role to service account.

```bash
gcloud projects add-iam-policy-binding [PROJECT_ID] --member="serviceAccount:[SERVICE_ACCOUNT_EMAIL]" --role="roles/secretmanager.secretAccessor"
```

## GCP OAuth2

Google provides OAuth2 service which can be used to authenticate users.

### Set OAuth consent screen and credentials

To use OAuth2 services in GCP project, you have to set:

- OAuth consent screen - <https://console.cloud.google.com/apis/credentials/consent>
- OAuth credentials - <https://console.cloud.google.com/apis/credentials/oauthclient>
- Add `http://127.0.0.1:8000/auth` and cloud instance address to `Authorized redirect URIs`

### GCP OAuth - Python

There is `gcp_oauth` module which provides `OAuth` class which use `jose`
package to wrap all together.

```bash
pip install python-jose
```

#### Initialize module

Copy `client_id` and `sevret_id` provided by OAuth credentials
and initialize `OAuth` class.

```python
from gcp_oauth import OAuth

...

oAuth = OAuth(
    client_id="...",
    client_secret="..."
)
```

But `client_secret` is secert and shoult be stored in secret manager
(replace `angular-python-420314` with your GCP project_id):

```python
from gcp_secrets import GcpSecrets

...

secrets = GcpSecrets("angular-python-420314")
client_secret = secrets.get_secret("oauth_client_secret")
oAuth = OAuth(
    client_id="...",
    client_secret=client_secret,
)
```

#### Redirect to login Google page

First is `login` page which redirects user to Google login page.

```python
@app.get("/login")
async def login_google(request: Request):
    return oAuth.redirect_login(request)
```

#### Authorization page

When Google authorize user, then it redirects user to `auth` page
with `code` parameter. This alowes us to get `access token` and
access token allows to access Google services and get user data.

```python
@app.get("/auth")
async def auth_google(code: str):
    return await oAuth.auth(code)
```

#### Verify access token

It is also possible, that user is already authorized in another
system (e.g. Angular). In this case, all requests have `Authorization`
header with access token. To protect (almost) all requests, add
this middleware.

```python
@app.middleware("http")
async def verify_token_middleware(request: Request, call_next):
    return await oAuth.verify_token_middleware(request, call_next)
```

#### Set python script as handler

In `app.yaml` add these two paths to be
served by python script:

```yaml
- url: /login
  script: auto

- url: /auth
  script: auto
```

### GCP OAuth - Angular

Angualr authorization requires setting `Authorized JavaScript origins`
on <https://console.cloud.google.com/apis/credentials>. For development
environment you have to add **both** `http://localhost:4200` and
`http://localhost`. And use `http://localhost:4200` in browser.
See: <https://developers.google.com/identity/gsi/web/guides/get-google-api-clientid>

#### Install Angular library (angularx-social-login)

<https://www.npmjs.com/package/@abacritt/angularx-social-login>.

```bash
cd frontend
npm i @abacritt/angularx-social-login
```

#### Create AuthService

```bash
ng generate service shared/auth/auth
```

```typescript
import { SocialAuthService, SocialUser } from '@abacritt/angularx-social-login';
import { Injectable } from '@angular/core';

@Injectable({
    providedIn: 'root'
})
export class AuthService {

    user: SocialUser | null = null;
    loggedIn: boolean = false;

    constructor(private socialAuthService: SocialAuthService) {
        this.socialAuthService.authState.subscribe((user) => {
            this.user = user;
            this.loggedIn = (user != null);
        });
    }

    public signOut(): void {
        this.socialAuthService.signOut();
        this.user = null;
        this.loggedIn = false;
    }

    public getToken(): string {
        return this.user?.idToken ?? '';
    }
    
}
```

#### Create authInterceptor

```bash
ng generate interceptor shared/auth/auth-interceptor
```

```typescript
import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { AuthService } from './auth.service';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
    const authService = inject(AuthService);
    const authToken = authService.getToken();

    // Clone the request and add the authorization header
    const authReq = req.clone({
        setHeaders: {
            Authorization: `Bearer ${authToken}`
        }
    });
    return next(authReq);
};
```

#### Add GoogleLoginProvider inject authInterceptor

In code below replace `{clientId}` with real client.

```typescript
// app.config.ts
import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet } from '@angular/router';
import { ConfigService } from './config/config.service';
import { ChatComponent } from './chat/chat.component';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { AuthService } from './shared/auth/auth.service';
import { GoogleSigninButtonModule } from '@abacritt/angularx-social-login';

@Component({
    selector: 'app-root',
    standalone: true,
    imports: [CommonModule, RouterOutlet, ChatComponent, MatToolbarModule, MatIconModule, MatButtonModule, GoogleSigninButtonModule],
    templateUrl: './app.component.html',
    styleUrl: './app.component.css'
})
export class AppComponent {

    version = '';

    constructor(public authService: AuthService, private config: ConfigService) {
        this.config.getConfig().subscribe(c => {
            this.version = c.version;
        })
    }

} 
```

#### Add Google login button

Modify `app.component.ts`.

- add AuthService in constructor
- read authState in ngOnInit
- add signOut() method

```typescript
export class AppComponent implements OnInit {

    version = '';
    user: SocialUser | null = null;
    loggedIn: boolean = false;

    constructor(private authService: SocialAuthService, private config: ConfigService) {
        this.config.getConfig().subscribe(c => {
            this.version = c.version;
        })
    }

    ngOnInit() {
        this.authService.authState.subscribe((user) => {
            this.user = user;
            this.loggedIn = (user != null);
        });
    }

    signOut(): void {
        this.authService.signOut();
        this.user = null;
        this.loggedIn = false;
    }

} 
```

Modify `app.component.html`.

- add toolbar with user photo and logout button in header
- add login button in main section

```html
<header>
    <mat-toolbar color="primary">
        <h1>Hello, {{hello}} - {{ title }}</h1>
        @if(authService.user != null){
        <div class="flex-spacer"></div>
        <img src="{{ authService.user.photoUrl }}" class="profile-photo" alt="User profile" referrerpolicy="no-referrer">
        <button mat-icon-button aria-label="Logout" (click)="authService.signOut()">
            <mat-icon>logout</mat-icon>
        </button>
        }
    </mat-toolbar>
</header>
<main [class.login]="!authService.loggedIn">
    @if(authService.loggedIn){
    <p>Congratulations! Your app is running . 🎉</p>
    <a routerLink="/movies">Movies</a>
    <router-outlet></router-outlet>
    }@else{
    <asl-google-signin-button type='standard' size='large'></asl-google-signin-button>
    }
</main>
<footer>
    <span>ver. {{version}}</span>
</footer>
```

Modify `app.component.css`.

```css
:host {
    display: flex;
    flex-direction: column;
    width: 100%;
    height: 100%
}

.flex-spacer {
    flex: 1 1 auto;
}

main {
    width: 100%;
    height: calc(100% - 1.5em - var(--mat-toolbar-standard-height));
}

footer {
    flex: 0 0 auto;
    padding: 0em 0.5em 0.5em 0.5em;
    text-align: right;
    height: 1em;
}

.profile-photo {
    border-radius: 50%;
    width: calc(var(--mat-toolbar-standard-height) * 0.8);
    height: calc(var(--mat-toolbar-standard-height) * 0.8);
    border: 2px solid white;
    box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.2);
}

main.login {
    display: grid;
    place-items: center;
}
```

## Sessions

Usually when user log in the user session is starting.
During next reqest, the session is checked, not authorization
token - it is faster.

```bash
pip install fastapi-sessions
```

### Define sessionData

Define class denoting data stored in session.
At least in have to be user identifier.

```python
class SessionData(BaseModel):
    username: str
```

### Initialise SessionManager

```python
session_manager = SessionManager[SessionData]()
```

### Create session when user logs in

```python
@app.get("/auth")
async def auth_google(code: str, response: Response):
    user_data = await oAuth.auth(code)
    await session_manager.create_session(response, SessionData(username=user_data.name))
    return user_data
```

### Get session data

```python
@app.get("/api/user")
async def user_get(session_data: SessionData = Depends(session_manager)):
    return session_data.user
```

### Handle Invalid session exception

When session is invalid try to authorize user
with token and create session again.

```python
async def session_reader(request: Request, response: Response) -> SessionData:
    try:
        data = await session_manager(request)
        return data
    except InvalidSessionException:
        pass
    except HTTPException as e:
        if e.status_code != 403 or e.detail != "No session provided":
            raise e
    user_data = oAuth.verify_token(request)
    if not user_data:
        raise HTTPException(status_code=401, detail="Unauthorized")
    data = SessionData(user=user_data)
    await session_manager.create_session(response, data)
    return data


@app.get("/api/user")
async def user_get(session_data: SessionData = Depends(session_reader)):
    return session_data.user
```

## GCP Firestore

Install client library.

```bash
pip install --upgrade google-cloud-firestore
```
