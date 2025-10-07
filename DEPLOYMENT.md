# Deployment Guide

## Quick Deploy to Hugging Face Spaces

### Prerequisites
- GitHub/Hugging Face account
- Google AI Studio API key (get from https://aistudio.google.com/app/apikey)
- (Optional) SerpAPI key for web search

### Step 1: Prepare Repository
```bash
# Initialize git if not already done
git init
git add .
git commit -m "Initial commit"
```

### Step 2: Create Hugging Face Space
1. Go to https://huggingface.co/spaces
2. Click "Create new Space"
3. Configure:
   - **Name**: `problem-2-multi-agentic`
   - **License**: Apache 2.0 (or your choice)
   - **SDK**: Docker
   - **Visibility**: Public or Private

### Step 3: Link Repository
```bash
# Add HF remote (replace YOUR_USERNAME)
git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/problem-2-multi-agentic

# Push to HF Spaces
git push hf main
```

### Step 4: Configure Secrets
In your Space settings (Settings → Repository secrets):

1. **GOOGLE_API_KEY** (Required)
   - Value: Your Google AI Studio API key
   - Example: `AIzaSyC...`

2. **GEMINI_MODEL** (Optional)
   - Default: `gemini-2.5-flash`
   - Options: `gemini-2.5-flash`, `gemini-2.5-pro`, `gemini-flash-lite-latest`

3. **SERPAPI_API_KEY** (Optional)
   - If omitted, falls back to DuckDuckGo
   - Get from: https://serpapi.com/

### Step 5: Wait for Build
- HF Spaces will automatically build your Docker container
- Build time: ~5-10 minutes
- Check logs in "Logs" tab if issues occur

### Step 6: Access Your App
- URL: `https://huggingface.co/spaces/YOUR_USERNAME/problem-2-multi-agentic`
- The app will be running on port 7860 internally
- HF provides a public URL automatically

---

## Alternative: Deploy to Render

### Step 1: Create Account
- Sign up at https://render.com
- Connect your GitHub account

### Step 2: Create Web Service
1. Dashboard → "New" → "Web Service"
2. Connect your GitHub repository
3. Configure:
   - **Name**: `problem-2-multi-agentic`
   - **Environment**: Docker
   - **Branch**: main
   - **Plan**: Free (or paid for better performance)

### Step 3: Environment Variables
Add in the "Environment" tab:
- `GOOGLE_API_KEY`: Your API key
- `GEMINI_MODEL`: (optional) `gemini-2.5-flash`
- `SERPAPI_API_KEY`: (optional)

### Step 4: Deploy
- Click "Create Web Service"
- Render will auto-detect Dockerfile
- Build time: ~5-10 minutes
- Access via provided .onrender.com URL

---

## Local Development

### Setup
```powershell
# Create virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Create .env file
Copy-Item .env.example .env
notepad .env  # Add your API keys
```

### Run
```powershell
uvicorn backend.main:app --host 0.0.0.0 --port 7860 --reload
```

Access at: http://localhost:7860

---

## Troubleshooting

### Build fails on HF Spaces
- Check "Logs" tab for errors
- Common issue: Missing dependencies → verify requirements.txt
- Docker build timeout → simplify dependencies or use smaller base image

### "Mock LLM Response" appearing
- Check Space Secrets are set correctly
- Verify GOOGLE_API_KEY is valid
- Check logs via GET /logs endpoint for error details

### FAISS/Sentence-Transformers issues
- On first run, downloads ~90MB model cache
- HF Spaces: cached automatically after first build
- Render: may need to increase disk space allocation

### Port conflicts locally
- Change port: `uvicorn backend.main:app --port 8000`
- Check no other service is using 7860

---

## API Keys - Security Reminders

⚠️ **Never commit API keys to git**
- Use .env locally (already in .gitignore)
- Use Space/Render secrets for deployment

⚠️ **Rotate exposed keys immediately**
- If keys were accidentally committed or shared

⚠️ **Monitor usage**
- Google AI Studio: https://aistudio.google.com/app/apikey
- SerpAPI: https://serpapi.com/dashboard

---

## Performance Notes

### Free Tier Limits
- **Google Gemini**: 15 req/min, 1.5K req/day
- **SerpAPI**: 100 searches/month
- **HF Spaces**: 2GB RAM, 16GB disk, CPU only
- **Render Free**: 512MB RAM, sleeps after 15min inactivity

### Recommendations
- For production: upgrade to paid plans
- For demo: free tiers are sufficient
- Consider caching frequently asked queries

---

## Next Steps After Deployment

1. **Test all endpoints**:
   - Upload a PDF
   - Ask questions about it
   - Try Web Search and ArXiv queries
   - Check /logs endpoint

2. **Monitor logs**:
   - View traces via /logs
   - Check for errors in Space/Render logs

3. **Share your Space**:
   - HF Spaces can be embedded in websites
   - Share URL: `https://huggingface.co/spaces/YOUR_USERNAME/problem-2-multi-agentic`

4. **Iterate**:
   - Add more sample PDFs
   - Tune model parameters
   - Improve rationale descriptions
