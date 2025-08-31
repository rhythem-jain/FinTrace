# FinTrace Deployment Guide for Render

This guide will help you deploy your FinTrace application on Render, a cloud platform that offers free hosting for web applications.

## Prerequisites

- A GitHub account with your FinTrace project repository
- A Render account (free tier available)

## Step 1: Prepare Your Repository

Your repository should now contain the following files for Render deployment:

- `app.py` - Main Flask application
- `requirements.txt` - Python dependencies
- `render.yaml` - Render service configuration
- `wsgi.py` - WSGI entry point
- `env.local` - Local environment template

## Step 2: Deploy on Render

### Option A: Using render.yaml (Recommended)

1. **Connect your GitHub repository to Render:**
   - Go to [render.com](https://render.com) and sign up/login
   - Click "New +" and select "Blueprint"
   - Connect your GitHub account and select the FinTrace repository
   - Render will automatically detect the `render.yaml` file

2. **Deploy the service:**
   - Click "Apply" to deploy your service
   - Render will automatically:
     - Install Python 3.9.16
     - Install dependencies from `requirements.txt`
     - Start the service using gunicorn
     - Generate a secure SECRET_KEY
     - Set production environment variables

### Option B: Manual Service Creation

1. **Create a new Web Service:**
   - Go to [render.com](https://render.com) and sign up/login
   - Click "New +" and select "Web Service"
   - Connect your GitHub repository

2. **Configure the service:**
   - **Name:** `fintrace` (or your preferred name)
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Plan:** Free

3. **Set Environment Variables:**
   - `FLASK_ENV`: `production`
   - `FLASK_DEBUG`: `0`
   - `SECRET_KEY`: Leave empty (Render will generate one)
   - `DATABASE_URL`: `sqlite:///instance/transactions.db`

## Step 3: Verify Deployment

1. **Check Build Status:**
   - Monitor the build logs in Render dashboard
   - Ensure all dependencies are installed successfully

2. **Test the Application:**
   - Visit your Render URL (e.g., `https://fintrace.onrender.com`)
   - Test the main functionality:
     - Welcome page loads
     - Dashboard is accessible
     - File upload works
     - API endpoints respond

3. **Check Health Status:**
   - Render will automatically monitor your service
   - Health checks run every 30 seconds on the `/` endpoint

## Step 4: Post-Deployment

### Database Initialization
The SQLite database will be automatically created in the `instance/` directory when the app first runs.

### File Uploads
Uploaded files are stored in the `instance/` directory. Note that on Render's free tier, this storage is ephemeral and files may be lost when the service restarts.

### Performance Considerations
- Render's free tier has limitations on CPU and memory
- Large file uploads may timeout
- Consider implementing file size limits for production use

## Troubleshooting

### Common Issues

1. **Build Failures:**
   - Check that all dependencies in `requirements.txt` are compatible
   - Ensure Python version compatibility (3.9.16)

2. **Runtime Errors:**
   - Check Render logs for error details
   - Verify environment variables are set correctly

3. **Database Issues:**
   - Ensure the `instance/` directory is writable
   - Check database file permissions

### Logs and Debugging

- **Build Logs:** Available in the Render dashboard during deployment
- **Runtime Logs:** Accessible via the "Logs" tab in your service dashboard
- **Environment Variables:** Check the "Environment" tab for current values

## Security Considerations

1. **Secret Key:** Render automatically generates a secure SECRET_KEY
2. **Environment Variables:** Sensitive data should be stored as environment variables
3. **File Uploads:** Implement proper validation and sanitization
4. **Database:** Consider using a managed database service for production

## Scaling and Upgrades

- **Free Tier:** Suitable for development and testing
- **Paid Plans:** Available for production workloads with better performance
- **Custom Domains:** Can be configured on paid plans
- **SSL Certificates:** Automatically provided by Render

## Support

- **Render Documentation:** [docs.render.com](https://docs.render.com)
- **Community Support:** [Render Community](https://community.render.com)
- **GitHub Issues:** For application-specific problems

## Next Steps

After successful deployment:

1. **Monitor Performance:** Use Render's built-in monitoring tools
2. **Set Up Alerts:** Configure notifications for service issues
3. **Backup Strategy:** Implement regular backups for your data
4. **CI/CD Pipeline:** Consider setting up automatic deployments from your main branch

Your FinTrace application should now be successfully deployed and accessible via your Render URL!
