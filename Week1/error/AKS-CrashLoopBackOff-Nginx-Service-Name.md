# Kubernetes Troubleshooting: CrashLoopBackOff Due to Nginx Service Name Mismatch

## 1. What Happened?

I got the `CrashLoopBackOff` error again while deploying the ClaimIQ frontend.

This time, the issue was caused by a difference between the backend service name used in the Nginx configuration and the backend Service name created in AKS.

## 2. Check the Pod Status

First, I checked the Pods in the `claimiq` namespace:

```bash
kubectl get pods -n claimiq
```

### Output

```text
NAME                                READY   STATUS    RESTARTS       AGE
claimiq-backend-864447c689-qnmrc    1/1     Running   0              37m
claimiq-frontend-5ffb567c5c-kqxcg   0/1     Error     4 (107s ago)   2m22s
postgres-6c5564fb66-66574           1/1     Running   0              37m
```

From the output, we can see that:

- The backend Pod is running.
- The PostgreSQL Pod is running.
- The frontend Pod is failing and restarting.

## 3. Describe the Frontend Pod

To get more details about the frontend Pod, I ran:

```bash
kubectl describe pod claimiq-frontend-5ffb567c5c-kqxcg -n claimiq
```

### Pod Information

```text
Name:             claimiq-frontend-5ffb567c5c-kqxcg
Namespace:        claimiq
Priority:         0
Service Account:  default
Node:             aks-agentpool-28524209-vmss000000/10.224.0.4
Start Time:       Tue, 13 Oct 2026 01:21:18 +0000
Labels:           app=claimiq-frontend
                  pod-template-hash=5ffb567c5c
                  topology.kubernetes.io/region=eastus
                  topology.kubernetes.io/zone=0
Annotations:      <none>
Status:           Running
IP:               10.244.1.210
IPs:
  IP:             10.244.1.210
Controlled By:    ReplicaSet/claimiq-frontend-5ffb567c5c
Containers:
  frontend:
    Container ID:   containerd://d1557e153ec7340c575970c7d99a2e6a7d771714b20f33043b33a8a15e56f0c5
    Image:          claimqregistry.azurecr.io/claimiq-frontend:latest
    Image ID:       claimqregistry.azurecr.io/claimiq-frontend@sha256:34835ae55920e73a4f2a30715f8247fe957c192406740bd48a36e844c04e7bfc
    Port:           80/TCP
    Host Port:      0/TCP
    State:          Terminated
      Reason:       Error
      Exit Code:    1
      Started:      Tue, 13 Oct 2026 01:24:04 +0000
      Finished:     Tue, 13 Oct 2026 01:24:05 +0000
    Last State:     Terminated
      Reason:       Error
      Exit Code:    1
      Started:      Tue, 13 Oct 2026 01:22:34 +0000
      Finished:     Tue, 13 Oct 2026 01:22:34 +0000
    Ready:          False
    Restart Count:  5
    Limits:
      cpu:          250m
      memory:       128Mi
    Requests:
      cpu:          50m
      memory:       64Mi
    Environment:    <none>
    Mounts:
      /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-lpjrq (ro)

Conditions:
  Type                        Status
  PodReadyToStartContainers   True
  Initialized                 True
  Ready                       False
  ContainersReady             False
  PodScheduled                True

Volumes:
  kube-api-access-lpjrq:
    Type:                     Projected (a volume that contains injected data from multiple sources)
    TokenExpirationSeconds:   3607
    ConfigMapName:            kube-root-ca.crt
    Optional:                 false
    DownwardAPI:              true

QoS Class:                    Burstable
Node-Selectors:               <none>
Tolerations:                  node.kubernetes.io/memory-pressure:NoSchedule
                              node.kubernetes.io/not-ready:NoExecute for 300s
                              node.kubernetes.io/unreachable:NoExecute for 300s

Events:
  Type     Reason     Age                 From               Message
  ----     ------     ----                ----               -------
  Normal   Scheduled  2m50s               default-scheduler  Successfully assigned claimiq/claimiq-frontend-5ffb567c5c-kqxcg to aks-agentpool-28524209-vmss000000
  Normal   Pulled     2m49s               kubelet            Successfully pulled image "claimqregistry.azurecr.io/claimiq-frontend:latest" in 1.007s (1.007s including waiting). Image size: 26326922 bytes.
  Normal   Pulled     2m48s               kubelet            Successfully pulled image "claimqregistry.azurecr.io/claimiq-frontend:latest" in 88ms (89ms including waiting). Image size: 26326922 bytes.
  Normal   Pulled     2m37s               kubelet            Successfully pulled image "claimqregistry.azurecr.io/claimiq-frontend:latest" in 67ms (67ms including waiting). Image size: 26326922 bytes.
  Normal   Pulled     2m16s               kubelet            Successfully pulled image "claimqregistry.azurecr.io/claimiq-frontend:latest" in 78ms (78ms including waiting). Image size: 26326922 bytes.
  Normal   Pulled     95s                 kubelet            Successfully pulled image "claimqregistry.azurecr.io/claimiq-frontend:latest" in 95ms (95ms including waiting). Image size: 26326922 bytes.
  Normal   Pulling    5s (x6 over 2m50s)   kubelet            spec.containers{frontend}: Pulling image "claimqregistry.azurecr.io/claimiq-frontend:latest"
  Normal   Created    5s (x6 over 2m49s)   kubelet            spec.containers{frontend}: Container created
  Normal   Started    5s (x6 over 2m49s)   kubelet            spec.containers{frontend}: Container started
  Normal   Pulled     5s                  kubelet            Successfully pulled image "claimqregistry.azurecr.io/claimiq-frontend:latest" in 159ms (159ms including waiting). Image size: 26326922 bytes.
  Warning  BackOff    4s (x6 over 2m47s)   kubelet            Back-off restarting failed container frontend in pod claimiq-frontend-5ffb567c5c-kqxcg_claimiq(874e535c-6825-4e97-9269-17730db413b7)
```

## 4. Check the Frontend Container Logs

Next, I checked the frontend container logs:

```bash
kubectl logs claimiq-frontend-5ffb567c5c-kqxcg -n claimiq
```

### Error Received

```text
/docker-entrypoint.sh: /docker-entrypoint.d/ is not empty, will attempt to perform configuration

/docker-entrypoint.sh: Looking for shell scripts in /docker-entrypoint.d/

/docker-entrypoint.sh: Launching /docker-entrypoint.d/10-listen-on-ipv6-by-default.sh

10-listen-on-ipv6-by-default.sh: info: Getting the checksum of /etc/nginx/conf.d/default.conf

10-listen-on-ipv6-by-default.sh: info: /etc/nginx/conf.d/default.conf differs from the packaged version

/docker-entrypoint.sh: Sourcing /docker-entrypoint.d/15-local-resolvers.envsh

/docker-entrypoint.sh: Launching /docker-entrypoint.d/20-envsubst-on-templates.sh

/docker-entrypoint.sh: Launching /docker-entrypoint.d/30-tune-worker-processes.sh

/docker-entrypoint.sh: Configuration complete; ready for start up

2026/10/13 01:24:05 [emerg] 1#1: host not found in upstream "backend" in /etc/nginx/conf.d/default.conf:21

nginx: [emerg] host not found in upstream "backend" in /etc/nginx/conf.d/default.conf:21
```

## 5. Why Did This Error Occur?

The important part of the error is:

```text
host not found in upstream "backend"
```

In the Docker Compose setup, the backend service was named `backend`. Docker Compose provides DNS resolution for service names, so Nginx could use `backend` as the hostname to connect to the backend container.

However, in AKS, the backend Kubernetes Service is named `claimiq-backend`.

Kubernetes DNS resolves Kubernetes Service names. It does not automatically know the old Docker Compose service name `backend`.

Because Nginx was still trying to connect to `backend`, it could not resolve that hostname in AKS. Nginx failed to start, and the frontend container exited with error code `1`.

## 6. Resolution

We need to update the backend hostname in the Nginx configuration.

**Before:**

```nginx
proxy_pass http://backend:5000/;
```

**After:**

```nginx
proxy_pass http://claimiq-backend:5000/;
```

Now Nginx uses the actual Kubernetes Service name, `claimiq-backend`, to connect to the backend.

After updating the Nginx configuration, rebuild the frontend image, push the updated image to ACR, and deploy the updated image to AKS.

## 7. Key Takeaways

- `CrashLoopBackOff` means the container is repeatedly failing and Kubernetes is trying to restart it.
- Use `kubectl get pods` to identify which Pod is failing.
- Use `kubectl describe pod` to check the Pod details and events.
- Use `kubectl logs` to find the application or container startup error.
- In Docker Compose, containers can communicate using Compose service names.
- In AKS, applications should use the appropriate Kubernetes Service DNS name.
- Nginx must use the correct backend Service name configured in Kubernetes.
- A hostname mismatch can prevent Nginx from starting and cause the frontend container to fail.

**Remember:** When moving an application from Docker Compose to AKS, check the service hostnames in the Nginx configuration. Docker Compose service names and Kubernetes Service names may be different.
