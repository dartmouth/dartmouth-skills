---
type: Reference
title: Worked example — deploying the Todo Streamlit app with a PostgreSQL database
description: End-to-end workshop walkthrough for the research-container-deployment skill, using the dartmouth/todo-demo Streamlit app.
tags: [dartmouth-dashboard, streamlit, postgresql, podman, workshop]
generated: { by: claude-cowork/claude-opus-5-5, at: 2026-10-13T08:45:00-04:00 }
verified: { by: human:f003q1r, at: 2026-10-13T08:51:49-04:00 }
stale_after: 2027-01-13T00:00:00Z
status: stable
sources:
  - id: rc-workshop
    resource: https://rcweb.dartmouth.edu/~f003q1r/workshops/dashboard/
    title: Deploying a Containerized Web Application with Dartmouth Dashboard (workshop)
    author: human:f003q1r
  - id: todo-demo
    resource: https://github.com/dartmouth/todo-demo
    title: Todo demo Streamlit app
---

# Todo app walkthrough

This follows the RCD workshop.[^rc-workshop] It deploys a prebuilt image, so step 4 (building your own image) is optional.

## 1. Project

Go to https://dashboard.dartmouth.edu/project/projects › **CREATE PROJECT**. Give it a Label (e.g. `todo`) and a Name (e.g. `todo`), then pick Free-tier or Enable Billing. Select the project in the **PROJECT** menu at the top.

## 2. Database

Go to https://dashboard.dartmouth.edu/databases/instances › **Create Instance** and fill in:

- Instance Type: **PostgreSQL**
- Instance Name: `todo`
- Location: pick the cluster from the dropdown (the workshop used `rcikube6`)
- Admin Password: click **GENERATE**, then the eye icon. **Copy it now. You won't see it again.**
- Storage: `1` GB

Click **Create**. When it's ready, select the instance › **Connect** and note the **Hostname**.

## 3. Run the app locally (optional but recommended)

Get the code from https://github.com/dartmouth/todo-demo (Code › Download ZIP) or:

```bash
git clone git@github.com:dartmouth/todo-demo.git
cd todo-demo
```

With Python installed:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run main.py
```

Without Python, install uv (https://docs.astral.sh/uv/getting-started/installation/), then:

```bash
uv run --with streamlit,python-dotenv,peewee,watchdog streamlit run main.py
```

The app opens at http://localhost:8501 and reloads when you edit the code.

As a container:

```bash
podman build --tag todo .
podman run -p 8501:8501 -e USER_NAME="Your Name" --name todo todo
```

## 4. Build your own image (skip for the workshop)

Join the Dartmouth GitHub organization if you haven't (Dashboard › GitHub › Invitation Request; see SKILL.md §3). Push the code and Dockerfile to a repo in a Dartmouth GitHub org. Add the `f0068fg` read collaborator and the release webhook (see SKILL.md §3). Create a Container Image Builder, publish a GitHub release, then copy the image **Location** from Compute › Container Images.

## 5. Container Deploy

Go to https://dashboard.dartmouth.edu/compute/container_deploy/ › **Create** and fill in:

| Field | Value |
|---|---|
| Deployment Name | e.g. `todo-yourname` |
| Container Image | `ghcr.io/dartmouth/todo-demo:latest` (or your own Location) |
| Environment Variable | `USER_NAME` = your name |
| Secret | `DATABASE_URL` = `postgresql://admin:<admin_password>@<hostname>:5432/postgres` |
| Secret | `TODOS_PASSWORD` = a new password the app uses for the todos database it creates |
| Ports | `8501` |

On a billed project you can also adjust CPU Limit and Memory Limit.

Click **Create**. After 5–10 minutes, open:

```
http://todo-yourname-app.c.dartmouth.edu:8501
```

## Checklist

- [ ] Project created and selected
- [ ] Database created; admin password and hostname saved
- [ ] Container image chosen (existing, or built from a release)
- [ ] Container Deploy created with env vars, secrets and port
- [ ] App reachable at `http://<deployment-name>-app.c.dartmouth.edu:<port>`
- [ ] Requested an `https://<appname>.dartmouth.edu` load-balancer address if the app handles logins or sensitive input: https://services.dartmouth.edu/TDClient/1806/Portal/Requests/Service/55228/Load-Balancing-Management/Request

[^rc-workshop]: Deploying a Containerized Web Application with Dartmouth Dashboard (workshop)
