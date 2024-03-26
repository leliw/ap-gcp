# Python + Angular on Google Cloud Platform (App Engine)

It's a simple full stack project with Angular frontend and Python backend
deployable in Goggle Cloud Platform (App Engine).

## Copy ap-basic project into new ap-gcp prject

```bash
git clone https://github.com/leliw/ap-basic.git ap-gcp
cd proxy-one-http
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
```

## GCP app.yaml

GCP requires `app.yaml` file **in root** directory.
It provides similar information as `Dockerfile` and `nginx.conf`.

- runtime - some kind of base image
- entrypoint - how to run service
- handlers - requests routing

```yaml
runtime: python311
entrypoint: gunicorn -b :$PORT -k uvicorn.workers.UvicornWorker backend.main:app

handlers:

- url: /api/.*
  script: auto

- url: /
  static_files: frontend/dist/frontend/browser/index.html
  upload: frontend/dist/frontend/browser/index.html

- url: /(.+)
  static_files: frontend/dist/frontend/browser/\1
  upload: frontend/dist/frontend/browser/(.+)
```

## GCP .gcloudignore

The second important file is `.gcloudignore`.
It is like `.dockerignore` or `.gitignore`,
specify which files shouldn't be send  to GCP.

```text
.gcloudignore
.git
.gitignore

__pycache__/
/setup.cfg

**/.venv
**/__pycache__/

# Ignore the Angular project except the dist folder
frontend/**
!frontend/
!frontend/dist/**
```

Last 3 lines prevents from sending Angular soure code but
allowes to send distribution files.

## GCP requirements.txt

The `requirements.txt` file also has to be stored in
**root** directory.

```bash
mv backend/requirements.txt ./requirements.txt
```

and update `requirements-dev.txt`.

```text
-r ../requirements.txt

# Linters
ruff
```

## Angular static files

GCP can serve static files independently from python service.
It is faster especially when python service is restarting.

By default, Angular files are compiled into directory
`frontend/dist/frontend/browser/` but I have changed it
to `backend/static` in `frontend\angular.json` file.
So I have changed `app.yaml` file to reflect that change.

```yaml
```yaml
runtime: python311
entrypoint: gunicorn -b :$PORT -k uvicorn.workers.UvicornWorker backend.main:app

handlers:

- url: /api/.*
  script: auto

- url: /
  static_files: backend/static/browser/index.html
  upload: backend/static/browser/index.html

- url: /(.+)
  static_files: backend/static/browser/\1
  upload: backend/static/browser/(.+)
```

## Python current path

Unfortunately current path in python application is
root directory (not `backend`). It is significant drawback.
You have to make a workaround.

- add current project path to sys path
- all disk operations has to use current project path

```python
...
project_path = '/'.join(__file__.split('/')[:-1])
if project_path not in sys.path:
    sys.path.append(project_path)

from movies import Movie
from static_files import static_file_response

app = FastAPI()
config = parse_config(f"{project_path}/config.yaml")
...
```

## Deployment

Build Angular project.

```bash
cd frontend
ng build
cd ..
```

Create GCP project as described in
<https://cloud.google.com/appengine/docs/standard/python3/building-app/creating-gcp-project>.

Deploy into GCP:

```bash
gcloud app deploy
```
