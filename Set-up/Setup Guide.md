# Setup Guide

## 🖥️ Local Development

### 1. Clone and Setup

```bash
git clone https://github.com/jacobbria/resume_webapp_AZ.git
cd resume_webapp_AZ

python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file with the following variables:

```env
SECRET_KEY=your-secret-key
GEMINI_API_KEY=your-gemini-api-key
ENTRA_CLIENT_ID=your-entra-client-id
EntraClientSecret=your-entra-client-secret
ENTRA_REDIRECT_URI=http://localhost:8000/auth/callback
```

### 3. Run Locally

```bash
# Development (Flask dev server)
python app.py

# Production-like (Gunicorn)
gunicorn -w 4 -b 0.0.0.0:8000 wsgi:app
```

Open http://localhost:8000 in your browser.

---

## ☁️ Azure Deployment

### Prerequisites

- Azure Subscription (Standard)
- Ubuntu 24.04 LTS VM (B1s size minimum)
- Azure Standard Load Balancer (public)
- NSG inbound rule: Allow TCP 80 from Internet

### Deployment Steps

#### 1. Create Azure VM with Custom Script

During VM creation, add Custom Script Extension:

```
Script Location: https://raw.githubusercontent.com/jacobbria/resume_webapp_AZ/main/setup.sh
```

#### 2. Manual Setup (if not using Custom Script Extension)

SSH into VM and run:

```bash
curl -fsSL https://raw.githubusercontent.com/jacobbria/resume_webapp_AZ/main/setup.sh | bash
```

#### 3. Verify Deployment

- Get Public IP from Azure Portal
- Browse to `http://<your-public-ip>`

---

## 🔧 Configuration

### Environment Variables

Edit `.env` or set in `/etc/supervisor/conf.d/resume_webapp.conf`:

```env
FLASK_ENV=production      # Set to 'development' for debugging
FLASK_DEBUG=0             # Never enable in production
SECRET_KEY=change-me      # MUST change in production
```

### Gunicorn Workers

Adjust in `setup.sh` (line for gunicorn command):

```bash
# For B1s (1 vCPU): 2-4 workers
gunicorn -w 4 -b 127.0.0.1:8000 wsgi:app

# For B2s (2 vCPU): 4-8 workers
gunicorn -w 8 -b 127.0.0.1:8000 wsgi:app
```

### Nginx Tuning

Edit `/etc/nginx/sites-available/resume_webapp` for:

- SSL/TLS configuration
- Caching policies
- Rate limiting
