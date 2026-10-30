# TLS, SSL Certificates, Private Keys, Certificate Authorities, and TLS Inspection

A beginner-friendly reference guide with practical examples for Linux,
corporate networks, and Kubernetes/AKS.

------------------------------------------------------------------------

## 1. What is a digital certificate?

A **digital certificate** is an electronic document that helps prove the
identity of a website, server, or organisation.

For example, when you open:

``` text
https://www.google.com
```

your browser needs to check that it is really communicating with the
server for `www.google.com`, rather than an impostor.

The server presents a digital certificate. The browser checks that:

-   The certificate covers the requested website name.
-   The certificate is within its validity period.
-   The certificate was signed by a trusted Certificate Authority (CA),
    through a valid certificate chain.
-   The certificate is suitable for the intended use.

If the checks succeed, the browser can trust the server's identity and
continue establishing the secure connection.

### What information is in a certificate?

A certificate commonly contains:

  -----------------------------------------------------------------------
  Field                               Meaning
  ----------------------------------- -----------------------------------
  Subject                             The identity the certificate
                                      represents

  Subject Alternative Name (SAN)      DNS names or other identities
                                      covered by the certificate

  Issuer                              The CA that signed the certificate

  Public key                          The public key associated with the
                                      certificate owner

  Valid From / Valid To               The certificate's validity period

  Serial number                       A unique identifier assigned by the
                                      issuer

  Signature                           The CA's digital signature over the
                                      certificate
  -----------------------------------------------------------------------

Example (illustrative only):

``` text
Subject: CN=claimiq.example.com
SAN: DNS:claimiq.example.com
Issuer: Example Public CA
Public Key: RSA public key
Valid From: 01-Oct-2026
Valid To:   01-Oct-2027
Signature: CA digital signature
```

**Important:** A certificate contains the public key, not the matching
private key.

------------------------------------------------------------------------

## 2. What are public keys and private keys?

A public key and a private key form a mathematically related
**asymmetric key pair**.

A simple analogy:

-   **Public key:** like a lock that can be shared.
-   **Private key:** like the secret key that must be protected by its
    owner.

The analogy is only a learning aid; real public-key cryptography uses
mathematical operations.

  -----------------------------------------------------------------------
  Public key                          Private key
  ----------------------------------- -----------------------------------
  Can be shared                       Must be kept secret

  Usually included in the certificate Kept by the certificate owner or
                                      service

  Can verify a digital signature made Creates digital signatures
  by the matching private key         

  In some cryptographic schemes, can  In those schemes, can decrypt
  encrypt data for the private-key    corresponding data
  owner                               
  -----------------------------------------------------------------------

Example:

``` text
Public key  = public-key-123
Private key = private-key-123
```

These are placeholder names, not real key values.

The website sends its certificate, which contains its public key. It
does **not** send its private key to the browser.

### Important modern TLS detail

Modern TLS does not normally encrypt all website traffic using the
certificate's public key. Instead:

1.  The certificate helps authenticate the server.
2.  Ephemeral key exchange (commonly ECDHE) helps both sides establish
    shared secret material.
3.  Both sides derive symmetric traffic keys.
4.  Symmetric encryption protects the application data.

This is efficient and provides forward secrecy when ephemeral key
exchange is used.

------------------------------------------------------------------------

## 3. What is a Certificate Authority (CA)?

A **Certificate Authority (CA)** is an organisation or service trusted
to issue and sign digital certificates.

Examples include:

-   DigiCert
-   GlobalSign
-   Let's Encrypt
-   Sectigo

A useful analogy is a passport authority:

  Real world                        Digital certificates
  --------------------------------- ----------------------------
  Government/passport authority     Certificate Authority
  Passport                          Digital certificate
  Passport issuer's official mark   CA's digital signature
  Checking the passport             Validating the certificate

### How does a CA issue a certificate?

Suppose you own:

``` text
claimiq.example.com
```

The general process is:

1.  Generate a public/private key pair.
2.  Create a Certificate Signing Request (CSR).
3.  Send the CSR to a CA.
4.  Prove control of the domain (and complete any other required
    validation).
5.  The CA issues and signs a certificate containing your public key and
    the validated identity.
6.  Install the certificate and matching private key where TLS will be
    terminated.

**The private key should remain with its owner. It is not normally sent
to the CA.**

------------------------------------------------------------------------

## 4. What is a CSR?

CSR means **Certificate Signing Request**. It is a request sent to a CA
asking it to issue a certificate.

### Generate a private key

On Linux, using OpenSSL:

``` bash
openssl genrsa -out server.key 2048
```

### Generate a CSR using that private key

``` bash
openssl req -new \
  -key server.key \
  -out server.csr
```

OpenSSL asks for certificate subject details. For a production website,
make sure the requested DNS name is included in the certificate's
Subject Alternative Name (SAN). A CA or certificate-management process
may require a configuration file to specify SANs.

The files are:

``` text
server.key  # Private key: keep secret
server.csr  # Request sent to the CA
server.crt  # Certificate issued by the CA
```

The CA returns the signed certificate after validating the request. The
private key remains with you.

### Inspect a certificate

``` bash
openssl x509 -in server.crt -text -noout
```

### Inspect a CSR

``` bash
openssl req -in server.csr -text -noout
```

### Check that a certificate and private key match

For RSA keys, one common method is to compare their moduli:

``` bash
openssl x509 -noout -modulus -in server.crt | openssl md5
openssl rsa  -noout -modulus -in server.key | openssl md5
```

The outputs should match. (For non-RSA keys, use an appropriate
public-key comparison method instead.)

------------------------------------------------------------------------

## 5. What is a certificate chain?

A browser does not need to trust every website certificate individually.
It can validate a chain of certificates leading back to a Root CA
already trusted by the operating system or browser.

A simplified chain looks like this:

``` text
Root CA certificate
       |
       | signs
       v
Intermediate CA certificate
       |
       | signs
       v
Website certificate
       |
       v
claimiq.example.com
```

-   **Root CA:** The trust anchor. Its certificate is installed in a
    trusted root store.
-   **Intermediate CA:** A CA certificate issued by a root or another
    intermediate. It is commonly used to issue website certificates.
-   **Leaf/server certificate:** The certificate presented by the
    website.

The browser validates the signatures and other certificate rules along
the chain. A website usually sends its leaf certificate and the
necessary intermediate certificates. The root is normally already
trusted locally.

------------------------------------------------------------------------

## 6. What is a Root CA certificate?

A **Root CA certificate** is a CA certificate that acts as a trust
anchor on a device.

For example, a laptop may have a trusted certificate store containing
certificates from public CAs and, in a company-managed environment, the
company's own inspection CA.

``` text
Laptop trusted certificate store
|
|-- Public Root CA A
|-- Public Root CA B
|-- Company Inspection Root CA
```

Two things must not be confused:

-   **Root CA certificate:** Public certificate that can be installed on
    trusted devices.
-   **Root CA private key:** Secret key used by the CA to sign
    certificates. It must be protected and should not be installed on
    employee laptops.

------------------------------------------------------------------------

## 7. How does HTTPS / TLS work?

TLS (Transport Layer Security) protects data sent between two endpoints.
HTTPS is HTTP carried over TLS.

TLS provides, among other things:

1.  **Authentication:** Helps the client verify the server's identity.
2.  **Confidentiality:** Encrypts data so observers cannot normally read
    it.
3.  **Integrity:** Detects unauthorised changes to protected data.

### Simple TLS 1.3 handshake

Suppose you visit:

``` text
https://claimiq.example.com
```

A simplified TLS 1.3 flow is:

``` text
Browser                                      Server
   |                                            |
   |------ ClientHello ------------------------>|
   |       Supported TLS options, key share    |
   |                                            |
   |<----- ServerHello -------------------------|
   |       Selected options, server key share  |
   |                                            |
   |<----- Certificate -------------------------|
   |<----- CertificateVerify ------------------|
   |<----- Finished ----------------------------|
   |                                            |
   |------ Finished --------------------------->|
   |                                            |
   |====== Encrypted application traffic ======|
```

### Step-by-step explanation

**Step 1: ClientHello**

The browser starts the handshake. It sends supported TLS options and an
ephemeral key share.

**Step 2: ServerHello**

The server selects the TLS settings and sends its own ephemeral key
share.

**Step 3: Server certificate**

The server sends its certificate chain. The browser checks the domain
name, validity dates, certificate chain, signatures, and other
requirements.

**Step 4: Proof of private-key possession**

The server sends a `CertificateVerify` message. It signs handshake data
using the private key corresponding to the certificate's public key. The
browser verifies this signature using the public key in the certificate.

**Step 5: Shared secret and traffic keys**

Using the ephemeral key exchange and handshake information, both sides
independently derive matching secret material and TLS traffic keys. The
keys are not simply sent across the network.

**Step 6: Encrypted communication**

The browser and server use symmetric traffic keys (for example, AES-GCM
or ChaCha20-Poly1305) to protect application data.

### Remember

-   The certificate helps prove server identity.
-   The private key proves possession of the certificate's matching key.
-   Ephemeral key exchange helps establish shared secret material.
-   Symmetric traffic keys encrypt and authenticate the actual
    application data.

------------------------------------------------------------------------

## 8. How does TLS decryption happen?

Imagine you send this message to a website:

``` text
Hello ClaimIQ
```

Before it travels over the network, TLS protects it using the
connection's symmetric traffic keys.

Conceptually:

``` text
At browser:
  Original data: Hello ClaimIQ
          |
          v
      TLS encryption
          |
          v
On network:
  Protected/encrypted TLS records
          |
          v
At server:
      TLS decryption
          |
          v
  Original data: Hello ClaimIQ
```

The server uses its matching TLS traffic keys to authenticate and
decrypt the received TLS records. The application then receives the
original request.

The certificate's private key is **not** used to decrypt every
application message. In modern TLS 1.3, the derived symmetric traffic
keys do that work.

------------------------------------------------------------------------

## 9. What is TLS Inspection / TLS Decryption in a company?

Companies may use a secure web gateway or proxy, such as Zscaler, to
inspect web traffic for malware, data leakage, and policy violations.

Normally, HTTPS traffic is encrypted between the laptop and the website.
A network device in the middle cannot ordinarily read the protected
application content.

With **TLS inspection**, the proxy acts as an intermediary and creates
two separate TLS connections:

``` text
Laptop
   |
   | TLS connection 1
   | Encrypted
   v
Corporate proxy / Zscaler
   |
   | TLS connection 2
   | Encrypted separately
   v
Website (for example, Google)
```

The proxy terminates the laptop's TLS connection, inspects the traffic,
and sends permitted traffic over its separate TLS connection to the real
website.

### Step-by-step TLS inspection

Suppose you visit:

``` text
https://www.google.com
```

1.  **Laptop requests the website.** The browser attempts to access
    `www.google.com`.
2.  **Proxy receives the connection.** Company network configuration
    directs the connection through the secure web gateway.
3.  **Proxy connects to Google.** The proxy establishes its own TLS
    connection to the real Google server and validates Google's actual
    certificate.
4.  **Proxy presents a generated certificate to the laptop.** It creates
    a certificate for `www.google.com`, signed by the company's
    inspection CA.
5.  **Laptop validates the generated certificate.** The laptop trusts
    the company's inspection Root CA because IT installed its public
    root certificate in the laptop's trusted certificate store.
6.  **Laptop-to-proxy TLS is established.** The browser and proxy
    establish one TLS connection. The proxy can decrypt traffic on this
    connection.
7.  **Proxy inspects the traffic.** It applies company security
    policies. It may allow, block, or otherwise handle the traffic.
8.  **Proxy forwards allowed traffic.** It sends the request over its
    separate TLS connection to Google and returns the response through
    the first connection.

The proxy does not need Google's private key. It has its own inspection
CA private key and creates a separate TLS connection to Google.

### Without and with TLS inspection

**Without inspection:**

``` text
Laptop  <====== one HTTPS/TLS connection ======>  Website
```

**With inspection:**

``` text
Laptop  <==== TLS connection 1 ====>  Proxy
                                      |
                                      | Proxy decrypts and inspects
                                      |
Website <==== TLS connection 2 ======+
```

### Why install the company Root CA on laptops?

The browser must be able to validate the proxy-generated website
certificate. The company distributes its Root CA **certificate** to
managed devices so those devices trust certificates signed by that CA.

The matching Root CA private key stays securely within the CA/proxy
infrastructure. It must never be distributed to employee devices.

**Note:** TLS inspection can be affected by certificate pinning, mutual
TLS, application-specific trust stores, and company policy. Some traffic
may be excluded from inspection.

------------------------------------------------------------------------

## 10. TLS termination vs TLS decryption

These terms are related:

-   **TLS termination:** A component ends a TLS connection. It handles
    the TLS session and can access the decrypted application data.
-   **TLS decryption:** The process of recovering the original data from
    protected TLS records at an endpoint that has the correct traffic
    keys.
-   **TLS inspection:** A proxy terminates a TLS connection to inspect
    the traffic, and may then send it over another TLS connection.
-   **TLS passthrough:** A component forwards the encrypted TLS
    connection without terminating or decrypting it.

### TLS termination example

Suppose ClaimIQ runs in AKS:

``` text
Browser
   |
   | HTTPS (443)
   v
NGINX Ingress Controller
   |
   | HTTP (5000) in this example
   v
Backend Kubernetes Service
   |
   v
Backend Pod
```

What happens?

1.  The browser connects to the Ingress using HTTPS.
2.  The Ingress presents the ClaimIQ certificate.
3.  The browser validates the certificate.
4.  The Ingress handles the TLS connection and decrypts incoming
    application traffic.
5.  The Ingress forwards the HTTP request to the backend Service.
6.  The Service routes the request to a backend Pod.

This is **TLS termination at the Ingress**.

In this example, traffic from Ingress to the backend is HTTP, so that
internal hop is not encrypted with TLS. If encryption is required on
that hop, configure HTTPS between the Ingress and backend as well.

### TLS passthrough example

``` text
Browser
   |
   | Encrypted TLS connection
   v
Ingress / TCP load balancer
   |
   | Still encrypted; no TLS termination here
   v
Backend application
   |
   | Backend terminates TLS
```

With passthrough, the backend application handles the TLS certificate
and private key. The intermediary cannot inspect HTTP paths or headers
because the HTTP content remains encrypted.

  -----------------------------------------------------------------------
  TLS termination                     TLS passthrough
  ----------------------------------- -----------------------------------
  Ingress ends the TLS connection     Ingress forwards the TLS connection

  Ingress has the certificate and     Backend has the certificate and
  private key                         private key

  Ingress can route using HTTP        Intermediary cannot read encrypted
  host/path information               HTTP paths

  Backend may receive HTTP or a new   Backend handles the original TLS
  HTTPS connection                    connection
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 11. TLS in Kubernetes / AKS

For ClaimIQ, imagine the public application URL is:

``` text
https://claimiq.example.com
```

You configure TLS on your Kubernetes Ingress.

### Example Ingress manifest

``` yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: claimiq-ingress
  namespace: claimiq
spec:
  tls:
    - hosts:
        - claimiq.example.com
      secretName: claimiq-tls

  rules:
    - host: claimiq.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: claimiq-backend
                port:
                  number: 5000
```

The `tls` section tells the Ingress which hostname and TLS Secret to
use.

### Example Kubernetes TLS Secret

A TLS Secret has two important data entries:

``` yaml
apiVersion: v1
kind: Secret
metadata:
  name: claimiq-tls
  namespace: claimiq
type: kubernetes.io/tls
data:
  tls.crt: BASE64_ENCODED_CERTIFICATE
  tls.key: BASE64_ENCODED_PRIVATE_KEY
```

-   `tls.crt`: The certificate (and, where required, its certificate
    chain).
-   `tls.key`: The matching private key.

The values above are placeholders. Do not use them as real certificate
or key data.

### Create a TLS Secret from files

If you already have the certificate and private key:

``` bash
kubectl create secret tls claimiq-tls \
  --cert=server.crt \
  --key=server.key \
  -n claimiq
```

### Verify the Secret

``` bash
kubectl get secret claimiq-tls -n claimiq
kubectl describe secret claimiq-tls -n claimiq
```

To inspect the certificate stored in the Secret:

``` bash
kubectl get secret claimiq-tls -n claimiq \
  -o jsonpath='{.data.tls\.crt}' | base64 -d | \
  openssl x509 -noout -subject -issuer -dates -ext subjectAltName
```

To inspect the certificate resource if you use cert-manager:

``` bash
kubectl describe certificate claimiq-tls -n claimiq
```

Remember: a Kubernetes Secret is base64-encoded by default, not
automatically encrypted just because it is a Secret. Protect access with
RBAC, enable encryption at rest for Kubernetes Secrets, and follow your
organisation's key-management practices.

### ClaimIQ request flow

``` text
Browser
   |
   | HTTPS
   v
Azure Load Balancer
   |
   v
NGINX Ingress Controller
   |
   | Reads claimiq-tls Secret
   | Uses certificate and private key
   | Terminates TLS
   |
   | HTTP in this example
   v
claimiq-backend Service
   |
   v
Backend Pod
```

------------------------------------------------------------------------

## 12. Useful OpenSSL commands

### Generate a private key

``` bash
openssl genrsa -out server.key 2048
```

### Generate a CSR

``` bash
openssl req -new \
  -key server.key \
  -out server.csr
```

### View certificate details

``` bash
openssl x509 -in server.crt -text -noout
```

### View CSR details

``` bash
openssl req -in server.csr -text -noout
```

### Inspect a live website's certificate and TLS connection

``` bash
openssl s_client \
  -connect google.com:443 \
  -servername google.com
```

The `-servername` option sends the SNI hostname, which helps the server
select the correct certificate when multiple websites share an IP
address.

To display only the certificate dates and identity details:

``` bash
openssl s_client -connect google.com:443 -servername google.com </dev/null 2>/dev/null \
  | openssl x509 -noout -subject -issuer -dates
```

------------------------------------------------------------------------

## 13. Quick revision table

  -----------------------------------------------------------------------
  Term                                Simple meaning
  ----------------------------------- -----------------------------------
  Certificate                         Digital document used to prove
                                      identity

  Public key                          Public part of an asymmetric key
                                      pair

  Private key                         Secret part of an asymmetric key
                                      pair

  CA                                  Trusted authority that signs
                                      certificates

  Root CA                             Trust anchor in a device's trusted
                                      certificate store

  Intermediate CA                     CA between the root and website
                                      certificate

  CSR                                 Request sent to a CA to obtain a
                                      certificate

  Certificate chain                   Certificates linking a website
                                      certificate to a trusted root

  TLS                                 Protocol that protects data in
                                      transit

  HTTPS                               HTTP protected by TLS

  TLS handshake                       Process used to establish a secure
                                      TLS connection

  Session/traffic keys                Symmetric keys used to protect TLS
                                      data

  TLS termination                     Component where a TLS connection
                                      ends

  TLS inspection                      Proxy decrypts and checks traffic,
                                      then forwards it over another
                                      connection

  TLS passthrough                     Encrypted TLS connection is
                                      forwarded without being terminated
                                      at that intermediary

  TLS Secret                          Kubernetes Secret containing
                                      `tls.crt` and `tls.key`
  -----------------------------------------------------------------------

## 14. Remember the complete picture

``` text
Certificate
   |
   | Contains
   v
Public Key
   |
   | Mathematically matches
   v
Private Key (kept secret)

CA
   |
   | Validates identity and signs
   v
Certificate

Browser + Server
   |
   | TLS handshake and key exchange
   v
Shared secret material
   |
   | Derive
   v
Symmetric traffic keys
   |
   | Protect application data
   v
Encrypted HTTPS communication

Corporate TLS inspection:
Laptop
   |
   | TLS connection 1
   v
Proxy (decrypt -> inspect -> encrypt)
   |
   | TLS connection 2
   v
Website

Kubernetes TLS termination:
Browser
   |
   | HTTPS
   v
Ingress (certificate + private key; terminates TLS)
   |
   | HTTP or separately configured HTTPS
   v
Backend Service -> Backend Pod
```

### The five most important things to remember

1.  A certificate proves identity; it contains a public key, not the
    private key.
2.  The private key must remain secret and protected.
3.  A CA signs certificates so clients can validate trust.
4.  TLS uses a handshake to establish symmetric traffic keys; those keys
    protect the actual application data.
5.  TLS inspection uses two TLS connections through a proxy, while
    Kubernetes Ingress TLS termination ends the browser's TLS connection
    at the Ingress.

------------------------------------------------------------------------

## 15. Knowledge check

Try answering these questions without looking at the earlier sections.

1.  What is the difference between a certificate and a private key?
2.  Why do we need a Certificate Authority?
3.  What is the purpose of a CSR?
4.  Does the browser receive the server's private key?
5.  Which keys normally encrypt actual application data in modern TLS?
6.  Why does a company install its Root CA certificate on employee
    laptops?
7.  In TLS inspection, why are there two TLS connections?
8.  Where does TLS termination happen in the ClaimIQ Ingress example?
9.  What are `tls.crt` and `tls.key` in a Kubernetes TLS Secret?
10. What is the difference between TLS termination and TLS passthrough?

**Suggested learning order:** Understand Sections 1--7 first, then
Sections 8--10, and finally practise Sections 11--12 on your Linux VM
and AKS cluster.
