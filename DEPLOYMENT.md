# Deployment Guide

This guide provides detailed instructions for deploying the Second Certainty Tax Management System to a production environment. The application is currently deployed on Render's free tier.

## Deployment Platforms

We recommend the following deployment options:

- **Render.com** (Current deployment)
- **Heroku**
- **AWS** (EC2 or ECS/EKS)
- **Digital Ocean**

This guide focuses on deployment to Render.com.

## Current Production URLs

- **Frontend**: [https://second-certainty.onrender.com](https://second-certainty.onrender.com)
- **Backend API**: [https://second-certainty-api.onrender.com](https://second-certainty-api.onrender.com)

## Prerequisites

Before deploying, ensure you have:

- A Render.com account
- Your code in a GitHub repository
- PostgreSQL database (Render provides this service)

## Backend Deployment (Render.com)

### 1. Create a PostgreSQL Database

1. Log in to your Render.com dashboard
2. Go to "New" > "PostgreSQL"
3. Configure your database:
   - Name: `second-certainty-db`
   - Database: `second_certainty`
   - User: Let Render generate this
   - Region: Choose based on your target audience
4. Click "Create Database"
5. Once created, note the connection information, especially the "Internal Database URL"

### 2. Deploy the Web Service

1. From your Render dashboard, go to "New" > "Web Service"
2. Connect your GitHub repository
3. Configure the web service:
   - Name: `second-certainty-api`
   - Environment: "Python 3"
   - Region: Same as your database
   - Branch: `main` (or your production branch)
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Select "Advanced" and add the following environment variables:

```
DATABASE_URL=<Internal Database URL from step 1>
SECRET_KEY=<your secure secret key>
ACCESS_TOKEN_EXPIRE_MINUTES=10080
SARS_WEBSITE_URL=https://www.sars.gov.za
DEBUG=False
ENVIRONMENT=production
ALLOWED_ORIGINS=https://second-certainty.onrender.com
```

4. Click "Create Web Service"

### 3. Initialize the Database

After your service is deployed, you'll need to initialize the database:

1. Go to your web service in the Render dashboard
2. Click on "Shell"
3. Run the following commands:

```bash
python init_db.py
python scripts/seed_data.py
python add_admin_field.py admin@yourdomain.com
```

## Frontend Deployment (Render.com)

### 1. Prepare the Frontend for Production

In your frontend project, ensure you have the correct API URL for production:

```javascript
// src/api/index.js
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'https://second-certainty-api.onrender.com/api';
```

### 2. Deploy the Static Site

1. From your Render dashboard, go to "New" > "Static Site"
2. Connect your GitHub repository (or the frontend repository if separate)
3. Configure the static site:
   - Name: `second-certainty`
   - Build Command: `npm install && npm run build`
   - Publish Directory: `build`
   - Environment Variables:
     - `REACT_APP_API_BASE_URL=https://second-certainty-api.onrender.com/api`
4. Click "Create Static Site"

## Custom Domain Setup (Optional)

If you have a custom domain:

### Backend

1. Go to your web service in the Render dashboard
2. Click on "Settings" > "Custom Domain"
3. Follow the instructions to add your domain (e.g., `api.yourdomain.com`)

### Frontend

1. Go to your static site in the Render dashboard
2. Click on "Settings" > "Custom Domain"
3. Follow the instructions to add your domain (e.g., `app.yourdomain.com` or just `yourdomain.com`)

## SSL Certificates

Render automatically provisions SSL certificates for all web services and static sites, including for custom domains.

## Monitoring and Logging

### Render Dashboard

Render provides basic monitoring and logging capabilities:

1. Go to your web service in the Render dashboard
2. Click on "Logs" to view application logs
3. You can filter logs by type and download them for analysis

### Additional Monitoring (Recommended)

For production deployments, consider adding:

- **Application Monitoring**: New Relic, Datadog, or Sentry
- **Structured Logging**: Configure the application's logging system to output JSON logs

## Production Considerations

### Security

1. Ensure your `SECRET_KEY` is strong and kept confidential
2. Set appropriate CORS headers in `ALLOWED_ORIGINS`
3. Consider implementing rate limiting for the API
4. Set up regular security scans for vulnerabilities

### Performance

1. Enable caching for appropriate endpoints
2. Consider using a CDN for the frontend (Render static sites include global CDN)
3. Optimize database queries for performance

### Backup

1. Set up regular database backups
2. Implement a disaster recovery plan

## Continuous Deployment

For continuous deployment with GitHub:

1. Go to your service in the Render dashboard
2. Under "Settings" > "Build & Deploy", ensure "Auto-Deploy" is enabled
3. Each push to your main branch will trigger a new deployment

## Upgrading to Paid Tier

As your application grows, consider upgrading to Render's paid tiers for:

- Improved performance
- No spin-down time for web services
- More resources (CPU, RAM)
- Additional features like background workers

## Troubleshooting Deployment Issues

### Backend Issues

- **Database Connection Errors**: Verify the `DATABASE_URL` environment variable
- **Build Failures**: Check the build logs for dependency issues
- **Runtime Errors**: Examine the application logs for exceptions

### Frontend Issues

- **Build Failures**: Check for JavaScript or dependency errors in build logs
- **API Connection Issues**: Ensure the API URL is correctly configured
- **Styling Issues**: Verify CSS/Tailwind builds correctly

### Database Issues

- **Migration Failures**: Run migrations manually via the shell
- **Data Inconsistencies**: Consider resetting and reseeding the database

## Support and Resources

- [Render Documentation](https://render.com/docs)
- [FastAPI Deployment Guide](https://fastapi.tiangolo.com/deployment/)
- [Create React App Deployment](https://create-react-app.dev/docs/deployment/)