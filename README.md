# AskMimis.dev - AI Analysis Web App

A lightweight, cost effective Flask web application for analysing job postings. Deployed on Azure container, Nginx reverse proxy, Gunicorn app server, and SQLite Database ([see stack](#-tech-stack)).

## 📁 Directory

- [Management](Management/) - App usage instructions and configuration guides
- [Documentation](Documentation/) - Project documentation
- [Set-up](Set-up/) - Setup resources

## 🎯 Features

- **Home Page**: Greeting with "Use Demo Data" button
- **Demo Dashboard**: Browse 6 trending job postings
- **Job Details**: View complete job information
- **Light/Modern UI**: Responsive design with gradient theme
- **Health Check**: Support for Azure Load Balancer health probes
- **Production Ready**: Uses Gunicorn + Supervisor + Nginx

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

## 📦 Tech Stack

- **Framework**: Flask 3.0.0
- **Server**: Gunicorn 21.2.0 (4 workers)
- **Reverse Proxy**: Nginx
- **Database**: SQLite (demo data)
- **Python**: 3.11+
- **OS**: Ubuntu 24.04 LTS

## 🚀 Local Development

### 1. Clone and Setup

```bash
git clone https://github.com/jacobbria/resume_webapp_AZ.git
cd resume_webapp_AZ

python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Environment Configuration

```bash
cp .env.example .env
# Edit .env with your settings (or use defaults for local dev)
```

### 3. Run Locally

```bash
# Development (Flask dev server)
python app.py

# Production-like (Gunicorn)
gunicorn -w 4 -b 0.0.0.0:8000 wsgi:app
```

Open http://localhost:8000 in your browser.

## 📋 Routes

| Route | Method | Description |
|-------|--------|-------------|
| `/` | GET | Home page with greeting |
| `/demo` | GET | Display all demo jobs |
| `/job/<id>` | GET | View job details |
| `/health` | GET | Health check (Azure LB probe) |

## 🗄️ Database

The app uses SQLite with a pre-populated demo dataset:

**Demo Jobs Included:**
- Senior Python Developer (TechCorp Inc.)
- Full Stack Web Developer (WebSolutions LLC)
- Data Scientist (DataDriven AI)
- DevOps Engineer (CloudMasters)
- Frontend Developer (DesignStudio Pro)
- Software Architect (Enterprise Solutions)

Database initializes automatically on first run.

## ☁️ Azure Deployment

### Prerequisites

- Azure Subscription (Standard)
- Ubuntu 24.04 LTS VM (B1s size minimum)
- Azure Standard Load Balancer (public)
- NSG inbound rule: Allow TCP 80 from Internet

### Deployment Steps

1. **Create Azure VM with Custom Script**

   During VM creation, add Custom Script Extension:
   ```
   Script Location: https://raw.githubusercontent.com/jacobbria/resume_webapp_AZ/main/setup.sh
   ```

2. **Manual Setup (if not using Custom Script Extension)**

   SSH into VM and run:
   ```bash
   curl -fsSL https://raw.githubusercontent.com/jacobbria/resume_webapp_AZ/main/setup.sh | bash
   ```

3. **Verify Deployment**

   ```bash
   # Check services
   systemctl status nginx
   supervisorctl status resume_webapp
   
   # Check logs
   tail -f /var/log/resume_webapp.log
   
   # Test health probe
   curl http://localhost:8000/health
   ```

4. **Access Application**

   - Get Public IP from Azure Portal
   - Browse to `http://<your-public-ip>`

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

## 📊 Monitoring

### Log Files

```bash
# Nginx
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# Flask/Gunicorn
tail -f /var/log/resume_webapp.log

# System Supervisor
supervisorctl status
```

### Azure Monitor

Configure in Azure Portal:
1. Go to your VM
2. Add diagnostics extension
3. Monitor: CPU, Memory, Disk, Network

### Health Check

The `/health` endpoint returns `200 OK` and is used by Azure Load Balancer:

```bash
curl -I http://localhost:8000/health
# HTTP/1.1 200 OK
```

## 🔐 Security Considerations

For production deployment:

1. **SSL/TLS**: Add certificate to Nginx (Let's Encrypt recommended)
   ```bash
   apt-get install certbot python3-certbot-nginx
   certbot --nginx -d yourdomain.com
   ```

2. **Firewall**: Azure NSG should only allow ports 80/443
3. **App Updates**: Periodically pull latest code from GitHub
4. **Secret Management**: Use Azure Key Vault for sensitive data
5. **Database**: Regular backups of `data/jobs.db`

## 📧 Troubleshooting

### App won't start
```bash
# Check Supervisor logs
supervisorctl status resume_webapp
supervisorctl tail resume_webapp -f

# Check app manually
cd /opt/resume_webapp
source venv/bin/activate
python -c "import app; print('OK')"
```

### Nginx not proxying correctly
```bash
# Test Nginx config
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx

# Check proxy logs
tail -f /var/log/nginx/error.log
```

### Port 8000 already in use
```bash
# Find process using port
lsof -i :8000
# Kill process
kill -9 <PID>
```

## 🤝 Contributing

Not an open source project - I appreciate all help, comments, or tips though!

## 📄 License

MIT License - See LICENSE file

## 📞 Support

For issues or questions:
- GitHub Issues: https://github.com/jacobbria/resume_webapp_AZ/issues
- Email: [your-email@domain.com]

---

**Last Updated**: February 2025
**Status**: Production Ready ✅
