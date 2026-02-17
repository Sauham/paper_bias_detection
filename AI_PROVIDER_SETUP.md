# AI Provider Setup Guide

This guide explains how to configure and use different AI providers for bias analysis with automatic fallback.

---

## 🎯 **Supported Providers**

| Provider | Model | Cost | Rate Limits | Best For |
|----------|-------|------|-------------|----------|
| **Gemini** | `gemini-2.0-flash` | Free tier: 1,500 RPD | 15 RPM, 1,500 RPD | Primary use, fast responses |
| **OpenRouter** | `openai/gpt-oss-120b:free` | Completely free | No limits | Fallback, high volume |

---

## 🚀 **Quick Setup**

### **Option 1: Gemini Only (Default)**

```env
AI_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_key_here
GEMINI_MODEL=gemini-2.0-flash
BIAS_ANALYSIS_ENABLED=true
```

**Get Gemini API Key:** https://aistudio.google.com/app/apikey

### **Option 2: OpenRouter Only**

```env
AI_PROVIDER=openrouter
OPENROUTER_API_KEY=your_openrouter_key_here
OPENROUTER_MODEL=openai/gpt-oss-120b:free
BIAS_ANALYSIS_ENABLED=true
```

**Get OpenRouter API Key:** https://openrouter.ai/keys

### **Option 3: Gemini with OpenRouter Fallback (Recommended)**

```env
AI_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_key_here
GEMINI_MODEL=gemini-2.0-flash
OPENROUTER_API_KEY=your_openrouter_key_here
OPENROUTER_MODEL=openai/gpt-oss-120b:free
BIAS_ANALYSIS_ENABLED=true
```

**How it works:**
1. ✅ Try Gemini first (fast, high quality)
2. ❌ If Gemini fails (rate limit, quota exceeded)
3. 🔄 Automatically switch to OpenRouter (unlimited, free)

---

## 📋 **Environment Variables**

### **Required**

```env
# Choose primary provider
AI_PROVIDER=gemini  # Options: "gemini" or "openrouter"

# Enable/disable bias analysis
BIAS_ANALYSIS_ENABLED=true
```

### **Gemini Configuration**

```env
# Get from: https://aistudio.google.com/app/apikey
GEMINI_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# Model options:
#   - gemini-2.0-flash (recommended - stable and fast)
#   - gemini-1.5-flash (legacy)
#   - gemini-1.5-pro   (slower but more capable)
GEMINI_MODEL=gemini-2.0-flash
```

### **OpenRouter Configuration**

```env
# Get from: https://openrouter.ai/keys
OPENROUTER_API_KEY=sk-or-v1-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# Model options:
#   - openai/gpt-oss-120b:free (recommended - free, no limits)
#   - openai/gpt-4o (paid, higher quality)
#   - anthropic/claude-3-sonnet (paid, higher quality)
OPENROUTER_MODEL=openai/gpt-oss-120b:free
```

---

## 🔧 **Configuration for Different Environments**

### **Local Development**

**File:** `backend/.env`

```env
AI_PROVIDER=gemini
GEMINI_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
OPENROUTER_API_KEY=sk-or-v1-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
GEMINI_MODEL=gemini-2.0-flash
OPENROUTER_MODEL=openai/gpt-oss-120b:free
BIAS_ANALYSIS_ENABLED=true
```

### **Render Deployment**

**Set via Dashboard → Environment Variables:**

```
AI_PROVIDER = gemini
GEMINI_API_KEY = AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
OPENROUTER_API_KEY = sk-or-v1-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
GEMINI_MODEL = gemini-2.0-flash
OPENROUTER_MODEL = openai/gpt-oss-120b:free
BIAS_ANALYSIS_ENABLED = true
```

### **Docker**

**File:** `docker-compose.yml`

```yaml
services:
  backend:
    environment:
      - AI_PROVIDER=gemini
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - GEMINI_MODEL=gemini-2.0-flash
      - OPENROUTER_MODEL=openai/gpt-oss-120b:free
      - BIAS_ANALYSIS_ENABLED=true
```

---

## 🧪 **Testing Your Configuration**

### **Test Script**

```bash
cd backend
python -m src.bias_analyzer
```

**Expected output:**
```
BiasAnalyzer initialized with Gemini: gemini-2.0-flash
Analyzing test text...
✅ Gemini API call successful
✅ Analysis complete using gemini
Provider Used: gemini
Overall Score: 72/100
Severity: high
```

### **Test API Endpoints**

```bash
# Health check
curl https://your-backend.onrender.com/health

# Upload test PDF
curl -X POST https://your-backend.onrender.com/analyze \
  -F "file=@test.pdf"
```

---

## 🔄 **Fallback Behavior**

### **How Fallback Works**

1. **Primary attempt:**
   ```
   Try Gemini API → Success? ✅ Return result
   ```

2. **Fallback on failure:**
   ```
   Gemini fails? → Try OpenRouter → Success? ✅ Return result
   ```

3. **Both fail:**
   ```
   Return error with details from both attempts
   ```

### **Fallback Triggers**

OpenRouter fallback activates when Gemini returns:
- `429 Too Many Requests` (rate limit)
- `403 Forbidden` (quota exceeded)
- `500 Internal Server Error`
- Network timeout
- Any other API error

### **Response Metadata**

Check which provider was used:

```json
{
  "bias_analysis": {
    "provider": "gemini",  // or "openrouter"
    "overall_score": 25,
    "severity": "low"
  }
}
```

---

## 📊 **Provider Comparison**

### **Gemini**

**Pros:**
- ✅ Very fast response times (~2-5 seconds)
- ✅ High quality analysis
- ✅ Good context understanding
- ✅ Free tier available

**Cons:**
- ❌ Rate limits (15 RPM)
- ❌ Daily quota (1,500 RPD)
- ❌ Requires API key setup

**Best for:** Primary provider for most users

### **OpenRouter (gpt-oss-120b:free)**

**Pros:**
- ✅ Completely free
- ✅ No rate limits
- ✅ No daily quotas
- ✅ Easy API key setup

**Cons:**
- ⚠️ Slightly slower (~5-10 seconds)
- ⚠️ May be less consistent
- ⚠️ Depends on OpenRouter availability

**Best for:** Fallback, high-volume testing, demo purposes

---

## 🐛 **Troubleshooting**

### **Issue: "Bias analysis disabled"**

**Check:**
```bash
# Verify environment variables are set
echo $GEMINI_API_KEY
echo $OPENROUTER_API_KEY
echo $AI_PROVIDER
```

**Fix:**
1. Ensure `BIAS_ANALYSIS_ENABLED=true`
2. Verify at least one API key is set
3. Check `AI_PROVIDER` matches available keys

---

### **Issue: "Gemini 429 rate limit"**

**Immediate fix:**
1. Wait a few minutes for quota reset
2. Or add OpenRouter as fallback (automatic)

**Long-term fix:**
1. Upgrade Gemini to paid tier
2. Use OpenRouter as primary (`AI_PROVIDER=openrouter`)

---

### **Issue: "Both providers failed"**

**Check:**
1. API keys are valid
2. Internet connection works
3. Provider services are up:
   - Gemini: https://status.cloud.google.com/
   - OpenRouter: https://status.openrouter.ai/

**Debug:**
```bash
# Check Render logs
# Look for detailed error messages
# Try test script locally first
python -m src.bias_analyzer
```

---

## 💡 **Best Practices**

### **For Development**

```env
AI_PROVIDER=gemini
GEMINI_API_KEY=your_dev_key
OPENROUTER_API_KEY=your_dev_key
```
- Use Gemini for fast iteration
- OpenRouter fallback for peace of mind

### **For Production**

```env
AI_PROVIDER=gemini
GEMINI_API_KEY=your_prod_key (paid tier)
OPENROUTER_API_KEY=your_backup_key
```
- Paid Gemini for reliability
- OpenRouter as safety net

### **For High Volume / Demo**

```env
AI_PROVIDER=openrouter
OPENROUTER_API_KEY=your_key
```
- No rate limits
- Predictable costs (free)

---

## 🔐 **Security**

### **Protect Your API Keys**

```bash
# ✅ Good - Use environment variables
export GEMINI_API_KEY=xxx

# ❌ Bad - Hardcode in code
api_key = "AIzaSyXXXXXX"  # NEVER DO THIS

# ✅ Good - Use .env file (gitignored)
echo "GEMINI_API_KEY=xxx" >> backend/.env

# ❌ Bad - Commit .env to git
git add backend/.env  # NEVER DO THIS
```

### **Key Rotation**

Rotate keys regularly:
1. Generate new key in provider dashboard
2. Update environment variable
3. Test new key works
4. Delete old key from provider

---

## 📈 **Monitoring**

### **Check Usage**

**Gemini:**
- Dashboard: https://aistudio.google.com/app/apikey
- Monitor: requests per day, quota remaining

**OpenRouter:**
- Dashboard: https://openrouter.ai/activity
- Monitor: total requests, costs (if using paid models)

### **Log Analysis**

Backend logs show which provider was used:

```
✅ Gemini API call successful
✅ Analysis complete using gemini
```

Or:

```
Gemini API failed: 429 Too Many Requests
🔄 Falling back to OpenRouter
✅ OpenRouter API call successful
✅ Analysis complete using openrouter
```

---

## 🎯 **Summary**

**Recommended Setup:**

```env
# backend/.env
AI_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_key
OPENROUTER_API_KEY=your_openrouter_key
GEMINI_MODEL=gemini-2.0-flash
OPENROUTER_MODEL=openai/gpt-oss-120b:free
BIAS_ANALYSIS_ENABLED=true
```

**This gives you:**
- ✅ Fast primary provider (Gemini)
- ✅ Reliable fallback (OpenRouter)
- ✅ No downtime from rate limits
- ✅ Best of both worlds

**Deploy to Render:**
1. Add all environment variables in dashboard
2. Redeploy service
3. Test with PDF upload
4. Check logs to verify provider usage

Done! 🎉
