**# Docker Compose and Nginx**



**## 1. Docker Compose**



**### What is Docker Compose?**



Docker Compose is a tool used to define, build, and run multiple containers together using a single YAML file called \`compose.yaml\` or \`docker-compose.yml\`.



For example, an application may contain:

\- **\*\*Frontend:\*\*** User interface

\- **\*\*Backend:\*\*** Application logic and APIs

\- **\*\*Database:\*\*** Stores application data



Without Docker Compose, we may need to run multiple Docker commands separately. With Docker Compose, we can define all the services in one YAML file and manage them together.



**\*\*Important:\*\*** Docker Compose manages containers, networks, and volumes. It can also build or pull Docker images.



**### Sample Docker Compose File**



\`\`\`yaml

services:

  frontend:

    build: ./frontend

    image: my-frontend:v1

    ports:

      - "80:80"

    depends_on:

      - backend



  backend:

    build: ./backend

    image: my-backend:v1

    environment:

      DB_HOST: database

    depends_on:

      - database



  database:

    image: postgres:16

    environment:

      POSTGRES_USER: admin

      POSTGRES_PASSWORD: example

      POSTGRES_DB: appdb

\`\`\`



**### Explanation of the Fields**



\| Field | Description |

\|---|---|

\| \`services\` | Defines the application services. |

\| \`frontend\`, \`backend\`, \`database\` | Service names used to identify each component. |

\| \`build\` | Specifies the directory containing the Dockerfile. |

\| \`image\` | Specifies the image name and tag. |

\| \`ports\` | Maps a host port to a container port. |

\| \`environment\` | Defines environment variables inside the container. |

\| \`depends_on\` | Defines dependencies and startup order between services. |



For example, \`build: ./frontend\` means Docker Compose looks for a Dockerfile inside the \`frontend\` directory.



**### Service Communication**



Docker Compose normally creates a shared network for the application services.



Services can communicate with each other using their service names as DNS hostnames.



Examples:



\- Frontend communicates with the backend using \`http\://backend:5000\`.

\- Backend connects to PostgreSQL using \`database:5432\`.



We generally do not need to hardcode container IP addresses because Docker's internal DNS resolves the service names.



**### What is \`depends_on\`?**



\`depends_on\` defines the order in which services are started.



For example:



\`\`\`yaml

services:

  backend:

    build: ./backend

    depends_on:

      - database



  database:

    image: postgres:16

\`\`\`



Here, Docker Compose starts the database before starting the backend.



**\*\*Important:\*\*** \`depends_on\` alone does not guarantee that the database is ready to accept connections. It normally waits for the dependency's container to start, not for the application to become healthy.



**### What is a Health Check?**



A health check verifies whether an application inside a container is functioning properly.



Example:



\`\`\`yaml

services:

  backend:

    build: ./backend

    depends_on:

      database:

        condition: service_healthy



  database:

    image: postgres:16

    environment:

      POSTGRES_USER: admin

      POSTGRES_PASSWORD: example

      POSTGRES_DB: appdb

    healthcheck:

      test: ["CMD-SHELL", "pg_isready -U admin -d appdb"]

      interval: 10s

      timeout: 5s

      retries: 5

      start_period: 10s

\`\`\`



In this example:



1\. Docker starts the database container.

2\. Docker executes the database health check.

3\. The health check verifies whether PostgreSQL is ready.

4\. Docker Compose starts the backend after the database becomes healthy.



The application should still handle connection failures and retry database connections when necessary.



**### Important Docker Compose Commands**



\| Command | Description |

\|---|---|

\| \`docker compose up -d --build\` | Builds images when required and starts services in the background. |

\| \`docker compose up -d\` | Starts services in the background without explicitly forcing a build. |

\| \`docker compose build\` | Builds the images defined in the Compose file. |

\| \`docker compose ps\` | Lists the Compose containers and their status. |

\| \`docker compose logs -f\` | Displays live logs from the services. |

\| \`docker compose logs -f backend\` | Displays live logs from the backend service. |

\| \`docker compose down\` | Stops and removes the containers and Compose network. |



**\*\*Note:\*\*** \`docker compose down\` does not normally remove named volumes unless you specify \`-v\`.



\---



**## 2. Nginx**



**### What is Nginx?**



Nginx is a web server that can also work as a reverse proxy and load balancer.



It can serve frontend files and route incoming HTTP requests to the appropriate backend service based on configured rules.



For example, an application may contain:



\- Frontend: HTML, CSS, and JavaScript files.

\- Backend: Application APIs.

\- Nginx: Receives requests and routes them to the correct destination.



**### How Does Nginx Work?**



Suppose a user opens \`http\://myapp.com\`.



1\. The browser sends an HTTP request to Nginx.

2\. Nginx checks its configuration rules.

3\. If the request is for \`/\`, Nginx serves the frontend's HTML file.

4\. If the request is for \`/api/claims\`, Nginx forwards the request to the backend API.

5\. The backend processes the request and returns a response through Nginx.



Examples:



\- \`http\://myapp.com/\` → Frontend

\- \`http\://myapp.com/api/claims\` → Backend API



**\*\*Important:\*\*** Nginx does not automatically identify frontend and backend requests. We configure the routing rules explicitly.



**### Sample Nginx Configuration**



\`\`\`nginx

server {

    listen 80;



    location / {

        root /usr/share/nginx/html;

        index index.html;

        try_files $uri $uri/ /index.html;

    }



    location /api/ {

        proxy_pass http\://backend:5000;

    }

}

\`\`\`



**### Explanation of the Configuration**



\| Directive | Description |

\|---|---|

\| \`server\` | Defines a virtual server configuration. |

\| \`listen 80\` | Makes Nginx listen on port 80. |

\| \`location /\` | Handles requests for the frontend. |

\| \`root\` | Specifies the directory containing frontend files. |

\| \`index\` | Specifies the default index file. |

\| \`try_files\` | Checks for the requested file and falls back to \`index.html\` if needed. |

\| \`location /api/\` | Matches API requests starting with \`/api/\`. |

\| \`proxy_pass\` | Forwards matching requests to the backend service. |



In this example, \`backend:5000\` assumes the backend service is named \`backend\` and listens on port 5000 on the shared Docker network.



**\*\*Note:\*\*** The trailing slash in \`proxy_pass\` can affect how the request path is forwarded. Configure it according to the paths expected by the backend.



**### What is a Reverse Proxy?**



A reverse proxy receives requests from clients and forwards them to backend servers.



Benefits of Nginx include:



\- Routing requests to different services.

\- Hiding backend service details from external users.

\- Configuring HTTPS termination.

\- Distributing traffic across multiple backend instances.

\- Serving static frontend files.

\- Supporting request logging and other HTTP handling rules.



\---



**## 3. How Docker Compose and Nginx Work Together**



Consider an application containing three containers:



1\. Nginx

2\. Backend API

3\. PostgreSQL database



**### Request Flow**



\`\`\`text

Browser / Client

       |

       v

 Nginx Container

       |

       |---- Frontend requests --> Frontend files

       |

       |---- API requests -------> Backend Container

                                      |

                                      v

                                PostgreSQL Database

\`\`\`



**### Responsibilities**



**\*\*Docker Compose:\*\***

\- Defines and manages application services.

\- Builds or pulls images.

\- Creates and manages containers.

\- Configures networks and volumes.

\- Controls service startup dependencies.



**\*\*Nginx:\*\***

\- Receives HTTP requests.

\- Serves frontend files when configured to do so.

\- Routes API requests to the backend.

\- Can terminate HTTPS and load-balance backend traffic.



**\*\*Backend:\*\***

\- Processes business logic.

\- Handles API requests.

\- Communicates with the database.



**\*\*Database:\*\***

\- Stores and retrieves application data.



Docker Compose manages the containers and their network, while Nginx manages HTTP routing.



\---



**## 4. Important Interview Questions**



**### 1. Why do we use Docker Compose?**



Docker Compose allows us to define and manage multiple containers using a single YAML file instead of running separate commands for every service.



**### 2. What is the difference between an image and a container?**



\- **\*\*Image:\*\*** A template used to create containers.

\- **\*\*Container:\*\*** An instance of an image.



**### 3. How do Docker Compose services communicate?**



Services communicate over a shared Docker network, generally using their service names as DNS hostnames.



**### 4. Does \`depends_on\` guarantee that a service is ready?**



No. It controls startup order. We can use \`condition: service_healthy\` with a suitable health check to wait for a dependency to become healthy.



**### 5. What is Nginx?**



Nginx is a web server that can also act as a reverse proxy and load balancer.



**### 6. How does Nginx route frontend and backend requests?**



We configure rules using directives such as \`location\` and \`proxy_pass\`. Nginx serves frontend files or forwards API requests based on these rules.



**### 7. What is the difference between Docker Compose and Nginx?**



\- **\*\*Docker Compose:\*\*** Manages containers, networks, volumes, and service dependencies.

\- **\*\*Nginx:\*\*** Serves web content and routes HTTP requests to configured destinations.



**### 8. What happens when we execute \`docker compose up -d --build\`?**



Docker Compose builds the required images and starts the services in detached mode, meaning they run in the background.



\---



**## 5. Quick Revision**



\| Concept | Key Point |

\|---|---|

\| Docker image | Template used to create a container. |

\| Docker container | An instance of an image. |

\| Docker Compose | Defines and manages multi-container applications. |

\| Service name | Used for service discovery and communication. |

\| \`depends_on\` | Defines service startup dependencies. |

\| Health check | Checks the health of an application inside a container. |

\| Nginx | Web server, reverse proxy, and load balancer. |

\| \`location\` | Defines which requests a configuration block handles. |

\| \`proxy_pass\` | Forwards requests to a backend service. |

\| Reverse proxy | Receives client requests and forwards them to backend servers. |



**\*\*Key takeaway:\*\*** Docker Compose manages the application containers, and Nginx serves frontend content and routes incoming HTTP requests to the appropriate services.
---

## 6. Connecting GitHub Actions to Azure Using a User-Assigned Managed Identity (UAMI)

### What is the purpose?

We can connect GitHub Actions to Azure using a User-Assigned Managed Identity (UAMI) and OpenID Connect (OIDC).

This lets a GitHub Actions workflow authenticate to Azure without storing an Azure client secret in GitHub.

### Step 1: Create a UAMI in Azure

1. Open the Azure portal.
2. Create a User-Assigned Managed Identity (UAMI).
3. Note its **Client ID**, **Tenant ID**, and **Subscription ID**.
4. Assign the required Azure RBAC roles to the UAMI, such as the roles needed to deploy or manage your infrastructure.

Assign only the permissions required by the workflow. For example, use the appropriate role and scope for the resources managed by your Terraform or other IaC deployment.

### Step 2: Get the GitHub Organization and Repository IDs

You can use the GitHub API to retrieve the IDs.

**Get the GitHub user or organization ID:**

```bash
curl -s https://api.github.com/users/karthik199109-art
```

Look for the `id` field in the output. If `karthik199109-art` is a personal account rather than a GitHub organization, this returns the user ID.

**Get the repository ID:**

```bash
curl -s https://api.github.com/repos/karthik199109-art/k8spractice
```

Look for the `id` field in the output.

These commands return JSON. To print only the ID when `jq` is installed, use:

```bash
curl -s https://api.github.com/users/karthik199109-art | jq .id
curl -s https://api.github.com/repos/karthik199109-art/k8spractice | jq .id
```

### Step 3: Configure Federated Credentials on the UAMI

1. Open the UAMI in the Azure portal.
2. Open **Federated credentials** and add a credential for GitHub Actions.
3. Select the correct GitHub organization or account, repository, and deployment target, such as a branch or GitHub environment.
4. Save the federated credential.

The credential must match the GitHub Actions workflow identity. For example, if the credential is configured for the `main` branch, the workflow must run from that branch to match the configured subject.

**Important:** The GitHub organization/repository names and the selected branch or environment determine the federated identity configuration. The organization ID and repository ID returned by the commands above are useful for identification, but they are not normally entered as separate fields in Azure's standard GitHub Actions federated credential configuration.

### Step 4: Add Azure Details to GitHub

In your GitHub repository, go to **Settings → Secrets and variables → Actions**.

Add the following repository secrets:

- `AZURE_CLIENT_ID` — Client ID of the UAMI.
- `AZURE_TENANT_ID` — Tenant ID of the Azure tenant.
- `AZURE_SUBSCRIPTION_ID` — Subscription ID containing the target resources.

Use the same secret names in your workflow, or update the workflow to match the names you choose.

### Step 5: Log In to Azure from GitHub Actions

Add the `id-token: write` permission to the workflow and use the Azure Login action.

Example:

```yaml
name: Login to Azure

on:
  workflow_dispatch:

permissions:
  id-token: write
  contents: read

jobs:
  azure-login:
    runs-on: ubuntu-latest

    steps:
      - name: Log in to Azure
        uses: azure/login@v2
        with:
          client-id: ${{ secrets.AZURE_CLIENT_ID }}
          tenant-id: ${{ secrets.AZURE_TENANT_ID }}
          subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}

      - name: Check Azure account
        run: az account show
```

### How does the authentication work?

1. The workflow requests an OIDC token from GitHub Actions. The `id-token: write` permission allows it to request this token.
2. The Azure Login action uses the token to authenticate with Microsoft Entra ID.
3. Azure checks whether the token matches the federated credential configured on the UAMI.
4. If the token matches, Azure authenticates the UAMI and provides an Azure access token.
5. The workflow can access Azure resources according to the RBAC roles assigned to the UAMI.

**Important:** `id-token: write` allows GitHub Actions to request an OIDC token; it does not grant Azure resource permissions by itself. Azure access is controlled by the RBAC roles assigned to the UAMI.

### Quick Revision

- **UAMI:** The Azure identity used by the GitHub Actions workflow.
- **Federated credential:** Establishes trust between GitHub Actions and the UAMI.
- **Client ID:** Identifies the UAMI for authentication.
- **Tenant ID:** Identifies the Microsoft Entra ID tenant.
- **Subscription ID:** Identifies the Azure subscription.
- **`id-token: write`:** Allows the workflow to request a GitHub OIDC token.
- **Azure RBAC:** Controls which Azure resources and operations the identity can access.
- **`azure/login@v2`:** Authenticates the GitHub Actions workflow to Azure.
