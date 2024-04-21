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
cd frontend
ng serve
```

And in the second terminal

```bash
cd backend
uvicorn main:app --reload
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

Then beploy Python project into GCP:

```bash
gcloud app deploy backend/app.yaml
```

## GCP secrets

When you have to deliver some secret data to the program, you should use
`Secret Manger`. It is designed to store configuration data as passwords, API keys and
certificates. Each secret is identified by `project_id`, `secret_id` and `version_id`.

<https://cloud.google.com/secret-manager/docs/create-secret-quickstart#secretmanager-quickstart-python>

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
There is `gcp_oauth` module which provides `OAuth` class which use `jose`
package to wrap all together.

```bash
pip install python-jose
```

### Set OAuth consent screen and credentials

To use OAuth2 services in GCP project, you have to set:

- OAuth consent screen - <https://console.cloud.google.com/apis/credentials/consent>
- OAuth credentials - <https://console.cloud.google.com/apis/credentials/oauthclient>
- Add `http://127.0.0.1:8000/auth` and cloud instance address to `Authorized redirect URIs`

### Initialize module

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
    client_id="48284060390-kope189hgqlq39u2m96jjqcaetib4tq8.apps.googleusercontent.com",
    client_secret=client_secret,
)
```

### Redirect to login Google page

First is `login` page which redirects user to Google login page.

```python
@app.get("/login")
async def login_google(request: Request):
    return oAuth.redirect_login(request)
```

### Authorization page

When Google authorize user, then it redirects user to `auth` page
with `code` parameter. This alowes us to get `access token` and
access token allows to access Google services and get user data.

```python
@app.get("/auth")
async def auth_google(code: str):
    return await oAuth.auth(code)
```

### Verify access token

It is also possible, that user is already authorized in another
system (e.g. Angular). In this case, all requests have `Authorization`
header with access token. To protect (almost) all requests, add
this middleware.

```python
@app.middleware("http")
async def verify_token_middleware(request: Request, call_next):
    return await oAuth.verify_token_middleware(request, call_next)
```

### Set python script as handler 

In `app.yaml` add these two paths to be
served by python script:

```yaml
- url: /login
  script: auto

- url: /auth
  script: auto
```