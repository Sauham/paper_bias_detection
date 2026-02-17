# Render Build Fixes: Complete Guide

This document addresses common build issues when deploying to Render.

---

## Issue 1: Python 3.14 Compatibility Error

### Problem

```
Core Pydantic V1 functionality isn't compatible with Python 3.14 or greater.
pydantic.v1.errors.ConfigError: unable to infer type for attribute "REGEX"
```

### Solution

Render defaults to Python 3.14, but our dependencies need Python 3.11. This is already fixed in the repo with:

1. **`runtime.txt`** - Tells Render to use Python 3.11.10
2. **`render.yaml`** - Sets `PYTHON_VERSION` environment variable

✅ **Already configured** - No action needed if you're using the latest code.

---

## Issue 2: spaCy Build Failures

### Problem

```
error: command '/usr/bin/gcc' failed with exit code 1
ERROR: Failed building wheel for blis
ERROR: Failed to build 'spacy' when installing build dependencies
```

### Why It Happens

spaCy's compiled dependencies (`blis`, `thinc`) need to be built from source, which can fail on Render's build environment.

### Solution Implemented

The app is designed to work **with or without** spaCy:

- ✅ **With spaCy**: Enhanced NLP-based section extraction
- ✅ **Without spaCy**: Regex-based extraction (fallback mode)

Our build process:
1. Installs core dependencies (always succeeds)
2. **Attempts** to install spaCy with pre-built wheels
3. If spaCy fails → continues anyway (app works in regex mode)

### Configuration

**`render.yaml` build command**:
```yaml
buildCommand: |
  pip install --upgrade pip setuptools wheel
  pip install --prefer-binary -r backend/requirements.txt
  pip install --prefer-binary spacy==3.7.5 || echo "spaCy installation failed - using regex-only mode"
  python -m spacy download en_core_web_sm || echo "spaCy model download failed - using regex-only mode"
```

**`requirements.txt`**:
- Core dependencies (required)
- spaCy is installed separately (optional)

**`requirements-spacy.txt`**:
- Optional file for local development
- Install with: `pip install -r backend/requirements-spacy.txt`

---

## Verification After Deploy

### Check Build Logs

Look for these success indicators:

```bash
# Python version
✓ Using Python version 3.11.10

# Dependencies installed
✓ Successfully installed fastapi uvicorn pdfplumber ...

# spaCy status (either is fine)
✓ Successfully installed spacy-3.7.5
# OR
⚠ spaCy installation failed - using regex-only mode
```

### Test Health Endpoint

```bash
curl https://your-app.onrender.com/health
```

Should return:
```json
{
  "status": "ok",
  "nlp_available": true  // or false if spaCy failed
}
```

---

## Force spaCy Installation (Optional)

If you need spaCy and it's failing, try these:

### Option 1: Install Build Dependencies

Update `render.yaml`:
```yaml
buildCommand: |
  apt-get update && apt-get install -y build-essential gcc g++ || true
  pip install --upgrade pip setuptools wheel
  pip install --prefer-binary -r backend/requirements.txt
  pip install --prefer-binary spacy==3.7.5
  python -m spacy download en_core_web_sm
```

### Option 2: Use Docker Deployment

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

# Install build tools
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install spacy==3.7.5
RUN python -m spacy download en_core_web_sm

COPY backend/ .
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
```

Deploy as Docker service on Render.

### Option 3: Use Managed spaCy Service

Alternative: Deploy spaCy as a separate microservice and call it via API.

---

## Environment Variables Required

Set these in Render Dashboard:

```env
GEMINI_API_KEY=your_api_key_here
PYTHON_VERSION=3.11.10
PIP_PREFER_BINARY=1
```

---

## Troubleshooting

### Build Still Failing?

1. **Clear Build Cache**:
   - Render Dashboard → Your Service → Settings → "Clear Build Cache"

2. **Check Python Version in Logs**:
   ```bash
   grep "Python version" build-logs
   # Should show: Using Python version 3.11.10
   ```

3. **Verify Dependencies**:
   ```bash
   # After successful deploy, in Render Shell:
   python --version  # 3.11.10
   pip list | grep -E "fastapi|spacy"
   ```

4. **Test Without spaCy**:
   - Remove spaCy install line from `render.yaml`
   - App will work in regex-only mode
   - Upload a test PDF to verify core functionality

### Runtime Errors?

If the app deploys but crashes:

1. **Check Service Logs**:
   - Render Dashboard → Your Service → Logs

2. **Missing Dependencies**:
   ```bash
   # Common issues
   ModuleNotFoundError: No module named 'pdfplumber'
   → Check requirements.txt installed correctly
   ```

3. **API Key Issues**:
   ```bash
   # Test with curl
   curl -X POST https://your-app.onrender.com/analyze \
     -F "file=@test.pdf"
   ```

---

## Summary

✅ **Python 3.14 Error** → Fixed with `runtime.txt` + `PYTHON_VERSION`  
✅ **spaCy Build Error** → Graceful fallback to regex-only mode  
✅ **App Functionality** → Works with or without spaCy  

**Current setup ensures deployment succeeds** even if optional dependencies fail.

---

## Files Changed

- ✅ `runtime.txt` - Python 3.11.10
- ✅ `render.yaml` - Updated build command with fallbacks
- ✅ `backend/requirements.txt` - Core dependencies only
- ✅ `backend/requirements-spacy.txt` - Optional spaCy (new)
- ✅ `backend/src/plagiarism_checker.py` - Already has spaCy fallback logic

---

## Next Steps

1. **Commit and push** all changes
2. **Trigger redeploy** on Render
3. **Monitor build logs** for success
4. **Test API endpoints** after deployment

```bash
git add .
git commit -m "fix: Optimize Render build with spaCy fallback"
git push origin main
```

---

**Need help?** Check the build logs first - they'll tell you exactly what succeeded/failed.
