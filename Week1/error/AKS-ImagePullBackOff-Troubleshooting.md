# Kubernetes Troubleshooting: ImagePullBackOff

## 1. What is ImagePullBackOff?

`ImagePullBackOff` occurs when Kubernetes is unable to pull the container image from the container registry.

When Kubernetes tries to start a Pod, it first needs to download the required container image. If the image pull fails, Kubernetes cannot start the container and keeps retrying after waiting for some time.

## 2. Step 1: Describe the Pod

To troubleshoot this issue, we mainly use the following command:

```bash
kubectl describe pod claimiq-backend-864447c689-qnmrc -n claimiq
```

### Why do we use `kubectl describe pod` instead of checking container logs?

We use `kubectl describe pod` because this issue occurs while Kubernetes is trying to pull the image.

The image-pulling process happens before the container is created and started. If the image cannot be pulled, the container does not start, so there are no application container logs to check.

The Pod description shows the container state and the events that explain why the image pull failed.

## 3. Error Faced During Deployment

Below is the Pod information and error I received while deploying the ClaimIQ backend.

```text
Name:             claimiq-backend-864447c689-qnmrc
Namespace:        claimiq
Priority:         0
Service Account:  default
Node:             aks-agentpool-28524209-vmss000000/10.224.0.4
Start Time:       Tue, 13 Oct 2026 00:46:21 +0000
Labels:           app=claimiq-backend
                  pod-template-hash=864447c689
                  topology.kubernetes.io/region=eastus
                  topology.kubernetes.io/zone=0
Annotations:      <none>
Status:           Pending
IP:               10.244.1.226
IPs:
  IP:             10.244.1.226
Controlled By:    ReplicaSet/claimiq-backend-864447c689
Containers:
  backend:
    Container ID:
    Image:         claimqregistry.azurecr.io/claimiq-backend:latest
    Image ID:
    Port:          5000/TCP
    Host Port:     0/TCP
    State:         Waiting
      Reason:      ImagePullBackOff
    Ready:         False
    Restart Count: 0
    Limits:
      cpu:         500m
      memory:      512Mi
    Requests:
      cpu:         100m
      memory:      128Mi
    Environment:
      DB_HOST:     postgres
      DB_PORT:     5432
      DB_NAME:     <set to the key 'POSTGRES_DB' in secret 'postgres-secret'>        Optional: false
      DB_USER:     <set to the key 'POSTGRES_USER' in secret 'postgres-secret'>      Optional: false
      DB_PASSWORD: <set to the key 'POSTGRES_PASSWORD' in secret 'postgres-secret'>  Optional: false
    Mounts:
      /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-pxwlt (ro)

Conditions:
  Type                        Status
  PodReadyToStartContainers   True
  Initialized                 True
  Ready                       False
  ContainersReady             False
  PodScheduled                True

Volumes:
  kube-api-access-pxwlt:
    Type:                     Projected (a volume that contains injected data from multiple sources)
    TokenExpirationSeconds:   3607
    ConfigMapName:            kube-root-ca.crt
    Optional:                 false
    DownwardAPI:              true

QoS Class:                    Burstable
Node-Selectors:               <none>
Tolerations:                  node.kubernetes.io/memory-pressure:NoSchedule op=Exists
                              node.kubernetes.io/not-ready:NoExecute for 300s
                              node.kubernetes.io/unreachable:NoExecute for 300s

Events:
  Type     Reason     Age                    From               Message
  ----     ------     ----                   ----               -------
  Normal   Scheduled  5m36s                  default-scheduler  Successfully assigned claimiq/claimiq-backend-864447c689-qnmrc to aks-agentpool-28524209-vmss000000
  Normal   Pulling    2m38s (x5 over 5m35s)  kubelet            spec.containers{backend}: Pulling image "claimqregistry.azurecr.io/claimiq-backend:latest"
  Warning  Failed     2m38s (x5 over 5m35s)  kubelet            spec.containers{backend}: Failed to pull image "claimqregistry.azurecr.io/claimiq-backend:latest": failed to pull and unpack image "claimqregistry.azurecr.io/claimiq-backend:latest": failed to resolve image: failed to authorize: failed to fetch anonymous token: unexpected status from GET request to https://claimqregistry.azurecr.io/oauth2/token?scope=repository%3Aclaimiq-backend%3Apull&service=claimqregistry.azurecr.io: 401 Unauthorized
  Warning  Failed     2m38s (x5 over 5m35s)  kubelet            spec.containers{backend}: Error: ErrImagePull
  Warning  Failed     33s (x20 over 5m34s)  kubelet            spec.containers{backend}: Error: ImagePullBackOff
  Normal   BackOff    21s (x21 over 5m34s)  kubelet            spec.containers{backend}: Back-off pulling image "claimqregistry.azurecr.io/claimiq-backend:latest"
```

## 4. Understanding the Error

The important part of the error is:

```text
401 Unauthorized
```

This means Kubernetes tried to access Azure Container Registry (ACR), but the request was not authorized.

From the error, we can understand:

1. The Pod was successfully scheduled to a Kubernetes node.
2. Kubernetes tried to pull the backend image from ACR.
3. The image pull failed because authentication was not successful.
4. ACR returned `401 Unauthorized`.
5. Kubernetes reported `ErrImagePull` and then `ImagePullBackOff`.

## 5. Resolution

The main reason for this issue was that we had not assigned the required **ACR Pull permission** to the AKS node pool's **System-Assigned Managed Identity**.

The AKS nodes use this identity to authenticate and pull container images from ACR.

We need to grant the appropriate ACR pull permission to the identity used by the AKS cluster so that the nodes can download the required images.

## 6. Key Takeaways

- `ImagePullBackOff` means Kubernetes is unable to pull the required container image.
- Use `kubectl describe pod` to check the Pod status and events.
- Container logs are not available when the container has not started.
- `ErrImagePull` indicates that an image pull attempt failed.
- `ImagePullBackOff` means Kubernetes is waiting before retrying the image pull.
- `401 Unauthorized` indicates an authentication or authorization problem when accessing the registry.
- In this case, the issue was resolved by providing the required ACR Pull permission to the AKS node pool's System-Assigned Managed Identity.

**Remember:** If the container image cannot be pulled, first check the Pod events using `kubectl describe pod`. Look for the exact error, such as `401 Unauthorized`, to identify whether the issue is related to registry authentication or permissions.
