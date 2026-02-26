# Project Overview

## Logical Architecture

<img width="1263" height="2809" alt="Resume-WebApp-Diagram" src="https://github.com/user-attachments/assets/df8eab72-1b8e-4338-a7ef-460554fcc65b" />


## Key Features

- **Health Check**: Support for Azure Load Balancer health probes
- **Production Ready**: Uses Gunicorn + Supervisor + Nginx

---

## 🏗️ Architecture

```
Azure VM (Ubuntu 24.04 LTS, B1s)
           ↓
Nginx (Port 80) → Reverse Proxy
           ↓
Gunicorn (Port 8000) → Flask App
           ↓
   SQLite Database (Demo Data)
```

---

## 📦 Tech Stack

| Component | Technology |
|-----------|------------|
| **Framework** | Flask 3.0.0 |
| **Server** | Gunicorn 21.2.0 (4 workers) |
| **Reverse Proxy** | Nginx |
| **Database** | SQLite |
| **Python** | 3.11+ |
| **OS** | Ubuntu 24.04 LTS |
