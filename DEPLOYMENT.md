# 🚀 Deployment Guide - FinTrace AML Dashboard

## GitHub Deployment

### 1. Initialize Git Repository
```bash
# Initialize git repository
git init

# Add all files
git add .

# Make initial commit
git commit -m "Initial commit: FinTrace AML Dashboard"

# Add remote origin (replace with your GitHub repo URL)
git remote add origin https://github.com/YOUR_USERNAME/FINTRACE_REPO_NAME.git

# Push to GitHub
git push -u origin main
```

### 2. GitHub Repository Setup
1. Create a new repository on GitHub
2. Don't initialize with README, .gitignore, or license (we already have these)
3. Copy the repository URL
4. Follow the git commands above

### 3. Continuous Deployment (Optional)
Create `.github/workflows/deploy.yml` for automated deployment:

```yaml
name: Deploy to Production

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        python -c "import app; print('App imports successfully')"
    
    - name: Deploy to server
      run: |
        echo "Deployment completed successfully"
```

## Production Deployment

### 1. Server Requirements
- **OS**: Ubuntu 20.04+ or CentOS 8+
- **Python**: 3.8+
- **Memory**: Minimum 2GB RAM
- **Storage**: 10GB+ available space

### 2. Server Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install python3 python3-pip python3-venv -y

# Install system dependencies
sudo apt install nginx supervisor -y
```

### 3. Application Deployment
```bash
# Create application directory
sudo mkdir -p /var/www/fintrace
sudo chown $USER:$USER /var/www/fintrace

# Clone repository
cd /var/www/fintrace
git clone https://github.com/YOUR_USERNAME/FINTRACE_REPO_NAME.git .

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with production values
```

### 4. Environment Configuration
Create `.env` file:
```env
FLASK_ENV=production
FLASK_APP=app.py
DATABASE_URL=sqlite:///instance/transactions.db
HOST=0.0.0.0
PORT=5000
SECRET_KEY=your-secret-key-here
```

### 5. Gunicorn Configuration
Create `gunicorn.conf.py`:
```python
bind = "127.0.0.1:8000"
workers = 4
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 30
keepalive = 2
```

### 6. Supervisor Configuration
Create `/etc/supervisor/conf.d/fintrace.conf`:
```ini
[program:fintrace]
directory=/var/www/fintrace
command=/var/www/fintrace/venv/bin/gunicorn -c gunicorn.conf.py app:app
autostart=true
autorestart=true
stderr_logfile=/var/log/fintrace/fintrace.err.log
stdout_logfile=/var/log/fintrace/fintrace.out.log
user=www-data
```

### 7. Nginx Configuration
Create `/etc/nginx/sites-available/fintrace`:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /var/www/fintrace/static;
    }
}
```

### 8. Enable Services
```bash
# Create log directory
sudo mkdir -p /var/log/fintrace
sudo chown www-data:www-data /var/log/fintrace

# Enable supervisor
sudo systemctl enable supervisor
sudo systemctl start supervisor

# Reload supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start fintrace

# Enable nginx site
sudo ln -s /etc/nginx/sites-available/fintrace /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Docker Deployment

### 1. Create Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create instance directory
RUN mkdir -p instance

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "runproduction.py"]
```

### 2. Docker Compose
Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  fintrace:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./instance:/app/instance
      - ./large_sample_transactions.csv:/app/large_sample_transactions.csv
    environment:
      - FLASK_ENV=production
      - FLASK_APP=app.py
    restart: unless-stopped
```

### 3. Run with Docker
```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Environment Variables

### Development
```env
FLASK_ENV=development
FLASK_DEBUG=1
DATABASE_URL=sqlite:///instance/transactions.db
HOST=localhost
PORT=5000
```

### Production
```env
FLASK_ENV=production
FLASK_DEBUG=0
DATABASE_URL=sqlite:///instance/transactions.db
HOST=0.0.0.0
PORT=5000
SECRET_KEY=your-production-secret-key
```

## Security Considerations

### 1. Environment Variables
- Never commit `.env` files to version control
- Use strong, unique secret keys
- Rotate secrets regularly

### 2. Database Security
- Use strong database passwords
- Limit database access to application only
- Regular database backups

### 3. Network Security
- Use HTTPS in production
- Configure firewall rules
- Monitor access logs

### 4. Application Security
- Keep dependencies updated
- Regular security audits
- Input validation and sanitization

## Monitoring and Maintenance

### 1. Log Monitoring
```bash
# View application logs
sudo tail -f /var/log/fintrace/fintrace.out.log

# View error logs
sudo tail -f /var/log/fintrace/fintrace.err.log

# View nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### 2. Performance Monitoring
```bash
# Check process status
sudo supervisorctl status fintrace

# Monitor system resources
htop
df -h
free -h
```

### 3. Backup Strategy
```bash
# Database backup
cp instance/transactions.db backups/transactions_$(date +%Y%m%d_%H%M%S).db

# Application backup
tar -czf fintrace_backup_$(date +%Y%m%d_%H%M%S).tar.gz /var/www/fintrace
```

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   sudo lsof -i :5000
   sudo kill -9 <PID>
   ```

2. **Permission Denied**
   ```bash
   sudo chown -R www-data:www-data /var/www/fintrace
   sudo chmod -R 755 /var/www/fintrace
   ```

3. **Database Locked**
   ```bash
   sudo systemctl restart fintrace
   ```

4. **Nginx Configuration Error**
   ```bash
   sudo nginx -t
   sudo systemctl reload nginx
   ```

## Support

For deployment issues:
1. Check application logs
2. Verify configuration files
3. Test individual components
4. Review system resources
5. Check network connectivity

---

**🚀 FinTrace AML Dashboard** - Secure and scalable deployment guide
