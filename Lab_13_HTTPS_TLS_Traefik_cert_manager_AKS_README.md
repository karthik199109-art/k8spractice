# Lab 13 -- HTTPS/TLS with Traefik and cert-manager on AKS

## 1. Lab objective

In this lab, we configured production HTTPS for the ClaimIQ application
running on AKS.

Tools and services used:

-   **AKS:** Runs the Kubernetes application.
-   **Traefik:** Ingress controller that receives external traffic and
    routes it to Kubernetes Services.
-   **cert-manager:** Automates certificate issuance and renewal.
-   **Let's Encrypt:** Certificate Authority (CA) that issues the TLS
    certificate.
-   **GoDaddy:** DNS provider for `demoproject.in`.

At the end, both `https://demoproject.in` and
`https://www.demoproject.in` returned `HTTP 200 OK` without bypassing
certificate verification.

## 2. Complete request flow

``` text
User's browser
      |
      | https://demoproject.in
      v
DNS (GoDaddy)
      |
      | Resolves domain to public IP
      v
Azure Load Balancer
      |
      v
Traefik Ingress Controller
      |
      | TLS termination using production certificate
      | Host/path-based routing
      v
Kubernetes Service
      |
      +-----------------------+
      |                       |
      v                       v
Frontend Service         Backend Service
claimiq-frontend:80      claimiq-backend:5000
      |                       |
      v                       v
Frontend Pod             Backend Pods
Nginx                    Application API
```

The browser establishes HTTPS with Traefik. Traefik reads the
certificate and private key from a Kubernetes TLS Secret, terminates
TLS, and forwards the request to the matching Service.

## 3. What is cert-manager?

cert-manager is a Kubernetes add-on that automates certificate
management. It can:

1.  Request certificates from a Certificate Authority.
2.  Complete domain ownership validation.
3.  Store the issued certificate and private key in a Kubernetes TLS
    Secret.
4.  Renew certificates before they expire.

A **Certificate Authority (CA)** is an organisation trusted to issue
digital certificates. In this lab, Let's Encrypt is the CA.

## 4. Install cert-manager using Helm

Add the Jetstack Helm repository and update it:

``` cmd
helm repo add jetstack https://charts.jetstack.io
helm repo update
```

Install cert-manager:

``` cmd
helm install cert-manager jetstack/cert-manager --namespace cert-manager --create-namespace --set crds.enabled=true
```

Check the pods:

``` cmd
kubectl get pods -n cert-manager
```

Components:

-   **cert-manager:** Main controller; watches certificate resources and
    manages requests.
-   **cainjector:** Injects CA bundle information into supported
    resources.
-   **webhook:** Validates and handles admission of cert-manager
    resources.

All three components were running successfully.

## 5. Create the staging ClusterIssuer

A `ClusterIssuer` tells cert-manager which CA to use and how to validate
domain ownership. We first used Let's Encrypt staging to test the
process.

File: `letsencrypt-staging.yaml`

``` yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-staging
spec:
  acme:
    email: YOUR_EMAIL_ADDRESS
    server: https://acme-staging-v02.api.letsencrypt.org/directory
    privateKeySecretRef:
      name: letsencrypt-staging-account-key
    solvers:
      - http01:
          ingress:
            ingressClassName: traefik
```

Apply and verify:

``` cmd
kubectl apply -f letsencrypt-staging.yaml
kubectl get clusterissuer
kubectl describe clusterissuer letsencrypt-staging
```

We confirmed the staging ClusterIssuer became `Ready=True` and its ACME
account was registered.

### Important fields

  -----------------------------------------------------------------------
  Field                               Meaning
  ----------------------------------- -----------------------------------
  `email`                             Email address registered with the
                                      ACME service.

  `server`                            Let's Encrypt ACME endpoint; this
                                      URL is for staging.

  `privateKeySecretRef.name`          Secret that stores the ACME account
                                      private key.

  `http01`                            Uses an HTTP challenge to validate
                                      domain ownership.

  `ingressClassName: traefik`         Uses Traefik for the HTTP-01
                                      challenge.
  -----------------------------------------------------------------------

**Important distinction:** The ACME account private key is not the same
as the website's TLS private key.

## 6. Create a staging Certificate

A `Certificate` resource tells cert-manager which domains need
certificates, which issuer to use, and which Secret should store the
issued certificate.

File: `claimiq-tls.yaml`

``` yaml
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: claimiq-tls
  namespace: claimiq
spec:
  secretName: claimiq-tls-secret
  issuerRef:
    name: letsencrypt-staging
    kind: ClusterIssuer
  dnsNames:
    - demoproject.in
    - www.demoproject.in
```

Apply and check:

``` cmd
kubectl apply -f claimiq-tls.yaml
kubectl get certificate -n claimiq
kubectl describe certificate claimiq-tls -n claimiq
kubectl get certificaterequest,order,challenge -n claimiq
kubectl get secret claimiq-tls-secret -n claimiq
```

The generated Secret had type `kubernetes.io/tls` and contains:

-   `tls.crt` -- The certificate.
-   `tls.key` -- The matching website private key.

### Understand these three fields

-   `privateKeySecretRef`: Secret for the ACME account private key used
    by cert-manager.
-   `issuerRef`: Selects the issuer that should issue the website
    certificate.
-   `secretName`: Destination Secret containing the issued website
    certificate and its private key.

## 7. How HTTP-01 validation works

1.  cert-manager requests a certificate from Let's Encrypt.
2.  Let's Encrypt asks cert-manager to prove control of the domain.
3.  cert-manager creates temporary Kubernetes challenge resources.
4.  Let's Encrypt accesses a special HTTP challenge URL on the domain.
5.  Traefik routes the request to the temporary challenge service.
6.  If validation succeeds, Let's Encrypt issues the certificate.
7.  cert-manager stores the certificate and private key in the requested
    TLS Secret.

Temporary challenge resources can include an Ingress, Service and Pod.
They may be removed after validation.

A temporary Traefik log message that a challenge service was not found
can occur while resources are being created or removed. Check
Certificate, CertificateRequest, Order and Challenge status to determine
whether issuance succeeded.

## 8. Staging versus production certificates

  -----------------------------------------------------------------------
  Staging                             Production
  ----------------------------------- -----------------------------------
  Used for testing                    Used for real users

  Not trusted by normal browsers      Trusted by normal browsers

  Useful to test ACME configuration   Provides the real website
                                      certificate
  -----------------------------------------------------------------------

We initially tested staging using:

``` cmd
curl.exe -vk https://demoproject.in/
```

The `-k` option skips certificate verification. It can help test
connectivity with a staging certificate, but it does not prove that the
certificate is trusted.

## 9. Create the production ClusterIssuer

After the staging test, we created a separate production ClusterIssuer.

File: `letsencrypt-production.yaml`

``` yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-production
spec:
  acme:
    email: YOUR_EMAIL_ADDRESS
    server: https://acme-v02.api.letsencrypt.org/directory
    privateKeySecretRef:
      name: letsencrypt-production-account-key
    solvers:
      - http01:
          ingress:
            ingressClassName: traefik
```

Apply and check:

``` cmd
kubectl apply -f letsencrypt-production.yaml
kubectl get clusterissuer
```

We confirmed `letsencrypt-production` showed `Ready=True`.

The staging ClusterIssuer later showed `False`, but this did not prevent
the production issuer from working. We continued using the production
issuer.

## 10. Create the production Certificate

We created a separate production Certificate and Secret, keeping them
separate from staging.

File: `claimiq-tls-production.yaml`

``` yaml
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: claimiq-tls-production
  namespace: claimiq
spec:
  secretName: claimiq-tls-production-secret
  issuerRef:
    name: letsencrypt-production
    kind: ClusterIssuer
  dnsNames:
    - demoproject.in
    - www.demoproject.in
```

Apply and verify:

``` cmd
kubectl apply -f claimiq-tls-production.yaml
kubectl get certificate -n claimiq
kubectl get secret claimiq-tls-production-secret -n claimiq
```

Our production Certificate showed:

``` text
claimiq-tls-production   True   claimiq-tls-production-secret
```

The production TLS Secret existed before we changed the Ingress to use
it.

## 11. Configure Traefik Ingress to use the production Secret

The relevant TLS section in `claimiq-ingress.yaml` was changed to:

``` yaml
tls:
  - hosts:
      - demoproject.in
      - www.demoproject.in
    secretName: claimiq-tls-production-secret
```

The Ingress uses:

``` yaml
ingressClassName: traefik
```

Our host/path rules were:

  Host                   Path        Kubernetes Service     Service port
  ---------------------- ----------- -------------------- --------------
  `demoproject.in`       `/`         `claimiq-frontend`               80
  `demoproject.in`       `/health`   `claimiq-backend`              5000
  `www.demoproject.in`   `/`         `claimiq-frontend`               80
  `www.demoproject.in`   `/health`   `claimiq-backend`              5000

We changed the Secret reference from the staging Secret,
`claimiq-tls-secret`, to the production Secret,
`claimiq-tls-production-secret`.

Apply and verify:

``` cmd
kubectl apply -f claimiq-ingress.yaml
kubectl describe ingress claimiq-ingress -n claimiq
```

The Ingress showed:

``` text
claimiq-tls-production-secret terminates demoproject.in,www.demoproject.in
```

## 12. Configure DNS in GoDaddy

We purchased `demoproject.in` and configured these DNS records in
GoDaddy.

  Type    Name    Value
  ------- ------- ------------------
  A       `@`     `20.75.140.161`
  CNAME   `www`   `demoproject.in`

### A record

An A record maps a domain name to an IPv4 address:

``` text
demoproject.in -> 20.75.140.161
```

### CNAME record

A CNAME makes one domain name an alias of another:

``` text
www.demoproject.in -> demoproject.in -> 20.75.140.161
```

This means `www` follows the root domain's IP address.

### Verify DNS from Windows CMD

``` cmd
nslookup demoproject.in 8.8.8.8
nslookup www.demoproject.in 8.8.8.8
```

Our final results showed:

``` text
Name:    demoproject.in
Address: 20.75.140.161
```

For `www`:

``` text
Name:    demoproject.in
Address: 20.75.140.161
Aliases: www.demoproject.in
```

Both names resolved to the expected public IP.

**Important:** The GoDaddy A record must point to the current public IP
of the Traefik LoadBalancer. If that IP changes, update the A record. A
stable public IP is recommended for production.

## 13. Verify HTTPS

After switching the Ingress to the production Secret, we tested without
`-k`:

``` cmd
curl.exe -I https://demoproject.in/
curl.exe -I https://www.demoproject.in/
```

Both returned:

``` text
HTTP/1.1 200 OK
```

The response included:

``` text
Content-Type: text/html
Server: nginx/1.31.6
```

Because these commands succeeded without `-k`, certificate verification
passed on the machine where we ran the tests.

## 14. Useful troubleshooting commands

### cert-manager pods

``` cmd
kubectl get pods -n cert-manager
```

### ClusterIssuers

``` cmd
kubectl get clusterissuer
kubectl describe clusterissuer letsencrypt-production
```

### Certificates

``` cmd
kubectl get certificate -n claimiq
kubectl describe certificate claimiq-tls-production -n claimiq
```

### Certificate issuance resources

``` cmd
kubectl get certificaterequest,order,challenge -n claimiq
```

### TLS Secret

``` cmd
kubectl get secret claimiq-tls-production-secret -n claimiq
```

### Ingress

``` cmd
kubectl get ingress -n claimiq
kubectl describe ingress claimiq-ingress -n claimiq
```

### Traefik Service and public IP

``` cmd
kubectl get svc -n traefik
```

### DNS

``` cmd
nslookup demoproject.in 8.8.8.8
nslookup www.demoproject.in 8.8.8.8
```

### HTTPS certificate verification

``` cmd
curl.exe -I https://demoproject.in/
curl.exe -I https://www.demoproject.in/
```

If certificate verification fails, check:

1.  Does the domain resolve to the current Traefik public IP?
2.  Is the production Certificate `Ready=True`?
3.  Does the production TLS Secret exist in the same namespace as the
    Ingress?
4.  Does the Ingress reference the correct Secret name?
5.  Does the Ingress use the correct Traefik IngressClass?
6.  Can the HTTP-01 challenge reach Traefik through public port 80?

## 15. Important concepts to remember

  -----------------------------------------------------------------------
  Resource/component                  Purpose
  ----------------------------------- -----------------------------------
  `ClusterIssuer`                     Defines how cert-manager obtains
                                      certificates from a CA; can be used
                                      across namespaces.

  `Certificate`                       Requests and manages a certificate
                                      for specified domain names.

  `CertificateRequest`                Represents a request to an issuer
                                      for a certificate.

  `Order`                             Represents the ACME order sent to
                                      Let's Encrypt.

  `Challenge`                         Represents domain ownership
                                      validation.

  TLS Secret                          Stores the issued certificate and
                                      its matching private key.

  Ingress                             Defines host/path routing and
                                      references the TLS Secret.

  Traefik                             Implements Ingress routing and
                                      handles incoming TLS connections.

  cert-manager                        Automates certificate issuance and
                                      renewal.

  Let's Encrypt                       CA that issues the certificate.
  -----------------------------------------------------------------------

Remember the relationship:

``` text
ClusterIssuer
    |
    | tells cert-manager who/how to issue
    v
Certificate
    |
    | requests a certificate and names the destination
    v
Kubernetes TLS Secret
    |
    | referenced by
    v
Ingress
    |
    v
Traefik
```

## 16. Lab 13 completion checklist

-   [x] Installed cert-manager using Helm.
-   [x] Verified cert-manager pods were running.
-   [x] Created the Let's Encrypt staging ClusterIssuer.
-   [x] Requested a staging certificate.
-   [x] Verified the staging TLS Secret.
-   [x] Understood HTTP-01 domain validation.
-   [x] Created the Let's Encrypt production ClusterIssuer.
-   [x] Requested the production certificate for both domain names.
-   [x] Verified the production Certificate was `Ready=True`.
-   [x] Updated Traefik Ingress to use the production TLS Secret.
-   [x] Configured GoDaddy DNS for the root domain and `www`.
-   [x] Verified both domain names resolved to the Traefik public IP.
-   [x] Tested both HTTPS URLs without `-k`.
-   [x] Received `HTTP 200 OK` from both domains.

**Lab result:** Production HTTPS was successfully configured for ClaimIQ
on AKS using Traefik, cert-manager and Let's Encrypt.

## 17. Production considerations

1.  **Public IP stability:** Keep the Traefik LoadBalancer public IP
    stable, or update DNS whenever it changes.
2.  **Certificate renewal:** cert-manager manages renewal automatically.
    Keep cert-manager running and monitor Certificate readiness and
    expiry.
3.  **Monitoring:** Monitor cert-manager events, Certificate status and
    Traefik health.
4.  **HTTP-to-HTTPS redirect:** This lab verified HTTPS. An
    HTTP-to-HTTPS redirect is a separate controller/Ingress
    configuration and should be tested separately if required.
5.  **TLS scope:** TLS termination at Traefik encrypts
    browser-to-Traefik traffic. Traffic from Traefik to backend Services
    is separate and is not automatically encrypted by this
    configuration.
6.  **Private key security:** Do not print or share TLS Secret contents.
    Restrict access to Kubernetes Secrets using RBAC.

------------------------------------------------------------------------

**End of Lab 13 -- HTTPS/TLS with Traefik and cert-manager on AKS.**
