# Deployment Guide

This guide provides detailed instructions for deploying the Second Certainty Tax Management System to a production environment. The application is currently deployed on Render's free tier.

## Current Production Deployment

- **Frontend**: [https://second-certainty.onrender.com](https://second-certainty.onrender.com)
- **Backend API**: [https://second-certainty-api.onrender.com](https://second-certainty-api.onrender.com)
- **API Documentation**: [https://second-certainty-api.onrender.com/api/docs](https://second-certainty-api.onrender.com/api/docs)

> **Note**: The application is deployed on Render's free tier, which results in:
> - Services "spin down" after 15 minutes of inactivity
> - Cold start delays of 30+ seconds when accessing after inactivity
> - Limited compute resources

## Deployment Platforms

Recommended deployment options in order of preference:

1. **Render.com** (Current deployment) - Easy setup, good free tier
2. **Railway** - Modern platform with excellent developer experience
3. **Heroku** - Established platform with extensive add-ons
4. **Fly.io** - Fast global deployment with Docker support
5. **AWS** (EC2/ECS/EKS) - Full control but more complex setup
6. **Digital Ocean** - Good balance of features and pricing

This guide focuses on deployment to Render.com.

## Prerequisites

Before deploying, ensure you have:

- A Render.com account
- Your code in a GitHub repository
- Separate repositories for backend and frontend (recommended)

## Backend Deployment (Render.com)

### 1. Create a PostgreSQL Database

1. Log in to your Render dashboard
2. Click "New" → "PostgreSQL"
3. Configure your database:
   - **Name**: `second-certainty-db`
   - **Database**: `second_certainty`
   - **User**: Let Render generate this
   - **Region**: Choose based on your target audience (e.g., Oregon for global)
   - **PostgreSQL Version**: Latest stable (15+)
   - **Plan**: Free (with limitations) or Starter ($7/month)
4. Click "Create Database"
5. Once created, note the connection information:
   - **Internal Database URL** (for backend service)
   - **External Database URL** (for external connections)

### 2. Deploy the Backend Web Service

1. From your Render dashboard, click "New" → "Web Service"
2. Connect your GitHub repository containing the backend code
3. Configure the web service:

**Basic Settings:**
- **Name**: `second-certainty-api`
- **Environment**: `Python 3`
- **Region**: Same as your database
- **Branch**: `main` (or your production branch)
- **Root Directory**: Leave blank (unless backend is in subdirectory)

**Build & Deploy:**
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

**Advanced Settings - Environment Variables:**

```bash
# Database
DATABASE_URL=<Internal Database URL from PostgreSQL service>

# Security
SECRET_KEY=<generate a secure 64-character secret key>
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Application
APP_NAME=Second Certainty
APP_VERSION=1.0.0
API_PREFIX=/api
DEBUG=False
ENVIRONMENT=production

# SARS Configuration
SARS_WEBSITE_URL=https://www.sars.gov.za

# CORS - Update with your frontend URL
CORS_ORIGINS=https://second-certainty.onrender.com

# Logging
LOG_LEVEL=INFO
ENABLE_QUERY_LOGGING=False

# File Upload
MAX_FILE_SIZE=10485760
UPLOAD_DIR=uploads
ALLOWED_FILE_TYPES=.pdf,.jpg,.jpeg,.png

# Rate Limiting
ENABLE_RATE_LIMITING=True
DEFAULT_RATE_LIMIT=100
AUTH_RATE_LIMIT=5

# Scraping
SCRAPING_TIMEOUT=30
SCRAPING_RETRIES=3
```

4. Click "Create Web Service"

### 3. Initialize the Database

After your service is deployed successfully:

1. Go to your web service in the Render dashboard
2. Click on "Shell" tab
3. Run the following commands one by one:

```bash
# Initialize database schema
python init_db.py

# Seed with initial data
python scripts/seed_data.py

# Create an admin user (replace with your details)
python create_admin.py admin@yourdomain.com secure_password Admin User
```

### 4. Verify Backend Deployment

Test your backend deployment:

```bash
# Health check
curl https://second-certainty-api.onrender.com/api/health

# API documentation
open https://second-certainty-api.onrender.com/api/docs
```

## Frontend Deployment (Render.com)

### 1. Prepare Frontend for Production

Ensure your frontend repository has the correct API URL configuration:

**In your React app (src/config/api.js or similar):**
```javascript
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 
  'https://second-certainty-api.onrender.com/api';

export default API_BASE_URL;
```

**Package.json build script:**
```json
{
  "scripts": {
    "build": "react-scripts build",
    "start": "react-scripts start"
  }
}
```

### 2. Deploy the Frontend Static Site

1. From your Render dashboard, click "New" → "Static Site"
2. Connect your GitHub repository containing the frontend code
3. Configure the static site:

**Basic Settings:**
- **Name**: `second-certainty`
- **Root Directory**: Leave blank (unless frontend is in subdirectory)
- **Branch**: `main`

**Build Settings:**
- **Build Command**: `npm install && npm run build`
- **Publish Directory**: `build`

**Environment Variables:**
```bash
REACT_APP_API_BASE_URL=https://second-certainty-api.onrender.com/api
NODE_VERSION=18
```

4. Click "Create Static Site"

### 3. Configure Custom Headers (Optional)

In your frontend repository, create a `public/_headers` file for security headers:

```
/*
  X-Frame-Options: DENY
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  X-XSS-Protection: 1; mode=block
  Permissions-Policy: camera=(), microphone=(), geolocation=()

/static/*
  Cache-Control: public, max-age=31536000, immutable
```

## Custom Domain Setup (Optional)

### Backend Custom Domain

1. Go to your web service settings in Render
2. Click "Custom Domains"
3. Add your domain (e.g., `api.yourdomain.com`)
4. Configure DNS records as instructed by Render
5. Update CORS settings to include your custom domain

### Frontend Custom Domain

1. Go to your static site settings in Render
2. Click "Custom Domains"
3. Add your domain (e.g., `app.yourdomain.com` or `yourdomain.com`)
4. Configure DNS records as instructed by Render
5. Update frontend API configuration if needed

## SSL Certificates

Render automatically provisions and renews Let's Encrypt SSL certificates for:
- All `.onrender.com` subdomains
- Custom domains (after verification)

No additional configuration required.

## Environment-Specific Configuration

### Production Environment Variables

Ensure these are properly set in production:

```bash
# Critical Production Settings
DEBUG=False
ENVIRONMENT=production
SECRET_KEY=<64-character secure random string>

# Database
DATABASE_URL=<production PostgreSQL URL>

# Security
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Performance
ENABLE_QUERY_LOGGING=False
LOG_LEVEL=INFO
```

### Staging Environment

For a staging environment, create separate services with:

```bash
# Staging Configuration
ENVIRONMENT=staging
DEBUG=False
CORS_ORIGINS=https://staging.yourdomain.com
DATABASE_URL=<staging database URL>
```

## Monitoring and Observability

### Render Built-in Monitoring

Render provides:
- Real-time logs accessible via dashboard
- Service metrics (CPU, memory, requests)
- Health check monitoring
- Automatic deploys on git push

### Application Monitoring

For enhanced monitoring, consider integrating:

**Sentry (Error Tracking):**
```bash
pip install sentry-sdk[fastapi]
```

Add to your FastAPI app:
```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn="YOUR_SENTRY_DSN",
    integrations=[FastApiIntegration(auto_enable=False)],
    environment="production"
)
```

**Log Management:**
- **Render Logs**: Built-in log aggregation
- **LogTail**: Simple log management
- **DataDog**: Comprehensive monitoring (paid)

### Health Checks

Render automatically monitors your service health via:
- HTTP health checks on your configured port
- Process monitoring
- Automatic restarts on failures

Configure a custom health check endpoint:
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }
```

## Performance Optimization

### Backend Optimization

1. **Database Connection Pooling:**
```python
# In app/core/config.py
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_pre_ping=True
)
```

2. **Caching (Future Enhancement):**
```bash
# Add Redis for caching
pip install redis
```

3. **Request Optimization:**
- Implement database query optimization
- Use database indexes appropriately
- Consider API response caching

### Frontend Optimization

1. **Build Optimization:**
```bash
# Enable production build optimizations
npm run build
```

2. **Static Asset Caching:**
Render automatically handles static asset caching with appropriate headers.

3. **Bundle Analysis:**
```bash
npm install --save-dev webpack-bundle-analyzer
npm run build -- --analyze
```

## Backup and Disaster Recovery

### Database Backups

**Render PostgreSQL:**
- Free tier: No automatic backups
- Paid plans: Daily automated backups with point-in-time recovery

**Manual Backup:**
```bash
# Create backup
pg_dump $DATABASE_URL > backup.sql

# Restore backup
psql $DATABASE_URL < backup.sql
```

### Application Backup

1. **Code Backup:** Maintained in Git repositories
2. **Configuration Backup:** Environment variables documented
3. **Data Migration Scripts:** Maintain up-to-date migration scripts

### Disaster Recovery Plan

1. **Service Outage:**
   - Monitor service status via Render dashboard
   - Check service logs for errors
   - Restart services if necessary

2. **Database Failure:**
   - Restore from most recent backup
   - Run database migrations if needed
   - Verify data integrity

3. **Complete Rebuild:**
   - Redeploy from Git repository
   - Restore database from backup
   - Update DNS if using custom domains

## Security Best Practices

### Environment Security

1. **Secret Management:**
   - Use Render's environment variable encryption
   - Rotate secrets regularly
   - Never commit secrets to Git

2. **HTTPS Enforcement:**
   - Render enforces HTTPS by default
   - Configure HSTS headers for additional security

3. **CORS Configuration:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

### Database Security

1. **Connection Security:**
   - Use SSL connections (Render enforces this)
   - Limit database access to application services only

2. **Access Control:**
   - Use dedicated database users with minimal privileges
   - Implement application-level authorization

## Troubleshooting Deployment Issues

### Common Backend Issues

**Build Failures:**
```bash
# Check build logs in Render dashboard
# Common issues:
# - Missing dependencies in requirements.txt
# - Python version conflicts
# - Environment variable issues
```

**Runtime Errors:**
```bash
# Check service logs for:
# - Database connection errors
# - Missing environment variables
# - Import errors
# - Port binding issues
```

**Database Connection Issues:**
```bash
# Verify DATABASE_URL format
# Check database service status
# Ensure database and web service are in same region
```

### Common Frontend Issues

**Build Failures:**
```bash
# Check build logs for:
# - npm install errors
# - Build script failures
# - Environment variable issues
```

**API Connection Issues:**
```bash
# Verify REACT_APP_API_BASE_URL is correct
# Check CORS configuration
# Ensure backend service is running
```

### Performance Issues

**Slow Response Times:**
```bash
# Check service metrics in Render dashboard
# Consider upgrading to paid plan for better performance
# Optimize database queries
# Implement caching strategies
```

**Service Downtime:**
```bash
# Monitor service health checks
# Check for resource limitations
# Review error logs for issues
```

## Upgrading and Maintenance

### Service Upgrades

**Upgrading to Paid Plans:**
- Better performance and reliability
- Automatic backups (database)
- Priority support
- No service sleep on inactivity

**Resource Scaling:**
- Monitor service metrics
- Upgrade when consistently hitting resource limits
- Consider horizontal scaling for high traffic

### Regular Maintenance

1. **Dependencies:**
```bash
# Regularly update Python packages
pip list --outdated
pip install --upgrade package_name

# Update Node.js packages
npm outdated
npm update
```

2. **Security Updates:**
- Monitor security advisories
- Apply critical security patches promptly
- Regular dependency audits

3. **Database Maintenance:**
- Monitor database performance
- Clean up old data if applicable
- Optimize slow queries

## Cost Optimization

### Render Free Tier Limitations

- Services sleep after 15 minutes of inactivity
- 750 hours/month total across all services
- Limited build minutes
- No automatic backups

### Cost-Effective Strategies

1. **Optimize Service Usage:**
   - Use sleep-friendly architectures
   - Implement efficient database queries
   - Minimize build frequency

2. **Resource Right-Sizing:**
   - Start with smaller instances
   - Monitor usage and scale up as needed
   - Use staging environments efficiently

3. **Alternative Architectures:**
   - Consider serverless functions for sporadic workloads
   - Use static hosting for frontend when possible
   - Implement client-side caching

This deployment guide should provide a comprehensive foundation for deploying the Second Certainty application to production while maintaining security, performance, and reliability standards.