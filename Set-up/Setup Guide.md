<h1 align="center">Setup Guide</h1>

<h2 align="center"> Local Development</h2>

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

# Test in Docker as well
---

<h2 align="center">☁️ Azure Deployment</h2>

### Deployment Steps

#### 1. Create Azure VM with Custom Script

During VM creation, add Custom Script Extension:

```
Script Location: https://raw.githubusercontent.com/jacobbria/resume_webapp_AZ/main/setup.sh
```

#### 2. Verify Deployment

- Get Public IP from Azure Portal
- Browse to `http://<your-public-ip>`

---

<h2 align="center">🔧 Configuration</h2>

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

- Caching policies
- Rate limiting
