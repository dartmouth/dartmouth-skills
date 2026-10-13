---
type: Reference
title: Kubernetes manifests behind Dartmouth Dashboard deployments
description: What Container Deploy generates (Dashboard-managed), the Kubernetes Deploy sample manifest (user-edited), how to adapt it, and how to seal secrets with kubeseal.
tags: [dartmouth-dashboard, kubernetes, manifests, sealed-secrets, kubeseal, gitops]
generated: { by: claude-cowork/claude-opus-5-5, at: 2026-10-13T09:20:00-04:00 }
verified: { by: human:f003q1r, at: 2026-10-13T10:14:30-04:00 }
stale_after: 2027-01-13T00:00:00Z
status: stable
sources:
  - id: dash-templates
    resource: https://dashboard.dartmouth.edu/compute/
    title: Dashboard manifest templates (container_deploy-manifest and kubernetes_deploy sample), provided by RCD
    author: team:dartmouth-rcd
  - id: sealed-secrets
    resource: https://github.com/bitnami-labs/sealed-secrets
    title: Bitnami Sealed Secrets
---

# Kubernetes manifests behind Dashboard deployments

| Deployment type | Manifests come from | Who changes them | Secrets |
|---|---|---|---|
| **Container Deploy** | A Dashboard template filled in from the form | **The Dashboard only.** Change the form, not the manifests. | Handled for you. Values entered under ADD SECRET are encrypted and sealed automatically. |
| **Kubernetes Deploy** | A sample manifest in each environment folder of the `k8s-<deployment-name>` repo in the Dartmouth GitHub org | **The user.** Edit, commit and push; Argo CD syncs about every 5 minutes. | You seal them yourself with `kubeseal` (see below). |

If a Container Deploy user needs something the form can't express (volumes, health probes, extra containers, custom network rules), the answer is to move to Kubernetes Deploy, not to edit the Container Deploy manifests.

## What Container Deploy generates

For reference when explaining behaviour or copying good defaults into a Kubernetes Deploy.[^dash-templates] The Deployment Name plus an `-app` suffix becomes the resource name (`<name>` below).

| Resource | Details |
|---|---|
| `SealedSecret` `<name>` | Only if secrets were entered. One key per secret, injected as env vars via `secretKeyRef`. |
| `Service` `<name>` | Only if ports were entered. `ClusterIP`, one TCP port per entry (`port` = `targetPort`). Annotated `external-dns.alpha.kubernetes.io/hostname: <name>.c.dartmouth.edu`, which is what creates the `<deployment>-app.c.dartmouth.edu` address. |
| `Deployment` `<name>` | 1 replica; rolling update with `maxSurge: 1`, `maxUnavailable: 0` (new pod must start before the old one stops); `imagePullSecrets: regcred`. |
| Resources | CPU and memory **requests = limits** = the form values (e.g. 0.25 CPU → `250m`, 1 GB → `1000Mi`). |
| Container `securityContext` | `runAsUser: 101`, `runAsGroup: 101`, `runAsNonRoot: true`, `allowPrivilegeEscalation: false`, all capabilities dropped. |
| `NetworkPolicy` `<name>` | Egress only. Allows everything in the same namespace (the namespace is the project, so this covers the project's Dashboard databases), cluster DNS, and the public internet. Blocks Dartmouth internal address ranges. Inbound traffic isn't restricted by this policy. |

**What that means for users:**

- **Non-root.** The image must run as UID 101: ports ≥ 1024, no runtime package installs, and writable paths owned by 101.
- **No persistent storage.** There's no volume, so anything written to the container's disk is lost on restart. Use a database.
- **No health probes.** Kubernetes only knows whether the process is running, not whether the app responds.
- **Limited outbound traffic.** The project's own databases work. Calls to other internal Dartmouth services, including databases in other projects, time out unless RCD opens them.

## The Kubernetes Deploy sample

`{{ component['name'] }}` is replaced with the deployment name, and every resource is named `<name>-sample`.[^dash-templates]

| Resource | Sample values |
|---|---|
| `SealedSecret` (commented out) | `DB_PASSWORD` |
| `PersistentVolumeClaim` | `ReadWriteMany`, `1G` |
| `Service` | `ClusterIP`, port `80` |
| `Deployment` | 1 replica, rolling update, `regcred`, image `nginx:stable-alpine`, `exec` readiness/liveness probes, env vars `DB_HOST`/`DB_USERNAME`, volume at `/data/` |

The sample is a placeholder. Unlike Container Deploy, it has no `securityContext`, `resources`, `NetworkPolicy` or DNS annotation. Add them yourself (step 7). If you copy Container Deploy's `NetworkPolicy`, the project's databases stay reachable because they're in the same namespace.

## Adapting the sample

1. **Rename.** Drop the `-sample` suffix. `metadata.labels.app`, `spec.selector.matchLabels.app`, `template.metadata.labels.app` and the Service `selector.app` **must all match**, or the Service won't find the pods.
2. **Image.** Set `containers[].image` to your image Location from Compute › Container Images. Keep `imagePullSecrets: - name: regcred`.
3. **Ports.** Set `containerPort` to your app's port (e.g. `8501`) and match it in the Service (`port` and `targetPort`).
4. **Probes.** Replace the sample probes. They grep for `Welcome to sample`, which a real app won't return, and the liveness probe calls `bash`, which Alpine images lack. Use `httpGet` instead:

   ```yaml
   readinessProbe:
     httpGet: { path: /, port: 8501 }   # Streamlit also serves /_stcore/health
     initialDelaySeconds: 5
     periodSeconds: 30
   livenessProbe:
     httpGet: { path: /, port: 8501 }
     initialDelaySeconds: 30
     periodSeconds: 60
   ```

5. **Env vars.** Non-sensitive values go in `env` with `value:`. Sensitive values come from a SealedSecret (next section).
6. **Storage.** Keep the PVC only if files must survive restarts; set its size and `mountPath`. If the container runs as non-root, uncomment/add `securityContext.fsGroup` at the pod level so it can write to the volume. Otherwise delete the PVC, `volumeMounts` and `volumes`.
7. **Match Container Deploy's defaults** (recommended):

   ```yaml
   # container level
   resources:
     requests: { cpu: 250m, memory: 1000Mi }
     limits:   { cpu: 250m, memory: 1000Mi }
   securityContext:
     allowPrivilegeEscalation: false
     runAsUser: 101
     runAsGroup: 101
     runAsNonRoot: true
     capabilities: { drop: ["ALL"] }
   ```

   To get the public `http://<name>.c.dartmouth.edu:<port>` address (the same mechanism Container Deploy uses), add this to the Service metadata:

   ```yaml
   annotations:
     external-dns.alpha.kubernetes.io/hostname: <name>.c.dartmouth.edu
   ```

8. **Commit and push** to the environment's folder. Argo CD applies it within about 5 minutes. Watch the sync, rollout and logs in Rancher (https://rci-rancher.dartmouth.edu). Rancher is available for Kubernetes Deploy only, not Container Deploy.

## Sealing secrets for Kubernetes Deploy

**Use `SealedSecret`, never a plain `Secret`.**[^dash-templates] The manifests live in Git. A plain `Secret` is only base64-encoded, so anyone with repo access could read it. A SealedSecret can only be decrypted by the cluster.[^sealed-secrets]

1. **Get the cluster's public certificate** (`kubeseal.pem`) from Infrastructure Services. Make sure it's for the cluster (Location) you deploy to.
2. **Install the tools** (macOS):

   ```bash
   brew install kubectl kubeseal
   ```

3. **Create the secret locally.** `--dry-run=client` means nothing is sent to a cluster. The name must match what your Deployment's `secretKeyRef.name` uses.

   ```bash
   kubectl create secret generic <name> \
     --from-literal=DB_PASSWORD='<value>' \
     --from-literal=DATABASE_URL='<value>' \
     --dry-run=client -o yaml > secret.yml
   ```

4. **Seal it:**

   ```bash
   kubeseal --scope cluster-wide --format=yaml --cert=kubeseal.pem < secret.yml > sealed-secret.yml
   ```

5. **Clean up.** Commit `sealed-secret.yml` (or paste it in place of the sample's commented block). **Delete `secret.yml` and never commit it**; add it to `.gitignore`.
6. **Reference it** from the Deployment:

   ```yaml
   env:
   - name: DB_PASSWORD
     valueFrom:
       secretKeyRef:
         name: <name>          # the secret's name from step 3
         key: DB_PASSWORD
   ```

To change a value, repeat steps 3–5 and commit the new sealed file. You can't edit encrypted values by hand. `--scope cluster-wide` lets the sealed secret be decrypted under any name or namespace on that cluster.[^sealed-secrets]

## Reaching the app

The Service is `ClusterIP`. External access comes from the `external-dns` hostname annotation (`<name>.c.dartmouth.edu`, plain HTTP on your port). For `https://<appname>.dartmouth.edu`, submit a Load Balancing Management request (see SKILL.md §4).

[^dash-templates]: Dashboard manifest templates (container_deploy-manifest and kubernetes_deploy sample), provided by RCD
[^sealed-secrets]: Bitnami Sealed Secrets
