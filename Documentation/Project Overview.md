<h1 align="center">Project Overview</h1>

## Logical Architecture

<img width="1263" height="3096" alt="Resume-WebApp-Diagram (1)" src="https://github.com/user-attachments/assets/47eb4ff0-2d60-470b-93f4-d879978c0069" />


<h3 align="center"><u>CI/CD Pipeline</u></h3>


<p align="center">

```mermaid
flowchart TB
    A[IDE: git push] --> B[PR Review & Approval]
    B --> C[Merge to main]
    C --> D[GitHub Actions Trigger]
    D --> E[Build Docker Image]
    E --> F[Push to ACR :latest]
    F --> G[ACR Webhook]
    G --> H[Azure App Service Pulls :latest]
```

</p>

---

<h2 align="center">🏗️ Architecture</h2>

<p align="center">

```mermaid
flowchart TB
    A[Azure VM<br/>Ubuntu 24.04 LTS, B1s] --> B[Nginx<br/>Port 80]
    B --> C[Gunicorn<br/>Port 8000]
    C --> D[Flask App]
    D --> E[SQLite Database]
```

</p>

<div align="center">

| Component | Description |
|-----------|-------------|
| **Azure VM** | Cloud infrastructure running Ubuntu 24.04 LTS on B1s tier |
| **Nginx** | Reverse proxy handling incoming HTTP traffic on port 80 |
| **Gunicorn** | WSGI server with 4 workers processing requests on port 8000 |
| **Flask App** | Python web application handling routes and business logic |
| **SQLite** | Lightweight database storing job posting data |

</div>

---

<h2 align="center">📦 Tech Stack</h2>

<div align="center">

| Component | Technology |
|-----------|------------|
| **Framework** | Flask 3.0.0 |
| **Server** | Gunicorn 21.2.0 (4 workers) |
| **Reverse Proxy** | Nginx |
| **Database** | SQLite |
| **Python** | 3.11+ |
| **OS** | Ubuntu 24.04 LTS |

</div>
