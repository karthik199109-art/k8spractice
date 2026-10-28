# Kubernetes Services, DNS, CoreDNS, and Load Balancing

## 1. What is a Kubernetes Service?

A **Kubernetes Service** provides a stable network endpoint for accessing a group of Pods.

Pods are temporary. Their IP addresses can change when they are recreated. A Service provides a stable IP address and DNS name so that other applications can communicate with the Pods without needing to know their individual IP addresses.

### Why do we need Services?

Suppose we have three backend Pods:

- Backend Pod 1: `10.244.1.10`
- Backend Pod 2: `10.244.2.15`
- Backend Pod 3: `10.244.3.20`

If the frontend connects directly to a backend Pod IP, communication may fail when that Pod is recreated and receives a new IP address.

Instead, we create a Kubernetes Service called `backend-service`.

The frontend connects to `backend-service`, and Kubernetes networking directs the traffic to an eligible backend Pod.

**Remember:** A Service provides a stable endpoint, while Pods provide the actual application instances.

---

## 2. Types of Kubernetes Services

Kubernetes has four commonly discussed Service types:

1. ClusterIP
2. NodePort
3. LoadBalancer
4. ExternalName

### 2.1 ClusterIP

**ClusterIP is the default Service type in Kubernetes.**

It exposes an application through an internal cluster IP address. It is generally used for communication between applications inside the cluster.

For example:

- Frontend communicates with the backend.
- Backend communicates with an internal authentication service.
- Backend communicates with another internal microservice.

#### Example

```yaml
apiVersion: v1
kind: Service
metadata:
  name: backend-service
spec:
  type: ClusterIP
  selector:
    app: backend
  ports:
    - port: 80
      targetPort: 5000
```

Explanation:

- `type: ClusterIP`: Creates an internal Service.
- `selector: app: backend`: Selects Pods with the label `app=backend`.
- `port: 80`: Port exposed by the Service.
- `targetPort: 5000`: Port on which the backend application listens inside the Pod.

The frontend can access the backend using:

```text
http://backend-service
```

For communication across namespaces, use the fully qualified Service DNS name:

```text
http://backend-service.<namespace>.svc.cluster.local
```

The namespace in this example must be replaced with the namespace containing the backend Service.

#### How does ClusterIP work?

1. Kubernetes creates a Service with a stable virtual IP.
2. CoreDNS enables other Pods to resolve the Service name to its IP address.
3. The request reaches the Service IP.
4. Kubernetes networking selects an eligible backend endpoint.
5. The request reaches one of the backend Pods.

**Important:** ClusterIP is normally reachable only within the cluster. External access requires an appropriate networking path, such as a LoadBalancer, NodePort, or Ingress.

### 2.2 NodePort

NodePort exposes a Service on a port across the cluster's nodes.

For example, if the NodePort is `30080`, the application may be accessed using:

```text
http://<node-ip>:30080
```

Example YAML:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: backend-nodeport
spec:
  type: NodePort
  selector:
    app: backend
  ports:
    - port: 80
      targetPort: 5000
      nodePort: 30080
```

Explanation:

- `port: 80`: Service port.
- `targetPort: 5000`: Application port inside the Pod.
- `nodePort: 30080`: Port exposed on the nodes.

The default NodePort range is `30000-32767`, unless the cluster is configured differently.

#### When do we use NodePort?

- Testing an application.
- Learning Kubernetes networking.
- Providing access through an existing external load balancer or network device.

NodePort does not automatically mean that only internal users can access the application. Accessibility depends on node networking, routing, firewalls, and security rules.

### 2.3 LoadBalancer

LoadBalancer exposes a Service through an external or internal load balancer supported by the Kubernetes environment.

In Azure Kubernetes Service (AKS), a `LoadBalancer` Service can provision or configure an Azure Load Balancer frontend.

Example:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: frontend-service
spec:
  type: LoadBalancer
  selector:
    app: frontend
  ports:
    - port: 80
      targetPort: 8080
```

Explanation:

- `type: LoadBalancer`: Requests load balancer integration.
- `port: 80`: Port exposed by the Service.
- `targetPort: 8080`: Port used by the frontend application.

Depending on the configuration, the Service may receive an external IP address or an internal IP address.

#### When do we use LoadBalancer?

- Exposing an application externally.
- Providing a stable external entry point.
- Allowing clients outside the cluster to access an application.

**Important:** A LoadBalancer Service does not automatically send traffic to an Ingress controller. It usually directs traffic to the endpoints of the Service it exposes. To expose an Ingress controller, a LoadBalancer Service is commonly created for that controller.

### 2.4 ExternalName

ExternalName allows a Kubernetes Service name to act as an alias for an external DNS hostname.

It is useful when an application inside Kubernetes needs to access a service outside the cluster, such as an externally hosted database or API.

Example:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: external-database
spec:
  type: ExternalName
  externalName: db.example.com
```

A Pod can use the following hostname:

```text
external-database
```

CoreDNS returns a DNS CNAME pointing to:

```text
db.example.com
```

The external hostname must resolve to an address that the Pod can reach.

#### Important points

- ExternalName does not create a ClusterIP.
- It does not create EndpointSlices for backend Pods.
- It does not proxy traffic to the external service.
- It does not create a load balancer.
- The application must still be able to reach the external destination through the network.

**Remember:** ExternalName provides DNS aliasing, not traffic forwarding.

---

## 3. How Kubernetes Selects the Correct Pods

A Service uses a label selector to identify the Pods that should receive traffic.

For example, a backend Pod may have these labels:

```yaml
metadata:
  labels:
    app: backend
```

The Service uses the same label:

```yaml
selector:
  app: backend
```

Kubernetes identifies matching Pods and maintains the corresponding endpoint information through EndpointSlices.

For example:

```text
backend-service
       |
       +---- Backend Pod 1: 10.244.1.10
       |
       +---- Backend Pod 2: 10.244.2.15
       |
       +---- Backend Pod 3: 10.244.3.20
```

When a matching Pod becomes ready, it can become an eligible endpoint. When the Pod is deleted or stops being eligible, Kubernetes updates the endpoint information accordingly.

**Remember:** Labels and selectors identify the Pods; EndpointSlices represent the endpoints; Kubernetes networking directs traffic to those endpoints.

---

## 4. What Is DNS?

DNS stands for **Domain Name System**.

DNS translates hostnames into information required to reach a destination, commonly an IP address.

For example:

```text
www.example.com
       |
       v
DNS lookup
       |
       v
IP address
```

Instead of remembering an IP address, a user can access a service using its hostname.

### What is a DNS server?

A DNS server answers DNS queries using DNS records, cached information, or queries to other DNS servers.

DNS does not necessarily contain every domain name and IP address in one central server.

### What is nslookup?

`nslookup` is a command-line utility used to query DNS.

Example:

```bash
nslookup www.example.com
```

It displays DNS information, including the resolved address when an address record is available.

To query a specific DNS server:

```bash
nslookup www.example.com 8.8.8.8
```

If the hostname cannot be resolved, the command may return an error such as `NXDOMAIN` or a timeout, depending on the cause.

**Remember:** DNS resolves names; it does not route the application's network traffic itself.

---

## 5. Kubernetes DNS and CoreDNS

Kubernetes provides DNS-based service discovery so that Pods can communicate using Service names rather than hard-coded IP addresses.

CoreDNS is the DNS server commonly deployed in Kubernetes clusters.

The Kubernetes DNS Service is often named `kube-dns`, even when CoreDNS is the actual DNS server implementation.

### What does CoreDNS do?

CoreDNS answers DNS queries for Kubernetes Services and other configured DNS names.

For example, suppose the backend Service is named:

```text
backend-service
```

A frontend Pod in the same namespace can connect using:

```text
http://backend-service
```

CoreDNS resolves the Service name to the Service's ClusterIP.

For a Service in another namespace:

```text
http://backend-service.production.svc.cluster.local
```

Here:

- `backend-service`: Service name.
- `production`: Namespace.
- `svc`: Indicates a Kubernetes Service.
- `cluster.local`: The commonly used cluster DNS domain; it can be configured differently.

### How does CoreDNS work?

1. A Pod requests the DNS resolution of `backend-service`.
2. The Pod's DNS configuration directs the query to the cluster DNS Service.
3. CoreDNS processes the query using Kubernetes service information.
4. For a normal ClusterIP Service, CoreDNS returns the Service IP address.
5. The application connects to that IP.
6. Kubernetes networking directs the traffic to an eligible backend endpoint.

**Important:** CoreDNS resolves the Service name. It does not normally choose the backend Pod for each application request.

For a headless Service, DNS can return the addresses of the eligible endpoints instead of a single ClusterIP.

---

## 6. What Is kube-proxy?

kube-proxy is a Kubernetes component that implements Service networking on many cluster configurations.

It watches Service and endpoint information and configures networking rules so that traffic addressed to a Service can reach its eligible endpoints.

Depending on the cluster configuration, it can use mechanisms such as `iptables` or IPVS. Some Kubernetes networking implementations replace kube-proxy with their own Service-routing functionality.

### Example

Suppose a backend Service has three eligible Pods:

```text
backend-service:80
        |
        v
Kubernetes Service networking
        |
        +---- Pod 1:5000
        +---- Pod 2:5000
        +---- Pod 3:5000
```

A request to the Service is directed to an eligible endpoint.

**Remember the responsibilities:**

- CoreDNS: Resolves the Service name.
- Service: Provides a stable virtual endpoint.
- EndpointSlices: Track eligible endpoints.
- kube-proxy or an alternative networking implementation: Implements Service traffic forwarding.

---

## 7. Complete Request Flow: External User to Backend Pod

Consider an application with these components:

- External user
- Azure Load Balancer
- Ingress controller
- Frontend application
- Backend application
- CoreDNS
- Kubernetes Services

The flow depends on the architecture, but a common setup works as follows.

### Step 1: The external user sends a request

The user opens:

```text
https://app.example.com
```

DNS for the application's public hostname resolves to the public IP configured for the application's entry point.

### Step 2: The request reaches the Azure Load Balancer

The Azure Load Balancer receives the network traffic and forwards it according to its configuration to the Ingress controller's exposed Service or another configured destination.

The Load Balancer does not automatically understand application URL paths such as `/api/claims`.

### Step 3: The Ingress controller processes the request

The Ingress controller receives the request and evaluates the configured Ingress rules.

For example:

```text
/app/*  -> frontend-service
/api/*  -> backend-service
```

These are illustrative rules. The actual routing depends on the configured Ingress resource and controller.

### Step 4: The frontend communicates with the backend

When the frontend needs backend data, it sends a request to the backend Service.

For example:

```text
http://backend-service
```

The backend Service hostname is resolved through CoreDNS if DNS resolution is needed.

If the frontend is a browser-based application, the browser may instead send the API request directly to a public API hostname. In that architecture, the browser does not use the internal Kubernetes Service DNS name.

### Step 5: Kubernetes directs traffic to a backend endpoint

The request reaches the backend Service IP or another applicable Service endpoint.

Kubernetes networking directs it to an eligible backend Pod, for example:

```text
backend-service
       |
       +---- Backend Pod 1
       +---- Backend Pod 2
       +---- Backend Pod 3
```

The selected Pod processes the request and returns the response.

### Complete flow

```text
External User
      |
      v
Public DNS
      |
      v
Azure Load Balancer
      |
      v
Ingress Controller
      |
      v
Frontend Service
      |
      v
Frontend Pod
      |
      v
CoreDNS resolves backend-service
      |
      v
Backend Service
      |
      v
Kubernetes Service networking
      |
      v
Eligible Backend Pod
      |
      v
Response
```

This diagram represents one possible architecture. If the frontend and backend are routed through the same Ingress, or if the frontend is browser-based, the request path can be different.

---

## 8. Can We Use Ingress Instead of LoadBalancer?

Ingress and LoadBalancer solve different problems.

### LoadBalancer

- Exposes a Service through a cloud or supported external load balancer.
- Provides an external or internal network entry point.
- Typically operates at the network or transport layer for the configured Service.

### Ingress

- Defines HTTP/HTTPS routing rules.
- Can route requests based on hostnames and URL paths.
- Requires an Ingress controller to implement those rules.

### Example

Suppose we have two applications:

```text
https://example.com/       -> frontend
https://example.com/api    -> backend
```

With a single Ingress controller, one common architecture is:

```text
Internet
   |
   v
Azure Load Balancer
   |
   v
Ingress Controller
   |
   +---- /     -> frontend-service
   |
   +---- /api  -> backend-service
```

The Ingress controller is commonly exposed using a LoadBalancer Service.

### Can we avoid a separate LoadBalancer for every application?

Yes. One LoadBalancer Service for the Ingress controller can expose multiple applications through HTTP/HTTPS routing rules.

However, the Ingress controller still needs an appropriate network entry point. In AKS, this is commonly provided by an Azure Load Balancer.

**Remember:**

- LoadBalancer provides the network entry point.
- Ingress defines HTTP/HTTPS routing.
- Ingress controller implements the routing rules.

Ingress is not a direct replacement for every type of LoadBalancer Service.

---

## 9. Azure Load Balancer: Inbound and Outbound Traffic

In Azure environments, inbound and outbound connectivity are separate networking concerns.

### Inbound traffic

Inbound traffic is traffic coming from a client outside the application environment.

For example:

```text
Internet
   |
   v
Public IP
   |
   v
Azure Load Balancer
   |
   v
Configured backend destination
```

Inbound load-balancing rules define how traffic received on a frontend IP and port is distributed to configured backend destinations.

### Outbound traffic

Outbound traffic is traffic initiated by a workload toward an external destination.

For example:

```text
Backend Pod
    |
    v
Node / Cluster Networking
    |
    v
Configured Outbound Connectivity
    |
    v
External API
```

Depending on the AKS networking configuration, outbound connectivity may use a Load Balancer outbound rule, NAT Gateway, or another supported networking path.

### Does a Load Balancer always have two public IPs?

No.

A Load Balancer does not necessarily require one public IP for inbound traffic and another public IP for outbound traffic.

The configuration may use:

- One frontend IP for inbound traffic.
- The same or a separate frontend IP for outbound traffic.
- Multiple frontend IPs.
- An internal frontend IP.
- A NAT Gateway or another outbound connectivity mechanism.

**Remember:** Inbound load-balancing rules and outbound rules serve different purposes, but they do not always require separate public IP addresses.

---

## 10. Quick Revision Table

| Component | Main responsibility |
|---|---|
| Service | Provides a stable endpoint for accessing applications |
| ClusterIP | Internal Service access |
| NodePort | Exposes a Service on a port across cluster nodes |
| LoadBalancer | Exposes a Service through a supported load balancer |
| ExternalName | Maps a Service DNS name to an external hostname using CNAME |
| Labels | Identify Pods |
| Selectors | Match Pods for a Service |
| EndpointSlices | Track the Service's endpoints |
| CoreDNS | Resolves Kubernetes Service DNS names |
| kube-proxy | Implements Service traffic forwarding on clusters that use it |
| Ingress | Defines HTTP/HTTPS routing rules |
| Ingress controller | Implements Ingress routing rules |
| Azure Load Balancer | Distributes configured network traffic |
| `nslookup` | Tests DNS resolution |

## 11. Important Points to Remember

1. Pods can be recreated, so their IP addresses are not a reliable permanent endpoint.
2. Services provide stable endpoints for accessing applications.
3. ClusterIP is the default Service type.
4. NodePort exposes a Service through a port on cluster nodes.
5. LoadBalancer exposes a Service through a supported load balancer.
6. ExternalName provides DNS aliasing; it does not proxy network traffic.
7. Labels and selectors determine which Pods are selected by a Service.
8. EndpointSlices track the Service's endpoints.
9. CoreDNS resolves Service names; it does not forward application traffic.
10. kube-proxy or an alternative networking implementation handles Service traffic forwarding.
11. Ingress defines HTTP/HTTPS routing, while the Ingress controller implements it.
12. An Ingress controller is commonly exposed using a LoadBalancer Service.
13. Inbound and outbound connectivity are different, but they do not always require separate public IPs.

**One-line summary:** DNS resolves names, Services provide stable endpoints, EndpointSlices track eligible Pods, Kubernetes networking forwards traffic, and Ingress routes HTTP/HTTPS requests to the appropriate Services.