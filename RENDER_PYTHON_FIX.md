# Fix: Python 3.14 Compatibility Error on Render

## Problem

When deploying to Render, you may encounter this error:

```
Core Pydantic V1 functionality isn't compatible with Python 3.14 or greater.
pydantic.v1.errors.ConfigError: unable to infer type for attribute "REGEX"
```

This happens because:
- Render defaults to Python 3.14 (latest version)
- spaCy depends on Pydantic v1
- Pydantic v1 is incompatible with Python 3.14+

## Solution (Choose One)

### Option 1: Using runtime.txt (Recommended)

1. **Create `runtime.txt` in project root**:
   ```bash
   echo "python-3.11.10" > runtime.txt
   ```

2. **Commit and push**:
   ```bash
   git add runtime.txt
   git commit -m "fix: Specify Python 3.11 for Render compatibility"
   git push origin staging
   ```

3. **Render will automatically use Python 3.11 on next deploy**

### Option 2: Using Render Dashboard

1. Go to your service on Render Dashboard
2. Click **Environment** tab
3. Add/Update environment variable:
   - **Key**: `PYTHON_VERSION`
   - **Value**: `3.11.10`
4. Click **Save Changes**
5. Manually trigger a new deploy

### Option 3: Update render.yaml

If using Blueprint deployment, ensure `render.yaml` has:

```yaml
services:
  - type: web
    name: paper-bias-backend
    env: python
    envVars:
      - key: PYTHON_VERSION
        value: "3.11.10"
```

## Verify the Fix

After deploying, check the build logs. You should see:

```
Using Python version 3.11.10
```

Instead of:

```
Using Python version 3.14.3
```

## Why This Works

- **Python 3.11** is stable and compatible with all dependencies
- **spaCy 3.7.x** fully supports Python 3.11
- **Pydantic v1** works correctly with Python 3.11
- No breaking changes needed to your code

## Alternative: Upgrade Dependencies (Not Recommended Yet)

You could upgrade to spaCy 4.0 (when available) which uses Pydantic v2:

```bash
# Future solution - not available yet
pip install spacy>=4.0.0
```

But this would require significant code changes and spaCy 4.0 is not stable yet.

## Quick Commands

```bash
# Fix and deploy in one go
echo "python-3.11.10" > runtime.txt
git add runtime.txt backend/requirements.txt render.yaml
git commit -m "fix: Pin Python 3.11 for dependency compatibility"
git push origin staging
```

## Still Having Issues?

1. **Clear Render's build cache**: 
   - Dashboard → Your Service → Settings → Clear Build Cache

2. **Check Python version in logs**:
   ```bash
   # Should show 3.11.10, not 3.14.x
   grep "Python version" build-logs
   ```

3. **Verify dependencies installed**:
   ```bash
   # In Render shell (if available)
   python --version  # Should show 3.11.10
   pip list | grep spacy  # Should show spacy 3.7.x
   ```

## Related Files Updated

- ✅ `runtime.txt` - Specifies Python 3.11.10
- ✅ `render.yaml` - Updated PYTHON_VERSION env var
- ✅ `backend/requirements.txt` - Pinned compatible versions
- ✅ `DEPLOYMENT.md` - Added troubleshooting section
- ✅ `DEPLOYMENT_QUICKSTART.md` - Added quick fix

---

**That's it!** Your deployment should now work correctly. 🎉
