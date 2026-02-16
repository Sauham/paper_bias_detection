# Deployment Guide - Render

This guide walks you through deploying the Research Paper Analyzer on Render, with the backend as a Web Service and frontend options.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Backend Deployment (Render Web Service)](#backend-deployment)
- [Frontend Deployment Options](#frontend-deployment)
- [Environment Variables](#environment-variables)
- [Post-Deployment](#post-deployment)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before you begin, ensure you have:

- ✅ A [Render account](https://render.com) (free tier available)
- ✅ Your GitHub repository pushed with all changes
- ✅ A Google Gemini API key (for bias analysis)
- ✅ Access to your repository (public or connected to Render)

---

## Backend Deployment

### Step 1: Prepare Backend Configuration

First, create a `render.yaml` file in your project root for easy deployment:

```yaml
services:
  - type: web
    name: paper-bias-backend
    env: python
    region: oregon
    buildCommand: pip install -r backend/requirements.txt && python -m spacy download en_core_web_sm
    startCommand: cd backend && uvicorn api:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: GEMINI_API_KEY
        sync: false
      - key: PYTHON_VERSION
        value: 3.11.0
    autoDeploy: true
```

### Step 2: Create Web Service on Render

1. **Go to [Render Dashboard](https://dashboard.render.com)**

2. **Click "New +" → "Web Service"**

3. **Connect Your Repository**
   - Select "Connect a repository"
   - Choose your GitHub account
   - Select `paper_bias_detection` repository
   - Click "Connect"

4. **Configure the Service**
   
   **Basic Settings:**
   - **Name**: `paper-bias-backend` (or your preferred name)
   - **Region**: Choose closest to your users (e.g., Oregon, Frankfurt)
   - **Branch**: `staging` or `main`
   - **Root Directory**: Leave blank (we'll specify in commands)
   - **Runtime**: `Python 3`

   **Build & Deploy:**
   - **Build Command**:
     ```bash
     pip install -r backend/requirements.txt && python -m spacy download en_core_web_sm
     ```
   
   - **Start Command**:
     ```bash
     cd backend && uvicorn api:app --host 0.0.0.0 --port $PORT
     ```

5. **Select Instance Type**
   - **Free**: 512 MB RAM, spins down after inactivity (good for testing)
   - **Starter ($7/mo)**: 512 MB RAM, always running
   - **Standard ($25/mo)**: 2 GB RAM (recommended for production)

   ⚠️ **Note**: The free tier may be slow for PDF processing. Consider Starter or Standard for production.

### Step 3: Configure Environment Variables

In the Render dashboard for your service:

1. Scroll to **Environment Variables** section
2. Add the following variables:

| Key | Value | Description |
|-----|-------|-------------|
| `GEMINI_API_KEY` | `your-api-key-here` | Your Google Gemini API key |
| `PYTHON_VERSION` | `3.11.0` | Python version |
| `PORT` | (auto-set by Render) | Server port (don't set manually) |

3. Click **Save Changes**

### Step 4: Deploy

1. Click **"Create Web Service"**
2. Render will start building your service
3. Watch the logs for any errors
4. Once deployed, you'll get a URL like: `https://paper-bias-backend.onrender.com`

### Step 5: Test Backend

Test your deployed backend:

```bash
# Health check
curl https://your-backend-url.onrender.com/health

# Should return: {"status":"ok"}
```

---

## Frontend Deployment

You have two options for deploying the frontend:

### Option A: Deploy Frontend on Vercel (Recommended)

**Pros**: Faster edge network, better for static sites, free SSL

1. **Go to [Vercel Dashboard](https://vercel.com)**

2. **Click "New Project"**

3. **Import Git Repository**
   - Select your `paper_bias_detection` repo
   - Click "Import"

4. **Configure Project**
   - **Framework Preset**: Vite
   - **Root Directory**: `web`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`

5. **Add Environment Variable**
   - Key: `VITE_API_BASE`
   - Value: `https://your-backend-url.onrender.com`

6. **Click "Deploy"**

7. Your frontend will be live at `https://your-project.vercel.app`

### Option B: Deploy Frontend on Render

1. **Create New Static Site**
   - Go to Render Dashboard
   - Click "New +" → "Static Site"
   - Connect your repository

2. **Configure Static Site**
   - **Name**: `paper-bias-frontend`
   - **Branch**: `staging` or `main`
   - **Root Directory**: `web`
   - **Build Command**: `npm install && npm run build`
   - **Publish Directory**: `web/dist`

3. **Add Environment Variable**
   - Key: `VITE_API_BASE`
   - Value: `https://your-backend-url.onrender.com`

4. **Click "Create Static Site"**

---

## Environment Variables

### Backend (.env file locally)

Create `backend/.env` for local development:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### Frontend Environment Variables

Create `web/.env` for local development:

```env
VITE_API_BASE=http://localhost:8000
```

For production (Render/Vercel), set:
```env
VITE_API_BASE=https://your-backend-url.onrender.com
```

---

## Post-Deployment

### 1. Update CORS Settings (if needed)

If you get CORS errors, update `backend/api.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-frontend.vercel.app",
        "https://your-frontend.onrender.com",
        "http://localhost:5173"  # for local dev
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 2. Monitor Logs

**On Render:**
- Go to your service → "Logs" tab
- Watch for errors or performance issues

### 3. Set Up Custom Domain (Optional)

**For Vercel:**
- Go to Project Settings → Domains
- Add your custom domain
- Update DNS records

**For Render:**
- Go to Service Settings → Custom Domain
- Add your domain
- Update DNS CNAME record

---

## Troubleshooting

### Issue 1: Backend Takes Long to Start

**Problem**: First request after inactivity is slow (Free tier)

**Solution**: 
- Upgrade to Starter plan ($7/mo) for always-on service
- Or implement a cron job to ping your backend every 14 minutes:
  ```yaml
  # Add to render.yaml
  - type: cron
    name: keep-backend-alive
    schedule: "*/14 * * * *"
    command: curl https://your-backend-url.onrender.com/health
  ```

### Issue 2: Python 3.14 Compatibility Error

**Problem**: Error message: `Core Pydantic V1 functionality isn't compatible with Python 3.14 or greater`

**Solution**: 
- Add `runtime.txt` to project root with: `python-3.11.10`
- Update `PYTHON_VERSION` environment variable to `3.11.10`
- Render will now use Python 3.11 instead of 3.14
- Redeploy your service

**Alternative**: In Render dashboard, set environment variable:
```
PYTHON_VERSION=3.11.10
```

### Issue 3: Build Fails - spaCy Model Download

**Problem**: spaCy model download fails during build

**Solution**: 
- Ensure build command includes: `python -m spacy download en_core_web_sm`
- Or add to `requirements.txt`: `https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.0/en_core_web_sm-3.7.0.tar.gz`

### Issue 4: 502 Bad Gateway

**Problem**: Backend crashes or out of memory

**Solution**:
- Check logs for memory errors
- Upgrade to Standard plan (2GB RAM)
- Optimize PDF processing in code

### Issue 5: API Calls Failing from Frontend

**Problem**: CORS errors or connection refused

**Solution**:
1. Verify `VITE_API_BASE` is set correctly
2. Check CORS settings in `backend/api.py`
3. Ensure backend is running (check logs)
4. Test backend directly with curl

### Issue 6: Slow PDF Processing

**Problem**: Analysis takes too long

**Solution**:
- Upgrade to Standard plan for better CPU
- Optimize dependencies (remove unused libraries)
- Consider caching results
- Implement request queuing

---

## Production Checklist

Before going live:

- [ ] Backend deployed and accessible
- [ ] Frontend deployed and accessible
- [ ] Environment variables configured
- [ ] CORS settings updated
- [ ] Custom domain configured (if applicable)
- [ ] SSL certificate active (auto on Render/Vercel)
- [ ] Error logging set up
- [ ] Health check endpoint working
- [ ] Tested PDF upload and analysis
- [ ] Gemini API key working
- [ ] Performance tested with real PDFs
- [ ] Backup API keys stored securely

---

## Cost Estimate

### Render Free Tier (Testing)
- **Backend**: Free (spins down after inactivity)
- **Frontend**: Free (100 GB bandwidth/month)
- **Total**: $0/month

### Render Starter (Light Production)
- **Backend**: $7/month (always-on, 512MB RAM)
- **Frontend**: Free or $1/month for custom domain
- **Total**: ~$7-8/month

### Render Standard (Production)
- **Backend**: $25/month (2GB RAM, better performance)
- **Frontend**: Free or $1/month
- **Total**: ~$25-26/month

### Recommended Setup
- **Frontend**: Vercel (Free)
- **Backend**: Render Starter ($7/month)
- **Total**: $7/month

---

## Support & Resources

- **Render Docs**: https://render.com/docs
- **Vercel Docs**: https://vercel.com/docs
- **FastAPI Deployment**: https://fastapi.tiangolo.com/deployment/
- **Render Community**: https://community.render.com/

---

## Next Steps

After deployment:

1. **Monitor Performance**: Use Render's metrics dashboard
2. **Set Up Analytics**: Add Google Analytics or similar
3. **Implement Rate Limiting**: Protect against abuse
4. **Add User Authentication**: If needed for your use case
5. **Set Up Backups**: For any user data
6. **Create CI/CD Pipeline**: Auto-deploy on git push

---

**Need Help?** 

Check the logs first, then consult:
- Render documentation
- Project README.md
- GitHub issues

Happy deploying! 🚀
