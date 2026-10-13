---
name: research-container-deployment
description: Help Dartmouth researchers deploy containerized web applications (Streamlit, Flask, Shiny, APIs, etc.) through the Dartmouth Computing Dashboard (dashboard.dartmouth.edu). Use when someone asks about creating a Dashboard project, free-tier vs billed projects, creating a PostgreSQL/MySQL/MariaDB/SQL Server database instance, joining the Dartmouth GitHub organization, building a container image from a GitHub repo (Container Image Builders, service-account read access, release webhook), checking image builds and scans, filling in a Container Deploy (image, environment variables, secrets, ports, CPU/memory), finding the app URL, Kubernetes Deploy (the k8s-<name> GitHub manifests repo, environments, Argo CD sync, Rancher), or getting an HTTPS appname.dartmouth.edu address on the load balancer.
type: Agent Skill
title: Research container deployment on Dartmouth Dashboard — end-user guide
resource: https://dashboard.dartmouth.edu
tags: [dartmouth-dashboard, containers, kubernetes, docker, podman, database, streamlit, end-user, rcd]
generated: { by: claude-cowork/claude-opus-5-5, at: 2026-10-13T08:45:00-04:00 }
verified: { by: human:f003q1r, at: 2026-10-13T10:14:30-04:00 }
stale_after: 2027-01-13T00:00:00Z
status: stable
sources:
  - id: rc-workshop
    resource: https://rcweb.dartmouth.edu/~f003q1r/workshops/dashboard/
    title: Deploying a Containerized Web Application with Dartmouth Dashboard (workshop)
    author: human:f003q1r
  - id: lb-request
    resource: https://services.dartmouth.edu/TDClient/1806/Portal/Requests/Service/55228/Load-Balancing-Management/Request
    title: Load Balancing Management request (TDX)
    author: team:dartmouth-itc
  - id: gh-create-account
    resource: https://dartmouth.github.io/get-started-on-dartmouth-github/create-account/
    title: Get Started on Dartmouth GitHub — Create Account
  - id: gh-add-email
    resource: https://dartmouth.github.io/get-started-on-dartmouth-github/add-dartmouth-email/
    title: Get Started on Dartmouth GitHub — Add Dartmouth Email
  - id: dash-github
    resource: https://dashboard.dartmouth.edu/github/invitation_request/
    title: Dashboard — GitHub Invitation Request
    author: team:dartmouth-rcd
  - id: dash-templates
    resource: https://dashboard.dartmouth.edu/compute/
    title: Dashboard manifest templates (Container Deploy and Kubernetes Deploy sample), provided by RCD
    author: team:dartmouth-rcd
  - id: dash-project
    resource: https://dashboard.dartmouth.edu/project/
    title: Dashboard — Project Console and Create Project form
    author: team:dartmouth-rcd
  - id: dash-database
    resource: https://dashboard.dartmouth.edu/database/
    title: Dashboard — Database Console and Create Instance form
    author: team:dartmouth-rcd
  - id: dash-compute
    resource: https://dashboard.dartmouth.edu/compute/
    title: Dashboard — Compute Console (builders, images, Container Deploy, Kubernetes Deploy)
    author: team:dartmouth-rcd
  - id: todo-demo
    resource: https://github.com/dartmouth/todo-demo
    title: Todo demo Streamlit app (workshop sample)
---

# Deploying research containers on Dartmouth Dashboard

The Dartmouth Computing Dashboard (https://dashboard.dartmouth.edu) lets Dartmouth users create databases and run containerized applications on Dartmouth's Kubernetes clusters without managing Kubernetes directly. It is run by Infrastructure Services.

The Dashboard has three sections that matter here:

| Section | URL | Purpose |
|---|---|---|
| Project | https://dashboard.dartmouth.edu/project/projects | Every resource lives in a project. Billing is set per project. |
| Database | https://dashboard.dartmouth.edu/databases/instances | Managed PostgreSQL, MariaDB, MySQL, SQL Server. |
| Compute | https://dashboard.dartmouth.edu/compute/ | Build images from GitHub and deploy containers. |

Form labels and limits below were read from the Dashboard UI in October 2026. If a user reports something different, trust what they see and the Dashboard's own help text over this file.

## Ground rules for answering

- **Pick a project first.** Most pages (e.g. Database › Instances) only work after a project is selected in the **PROJECT** menu in the green top bar.[^dash-database]
- **Never ask for or repeat secrets.** Passwords, connection strings and API keys go into the Dashboard's **Secret** fields, not into chat, code, Dockerfiles or Git.
- **Test locally before deploying.** If the container doesn't run with `podman run` / `docker run` on the user's laptop, it won't run on the cluster.
- **Sensitive data or logins:** apps that take usernames, passwords or other sensitive input need HTTPS. Have the user request an `https://<appname>.dartmouth.edu` address on the load balancer (see §4).[^lb-request]
- **Regulated data** (HIPAA, FERPA, etc.): don't assume the Dashboard is approved. Have the user contact research.computing@dartmouth.edu first.
- **Support:** https://services.dartmouth.edu/TDClient/1806/Portal/Requests/Service/55225/Container-Hosting-and-Management/Request

## The whole path at a glance

1. Create a **Project** (or select an existing one).
2. Create a **Database Instance** if the app needs one. Save the admin password and hostname.
3. Get a **container image**: either use an existing public image or set up a **Container Image Builder** for your GitHub repo and cut a release.
4. Create a **Container Deploy** with the image, environment variables, secrets and port.
5. Open the app at its `-app.c.dartmouth.edu` URL after 5–10 minutes.[^rc-workshop] Optionally request an HTTPS `<appname>.dartmouth.edu` address.

A complete worked example using the sample Todo Streamlit app is in [references/todo-walkthrough.md](references/todo-walkthrough.md). Load it when the user is following the workshop or wants a concrete end-to-end example.

## 1. Projects

Project › Projects › **CREATE PROJECT**.[^dash-project] You become the owner automatically.

| Field | Rules |
|---|---|
| Project Label | Display name. 1–40 chars: letters, numbers, dashes, spaces. |
| Project Name | ID. 1–20 chars: lowercase letters, numbers, dashes; can't start/end with a dash. **Can't be changed later.** |
| Members | Other users who get access to the project's resources. |
| Free-tier / Enable Billing | Free-tier needs no billing info. Enable Billing asks for a chart string. |

- **One free-tier project per user.** Free-tier projects can only create free-tier resources.
- **Billing is one-way.** Adding billing (Edit project) lifts the free-tier limits, and the project can never go back to free-tier.[^dash-project]
- **Sharing:** members have the same access to resources as the owner, but only the owner can rename the project or add/remove members.
- **Compute and free tier:** the Compute console currently says there is no free tier for compute resources.[^dash-compute] If a free-tier user can't deploy, the fix is a billed project (chart string), or ask RCD.

## 2. Databases

Database › Instances › **Create Instance** (select a project first).[^dash-database]

| Field | Rules / advice |
|---|---|
| Instance Type | PostgreSQL 14, MariaDB 10.7, MySQL 8.0, SQL Server 2019 |
| Instance Name | 1–40 chars: lowercase letters, numbers, dashes. Can't start with a number or start/end with a dash. |
| Instance Version | Pick from the list. |
| Location | Cluster to deploy to; pick from the dropdown (the workshop used `rcikube6`). |
| Admin Password | 8–32 chars: letters, numbers, `-_$!^#()*`. Click **GENERATE**, then the eye icon, and **save it now. It can't be retrieved later.** |
| Storage | 1–100 GB. |
| Automatically backup | Optional, extra cost per backup. Not on free tier. |

**Limits:**

- Billed projects: up to **10 instances** with **100 GB** each by default. Email research.computing@dartmouth.edu to raise limits.
- Free-tier projects: **one instance**, up to **10 GB**, **no backups**.[^dash-database]

**Connecting:** open Database › Instances, select the instance, click **Connect**, and note the **Hostname**. A PostgreSQL connection string looks like:

```
postgresql://admin:<admin_password>@<hostname>:5432/postgres
```

MySQL/MariaDB users can also use phpMyAdmin at https://pma.dartmouth.edu.

## 3. Building a container image

Skip this if the user is deploying an existing public image (e.g. `ghcr.io/dartmouth/todo-demo:latest`).

**Prerequisites:**[^dash-compute]

- **Membership in the Dartmouth GitHub organization** (https://github.com/dartmouth). See *Joining Dartmouth GitHub* below.
- Source code **and a `Dockerfile`** in a GitHub repository in one of the Dartmouth GitHub organizations.
- The image builds and runs locally:

  ```bash
  podman build --tag myapp .          # or: docker build -t myapp .
  podman run -p 8501:8501 -e SOME_VAR=value myapp
  ```

**Joining Dartmouth GitHub** (one time per person):

1. **Get a GitHub account set up for Dartmouth.**
   - No GitHub account yet: create one, ideally with your `name@dartmouth.edu` address: https://dartmouth.github.io/get-started-on-dartmouth-github/create-account/[^gh-create-account]
   - Already have one (personal is fine; GitHub recommends one account per person): add **both** `name@dartmouth.edu` and `netid@dartmouth.edu` under GitHub Settings › Emails and verify each: https://dartmouth.github.io/get-started-on-dartmouth-github/add-dartmouth-email/[^gh-add-email] The NetID address is what makes Dartmouth SSO work.
2. **Request an invitation:** in the Dashboard, open GitHub › Invitation Request (https://dashboard.dartmouth.edu/github/invitation_request/) and click **REQUEST INVITATION**.[^dash-github]
3. Within a few minutes an email arrives at your Dartmouth account. Follow it to accept the invitation.

Other Dartmouth GitHub organizations are invite-only; ask that org's owner to add you.[^gh-add-email]

**One-time GitHub setup per repository** (also shown under Compute › Container Image Builders › **SETUP GITHUB**):[^dash-compute]

*Read access for the build service account:*

1. In the GitHub repo: Settings › Collaborators and teams › **Add people**.
2. Search for `f0068fg`, select it, choose **Read** if asked, click **Add**.

*Webhook to trigger builds on release:*

1. Settings › Webhooks › **Add webhook**.
2. Payload URL: `https://github-webhook-proxy.dartmouth.edu`
3. Content type: `application/json`
4. Trigger: **Let me select individual events**, and check **only Releases**.
5. Click **Add webhook**.

**Create the builder:** Compute › Container Image Builders › **CREATE**. Give it a name and the repo (`git@github.com:<org>/<repo>.git`). If the Dockerfile isn't at the repo root, set **Dockerfile Path** (e.g. `backend/Dockerfile`) and **Context Path** (e.g. `backend`). That's how one repo can feed several builders. Add an email address to get notified when a build fails.

**Trigger a build:** on GitHub, Releases › **Draft a new release**, create a tag (e.g. `v0.1.0`), and publish. Each release starts a build.[^rc-workshop]

**Check the result:** Compute › **Container Images** lists every build with Status (Success/Failed), a **Build** log, a **Scan** (security vulnerability) report, and the image **Location**. Copy the Location of a successful build; that's what goes in Container Deploy.

**Build failed?** Open the Build log. Common causes:

- The repo isn't in a Dartmouth GitHub organization, or you aren't a member yet.
- The service account wasn't added, or was added to a different repo.
- The Dockerfile/Context Path doesn't match the repo layout.
- The Dockerfile only works locally (e.g. it copies files that are in `.gitignore`, or depends on a local base image).
- The webhook isn't set to **Releases** only, or a release was saved as a draft and not published.

## 4. Container Deploy

Compute › Container Deploy › **Create**.[^dash-compute]

| Field | What to enter |
|---|---|
| Deployment Name | 3–40 chars: lowercase letters, numbers, dashes; can't start with a number or dash. Also used in the app URL. |
| Container Image | Image name/tag: the **Location** from Container Images, or a public image such as `ghcr.io/<org>/<image>:<tag>`. |
| ADD ENVIRONMENT VARIABLE | Non-sensitive settings (names, feature flags). |
| ADD SECRET | Anything sensitive: `DATABASE_URL`, passwords, API keys. The Dashboard encrypts these and injects them as env vars; nothing else to do. |
| Ports | Comma-separated TCP ports the app listens on, e.g. `8501` for Streamlit, `8000`, `8080`. Use ports ≥ 1024 (see below). |
| CPU Limit | Fraction of a CPU, default `0.25`. Billed projects only. |
| Memory Limit (GB) | Default `1`. Billed projects only. |

CPU and memory are both the guaranteed amount and the hard cap. An app that exceeds its memory limit is killed and restarted.

**App code must:**

- Read config from environment variables (e.g. `os.environ["DATABASE_URL"]`), not hard-coded values or a `.env` file baked into the image.
- Listen on `0.0.0.0`, not `localhost`/`127.0.0.1`, on the port entered above.
- **Run as a non-root user.** Containers run as UID/GID `101`, with all Linux capabilities dropped and no privilege escalation.[^dash-templates] So:
  - Listen on a port **≥ 1024** (e.g. `8080`, not `80`). Stock `nginx`/`httpd` images on port 80 fail; use an unprivileged variant such as `nginxinc/nginx-unprivileged`.
  - Don't rely on `sudo`, `apt-get` or writing to root-owned paths at runtime. Install everything at build time.
  - Any directory the app writes to must be writable by UID 101 (e.g. `/tmp`, or `chown 101:101` it in the Dockerfile). Test locally with `podman run --user 101:101 ...`.
- **Not keep data on the container's disk.** Container Deploy has no persistent volume, so files written inside the container are lost on every restart or update. Use a Dashboard database (or Kubernetes Deploy with a volume).
- **Expect limited outbound network access.** Each project is its own Kubernetes namespace. The app can reach the public internet, DNS, and anything else in its project, including **that project's Dashboard databases**. Outbound connections to other Dartmouth internal networks are blocked by default, and that includes databases in a *different* project.[^dash-templates] If the app needs a campus service, ask research.computing@dartmouth.edu.

**After clicking Create:** the app is usually up in **5–10 minutes** at:[^rc-workshop]

```
http://<deployment-name>-app.c.dartmouth.edu:<port>
```

Every deployment always gets this plain-HTTP address.

**HTTPS and a friendly name (optional):** to also serve the app at `https://<appname>.dartmouth.edu` through the load balancer, submit a Load Balancing Management request:[^lb-request]
https://services.dartmouth.edu/TDClient/1806/Portal/Requests/Service/55228/Load-Balancing-Management/Request

Include the app name you want, the deployment's `-app.c.dartmouth.edu` address and port. Do this for any app that handles logins or sensitive input. The `-app.c.dartmouth.edu:<port>` address keeps working alongside it.

**Updating the app:** cut a new GitHub release, wait for a successful build in Container Images, then update the deployment's Container Image to the new Location.

**Change Container Deploys only through the Dashboard.** The Dashboard generates and owns the Kubernetes manifests behind a Container Deploy. Don't edit them by hand. If you need something the form can't do (extra volumes, custom probes, sidecars), use Kubernetes Deploy instead.

**App not loading?**

- Wait the full 10 minutes.
- The port in the URL must match the Ports field and the port the app listens on.
- The app must bind to `0.0.0.0`.
- `Permission denied` errors or a crash on start: usually a port below 1024 or a write to a root-owned path (the container runs as UID 101).
- Timeouts calling another Dartmouth service, or a database in another project: outbound traffic outside the project to internal networks is blocked by default. Create the database in the same project as the deployment.
- Missing or misspelled env var/secret names. They are case-sensitive.
- Database connection: wrong hostname or password, or the database is still provisioning.
- **Logs:** Container Deploy apps **don't have Rancher access**. Reproduce the problem locally with `podman run` (same image, env vars, `--user 101:101`). If it only fails on the cluster, email research.computing@dartmouth.edu with the deployment name. Teams that need regular access to logs should use Kubernetes Deploy.

## 5. Kubernetes Deploy (advanced)

For users who want to manage Kubernetes manifests themselves.[^dash-compute]

**What you get:** creating a Kubernetes Deploy creates a **GitHub repository of Kubernetes manifests** in the Dartmouth GitHub organization, named `k8s-<deployment-name>`, with **one folder per environment**. The Dashboard links to the repo. **The repo is the deployment.** Edit the manifests, then commit and push. Argo CD syncs the repo to the cluster about **every 5 minutes**, so you never run `kubectl apply` yourself.

**Creating it:** Compute › Kubernetes Deploy › Create.

- **Deployment Name:** 3–40 chars, lowercase, numbers, dashes. **Don't include the environment** (no `-prod`, `-dev`).
- **Environments** (`+`): each has a **Location** (cluster), an **Environment Name** (stage, e.g. prod/preprod/dev) and a **Path** (that environment's folder in the repo). Each Location/Environment combination is an independent deployment.

**Working with it:**

- **You own these manifests.** Each environment folder starts with a sample (an nginx `Deployment`, a `Service`, a `PersistentVolumeClaim` and a commented-out `SealedSecret`) that you replace with your app.
- **Secrets must be `SealedSecret`s**, never plain `Secret`s, because the manifests live in Git. Unlike Container Deploy, you seal them yourself with `kubeseal` and the `kubeseal.pem` certificate from Infrastructure Services.
- How to adapt the sample (image, ports, probes, storage, sealing secrets, mirroring Container Deploy's security settings): [references/kubernetes-manifests.md](references/kubernetes-manifests.md). Load it whenever a user is editing manifests.
- **Public address:** add the annotation `external-dns.alpha.kubernetes.io/hostname: <name>.c.dartmouth.edu` to your Service to get `http://<name>.c.dartmouth.edu:<port>`. This is the same mechanism Container Deploy uses. For HTTPS, use the load-balancer request in §4.
- **Sync status, pod state and logs:** use Rancher (https://rci-rancher.dartmouth.edu). It's the only place to see whether Argo CD has applied your last commit. Allow up to 5 minutes after pushing before expecting a change.
- **Updating the app:** change the image tag in the manifests and push. Unlike Container Deploy, there's no form field to update.

Point beginners to Container Deploy first. Kubernetes Deploy is for people comfortable with manifests.

## Learning resources

The Compute console's **Other Resources** panel links to beginner Docker and Kubernetes guides and videos.[^dash-compute] Official docs:

- Docker: https://docs.docker.com/get-started/
- Kubernetes: https://kubernetes.io/docs/home/
- Streamlit: https://docs.streamlit.io/
- Workshop page with the full walkthrough: https://rcweb.dartmouth.edu/~f003q1r/workshops/dashboard/

[^rc-workshop]: Deploying a Containerized Web Application with Dartmouth Dashboard (workshop)
[^lb-request]: Load Balancing Management request (TDX)
[^gh-create-account]: Get Started on Dartmouth GitHub — Create Account
[^gh-add-email]: Get Started on Dartmouth GitHub — Add Dartmouth Email
[^dash-github]: Dashboard — GitHub Invitation Request
[^dash-templates]: Dashboard manifest templates (Container Deploy and Kubernetes Deploy sample), provided by RCD
[^dash-project]: Dashboard — Project Console and Create Project form
[^dash-database]: Dashboard — Database Console and Create Instance form
[^dash-compute]: Dashboard — Compute Console (builders, images, Container Deploy, Kubernetes Deploy)
