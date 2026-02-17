# Use a slim Python image
FROM python:3.11-slim

# Install Nginx and Supervisor
RUN apt-get update && apt-get install -y nginx supervisor && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY . .

# Copy Nginx config 
COPY nginx.conf /etc/nginx/sites-available/default

# Copy Supervisor config 
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Expose Port 80 for traffic
EXPOSE 80

# Start Supervisor to manage Gunicorn and Nginx
CMD ["/usr/bin/supervisord"]
