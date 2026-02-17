# Frontend Deployment Guide

## 🚀 Quick Deploy to Vercel

### Prerequisites
- ✅ Backend deployed at: `https://paper-bias-detection.onrender.com`
- ✅ Vercel account (free)

---

## Step 1: Configure Backend URL

The frontend is already configured to use environment variables. Update `web/.env`:

```env
VITE_API_BASE=https://paper-bias-detection.onrender.com
```

✅ **Already done for you!** The file is created.

---

## Step 2: Deploy to Vercel

### Option A: One-Click Deploy (Recommended)

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/rk0802p/paper_bias_detection&root-directory=web&env=VITE_API_BASE&envDescription=Backend%20API%20URL&envLink=https://paper-bias-detection.onrender.com)

### Option B: Manual Deploy

1. **Install Vercel CLI**:
   ```bash
   npm install -g vercel
   ```

2. **Navigate to web directory**:
   ```bash
   cd web
   ```

3. **Deploy**:
   ```bash
   vercel
   ```

4. **Follow prompts**:
   - Link to existing project? → No
   - Project name? → `paper-bias-detection-frontend`
   - Directory? → `./` (current directory)
   - Want to override settings? → No

5. **Set environment variable**:
   ```bash
   vercel env add VITE_API_BASE production
   # When prompted, enter: https://paper-bias-detection.onrender.com
   ```

6. **Redeploy**:
   ```bash
   vercel --prod
   ```

### Option C: GitHub Integration

1. Go to [vercel.com](https://vercel.com)
2. Click "Import Project"
3. Import from GitHub: `rk0802p/paper_bias_detection`
4. Configure:
   - **Framework Preset**: Vite
   - **Root Directory**: `web`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
5. Add Environment Variable:
   - **Name**: `VITE_API_BASE`
   - **Value**: `https://paper-bias-detection.onrender.com`
6. Click "Deploy"

---

## Step 3: Test Your Deployment

After deployment, your frontend will be available at:
```
https://your-project-name.vercel.app
```

### Test the connection:

1. **Open your deployed frontend**
2. **Open browser console** (F12)
3. **Upload a test PDF**
4. **Check network tab** - should see requests to:
   ```
   https://paper-bias-detection.onrender.com/analyze
   ```

---

## 🔧 Local Development

### Test with Production Backend

```bash
cd web
npm install
npm run dev
```

Your local frontend will connect to the production backend automatically.

### Test with Local Backend

1. Update `web/.env`:
   ```env
   VITE_API_BASE=http://localhost:8000
   ```

2. Start local backend:
   ```bash
   cd backend
   python -m uvicorn api:app --reload
   ```

3. Start frontend:
   ```bash
   cd web
   npm run dev
   ```

---

## 🌐 CORS Configuration

✅ **Already configured!** Your backend allows all origins:

```python
# backend/api.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows your Vercel deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

No additional configuration needed!

---

## 📊 Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `VITE_API_BASE` | Backend API URL | `https://paper-bias-detection.onrender.com` |

### How to Update on Vercel:

1. Go to your project on Vercel
2. **Settings** → **Environment Variables**
3. Edit `VITE_API_BASE`
4. Click **Save**
5. **Redeploy** from Deployments tab

---

## 🐛 Troubleshooting

### CORS Errors

If you see:
```
Access to fetch at 'https://...' has been blocked by CORS policy
```

**Solution**: Backend CORS is already configured. Clear browser cache and try again.

### 404 on API Calls

If you see `404 Not Found` when uploading:

1. **Check backend URL** in browser console
2. **Verify environment variable**:
   ```bash
   vercel env ls
   ```
3. **Ensure backend is running**:
   ```bash
   curl https://paper-bias-detection.onrender.com/health
   ```

### Network Errors

If requests fail:

1. **Check backend health**:
   ```bash
   curl https://paper-bias-detection.onrender.com/health
   ```

2. **Check backend logs** on Render dashboard

3. **Verify VITE_API_BASE** is set correctly

---

## 🔐 Production Checklist

- ✅ Backend deployed: `https://paper-bias-detection.onrender.com`
- ✅ Backend health endpoint working
- ✅ CORS configured
- ✅ Frontend environment variable set
- ✅ Frontend deployed to Vercel
- ✅ Test file upload working

---

## 📱 Custom Domain (Optional)

### On Vercel:

1. Go to your project → **Settings** → **Domains**
2. Add your custom domain (e.g., `bias-detector.yourdomain.com`)
3. Update DNS records as instructed
4. SSL certificate auto-generated

### Update Backend CORS (Recommended):

For better security, restrict CORS to your domain:

```python
# backend/api.py
allow_origins=[
    "https://your-project.vercel.app",
    "https://bias-detector.yourdomain.com",
    "http://localhost:5173"  # For local dev
]
```

---

## 🚀 Quick Commands

```bash
# Deploy frontend
cd web
vercel --prod

# Update environment variable
vercel env add VITE_API_BASE production

# Check deployment
curl https://your-project.vercel.app

# View logs
vercel logs
```

---

## ✨ Summary

Your setup:
- **Backend**: https://paper-bias-detection.onrender.com ✅
- **Frontend**: Deploy to Vercel with one command ✅
- **CORS**: Already configured ✅
- **Environment**: `.env` file created ✅

**You're ready to deploy!** 🎉

Run:
```bash
cd web
vercel
```

And your app will be live!
