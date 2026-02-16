# 🚀 Quick Start Deployment Guide

## TL;DR - Deploy in 5 Minutes

### Step 1: Prepare Your Repository
```bash
# Ensure all changes are committed
git add .
git commit -m "chore: Add deployment configuration"
git push origin staging
```

### Step 2: Deploy Backend on Render

**Option A: Using Render Dashboard (Easiest)**
1. Go to https://dashboard.render.com
2. Click "New +" → "Web Service"
3. Connect your GitHub repo
4. Use these settings:
   - **Build Command**: `pip install -r backend/requirements.txt && python -m spacy download en_core_web_sm`
   - **Start Command**: `cd backend && uvicorn api:app --host 0.0.0.0 --port $PORT`
   - **Add Environment Variable**: `GEMINI_API_KEY` = your-api-key
5. Click "Create Web Service"
6. Copy your backend URL: `https://your-app.onrender.com`

**Option B: Using Render Blueprint (Faster)**
1. Push `render.yaml` to your repo
2. Go to https://dashboard.render.com
3. Click "New +" → "Blueprint"
4. Select your repository
5. Render will auto-configure everything
6. Add your `GEMINI_API_KEY` when prompted

### Step 3: Deploy Frontend on Vercel

1. Go to https://vercel.com/new
2. Import your GitHub repo
3. Configure:
   - **Root Directory**: `web`
   - **Framework**: Vite
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
4. Add Environment Variable:
   - **Key**: `VITE_API_BASE`
   - **Value**: `https://your-backend.onrender.com`
5. Click "Deploy"

### Step 4: Verify Deployment

```bash
# Test backend
curl https://your-backend.onrender.com/health

# Or use the verification script
./verify-deployment.sh https://your-backend.onrender.com
```

✅ **Done!** Your app is live!

---

## Essential Commands

### Local Development
```bash
# Backend
cd backend
uvicorn api:app --reload --port 8000

# Frontend (separate terminal)
cd web
npm run dev
```

### Deploy Updates
```bash
# Make changes
git add .
git commit -m "your message"
git push origin staging

# Render auto-deploys on push (if enabled)
# Vercel auto-deploys on push
```

### View Logs
```bash
# On Render Dashboard: Service → Logs
# Or use Render CLI:
render logs -s your-service-name
```

---

## Environment Variables Checklist

### Backend (Render)
- ✅ `GEMINI_API_KEY` - Your Google Gemini API key
- ✅ `PYTHON_VERSION` - `3.11.0`

### Frontend (Vercel)
- ✅ `VITE_API_BASE` - Your backend URL from Render

---

## Pricing Quick Reference

| Service | Tier | Cost | Features |
|---------|------|------|----------|
| **Render Backend** | Free | $0 | Spins down after inactivity |
| **Render Backend** | Starter | $7/mo | Always on, 512MB RAM |
| **Render Backend** | Standard | $25/mo | 2GB RAM, better performance |
| **Vercel Frontend** | Free | $0 | 100GB bandwidth/month |

**Recommended**: Render Starter ($7/mo) + Vercel Free = $7/month total

---

## Common URLs After Deployment

- **Backend API**: `https://your-backend.onrender.com`
- **Backend Health**: `https://your-backend.onrender.com/health`
- **Backend Docs**: `https://your-backend.onrender.com/docs`
- **Frontend**: `https://your-app.vercel.app`

---

## Troubleshooting Quick Fixes

### Python 3.14 Compatibility Error
```bash
# Error: "Pydantic V1 functionality isn't compatible with Python 3.14"
# Fix: Ensure runtime.txt exists with python-3.11.10
# Or set PYTHON_VERSION=3.11.10 in Render environment variables
```

### Backend Won't Start
```bash
# Check logs on Render dashboard
# Common issues:
# 1. Missing GEMINI_API_KEY
# 2. Python version incompatibility (use 3.11.10)
# 3. spaCy model download failed
```

### Frontend Can't Connect to Backend
```bash
# 1. Verify VITE_API_BASE is set correctly
# 2. Check backend is running (visit /health endpoint)
# 3. Check CORS settings in backend/api.py
```

### Slow First Request (Free Tier)
```bash
# This is normal - free tier spins down after inactivity
# Upgrade to Starter plan ($7/mo) for always-on service
```

---

## Next Steps After Deployment

1. ✅ Test with a real PDF upload
2. ✅ Set up custom domain (optional)
3. ✅ Enable monitoring and alerts
4. ✅ Add analytics (Google Analytics, etc.)
5. ✅ Set up database for user data (if needed)

---

## Need More Details?

See [DEPLOYMENT.md](./DEPLOYMENT.md) for the complete step-by-step guide.

---

**Questions?** Check the logs first, then the full deployment guide.

**Happy Deploying!** 🎉
