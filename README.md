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
```

## Angular static files

GCP can serve static files independently from python service.
It is faster especially when python service is restarting.

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
