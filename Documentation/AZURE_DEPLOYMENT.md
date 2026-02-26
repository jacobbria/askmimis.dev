# Azure Deployment Guide for Resume Webapp

## Step-by-Step Deployment

### 1. Prerequisites Checklist
- [ ] Azure Subscription (Standard tier)
- [ ] Virtual Network with public subnet
- [ ] Azure Standard Load Balancer (public endpoint on port 80)
- [ ] Ubuntu 24.04 LTS VM (B1s minimum)
- [ ] NSG inbound rule: Allow TCP 80 from 0.0.0.0/0
- [ ] GitHub account with repository cloned

### 2. Push Code to GitHub

```bash
# In your local machine
cd c:\Users\mrjac\OneDrive\Desktop\Apps\resume_webapp_AZ

# Initialize git (if not already done)
git init
git remote add origin https://github.com/YOUR_USERNAME/resume_webapp_AZ.git

# Make all script files executable (Windows Git Bash)
git add .
git commit -m "Initial commit: Flask webapp for Azure deployment"
git push -u origin main
```

### 3. Create Azure VM with Automated Setup

**Option A: Azure Portal**

1. Azure Portal → Virtual Machines → Create
2. Basics:
   - Resource Group: `resume-app-rg`
   - VM name: `resume-webapp-vm`
   - Region: `East US` (or your preference)
   - Image: `Ubuntu 24.04 LTS`
   - Size: `B1s` (minimum for free tier)
   - Username: `azureuser`

3. Networking:
   - Virtual Network: Select your existing VNet
   - Subnet: Select public subnet
   - Public IP: Create new
   - NSG: Create new with inbound port 80 allowed

4. Management → Advanced:
   - Custom data script:
   ```bash
   #!/bin/bash
   curl -fsSL https://raw.githubusercontent.com/YOUR_USERNAME/resume_webapp_AZ/main/setup.sh | bash
   ```

5. Create VM and wait ~2-3 minutes for setup

**Option B: Azure CLI**

```bash
# Set variables
RESOURCE_GROUP="resume-app-rg"
VM_NAME="resume-webapp-vm"
IMAGE="UbuntuLTS"
SIZE="Standard_B1s"
LOCATION="eastus"

# Create resource group
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create VM with custom script
az vm create \
  --resource-group $RESOURCE_GROUP \
  --name $VM_NAME \
  --image $IMAGE \
  --size $SIZE \
  --admin-username azureuser \
  --generate-ssh-keys \
  --public-ip-sku Standard \
  --custom-data setup.sh

# Get public IP
az vm show -d --resource-group $RESOURCE_GROUP --name $VM_NAME \
  --query publicIps -o tsv
```

### 4. Configure Load Balancer

**In Azure Portal:**

1. Go to Load Balancer (public)
2. Backend pools → Add VM to pool
3. Health probes:
   - Protocol: HTTP
   - Port: 80
   - Path: `/health`
   - Interval: 5 seconds
4. Load balancing rules:
   - Frontend: Port 80
   - Backend: Port 80
   - Health probe: (created above)

### 5. Verify Deployment

Once VM is running:

```bash
# Get VM public IP
PUBLIC_IP=$(az vm show -d --resource-group resume-app-rg \
  --name resume-webapp-vm --query publicIps -o tsv)

# SSH into VM
ssh azureuser@$PUBLIC_IP

# Check services
systemctl status nginx
supervisorctl status resume_webapp

# View logs
tail -30 /var/log/resume_webapp.log

# Test health endpoint
curl http://localhost:8000/health
```

### 6. Access Application

Open browser to `http://<PUBLIC_IP>` or `http://<PUBLIC_IP>:80`

You should see:
- Greeting page with "Use Demo Data" button
- 6 demo job postings when clicking button
- Clickable job cards with detailed views

### 7. Support Nginx HTTPS (Optional but Recommended)

```bash
# SSH into VM
ssh azureuser@$PUBLIC_IP

# Install Certbot
sudo apt-get update
sudo apt-get install -y certbot python3-certbot-nginx

# Get certificate (requires domain name)
sudo certbot --nginx -d your-domain.com

# Certbot auto-renews certificates
```

## Troubleshooting Deployments

### Setup Script Didn't Run

Check custom data logs:
```bash
# SSH into VM
sudo cat /var/log/cloud-init-output.log | tail -50
```

### Services Not Running

```bash
# Restart all services
sudo systemctl restart nginx
sudo supervisorctl restart resume_webapp

# Check supervisor status
sudo supervisorctl status
```

### Port 80 Access Denied

Verify NSG inbound rule:
1. Azure Portal → Network Security Groups
2. Inbound rules → Check port 80 allowed from 0.0.0.0/0
3. If not, create rule:
   - Priority: 100
   - Source: Any
   - Port: 80
   - Action: Allow

### High CPU/Memory Usage

Check Gunicorn worker count in `setup.sh`:
```bash
# For B1s (1 vCPU): reduce to 2 workers
gunicorn -w 2 -b 127.0.0.1:8000 wsgi:app

# Update on running VM
sudo nano /etc/supervisor/conf.d/resume_webapp.conf
# Change command line, then:
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl restart resume_webapp
```

## Scaling Considerations

### For B2s VM (2 vCPU):
- Increase workers: `gunicorn -w 8`
- Handle ~100 concurrent users

### For B4ms VM (4 vCPU):
- Increase workers: `gunicorn -w 16`
- Handle ~500 concurrent users

### Database Scaling:
If demo data grows beyond SQLite limits:
1. Migrate to Azure SQL Database
2. Update connection string in `db.py`
3. Redeploy via GitHub webhook

## Environment Variables for Production

SSH into VM and update:
```bash
# Edit supervisor config
sudo nano /etc/supervisor/conf.d/resume_webapp.conf

# Add environment section:
environment=
    FLASK_ENV=production,
    SECRET_KEY=YOUR_SECURE_KEY_HERE,
    FLASK_DEBUG=0

# Restart
sudo supervisorctl restart resume_webapp
```

## Monitoring & Logging

### Enable Azure Monitor:
1. Azure Portal → VM → Insights
2. Enable Application Insights
3. Set up alerts for:
   - CPU > 80%
   - Memory > 90%
   - Failed requests > 5%

### Local Logs:
```bash
# Real-time app logs
sudo tail -f /var/log/resume_webapp.log

# Nginx access
sudo tail -f /var/log/nginx/access.log

# Nginx errors
sudo tail -f /var/log/nginx/error.log
```

## Cost Optimization

- **B1s VM**: ~$8-10/month (always-on)
- **Standard Load Balancer**: ~$16/month
- **Data transfer**: First 1GB free, then ~$0.12/GB

Total estimated: **~$25-30/month**

To reduce costs:
1. Use Azure DevOps for CI/CD (free tier)
2. Use Spot VMs for dev/test (up to 70% savings)
3. Schedule VM shutdowns if not 24/7 needed

## Next Steps

1. ✅ Create GitHub repo
2. ✅ Deploy to Azure VM
3. ✅ Verify health checks
4. ⏭️ Add custom domain with DNS
5. ⏭️ Enable HTTPS with Let's Encrypt
6. ⏭️ Monitor with Azure Monitor
7. ⏭️ Set up CI/CD pipeline for auto-deployment
