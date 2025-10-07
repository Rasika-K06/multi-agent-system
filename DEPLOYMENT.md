# Deployment Guide

This guide explains how to run this project locally or deploy it to a cloud platform.

---

## Prerequisites

- **Python 3.10+** installed
- **Google Gemini API Key** (required)
  - Get one free at: https://aistudio.google.com/app/apikey
- **SerpAPI Key** (optional, for web search)
  - Get one at: https://serpapi.com/ (free tier: 100 searches/month)
  - If omitted, system falls back to DuckDuckGo

---

## Option 1: Local Development (Recommended for Testing)

### Step 1: Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/multi-agent-system.git
cd multi-agent-system
```

### Step 2: Create Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

1. Copy the example file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your API keys:
   ```bash
   GOOGLE_API_KEY=your_actual_google_ai_studio_key
   GEMINI_MODEL=gemini-2.5-flash  # optional
   SERPAPI_API_KEY=your_serpapi_key  # optional
   ```

### Step 5: Run the Application
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 7860 --reload
```

### Step 6: Access the Application
Open your browser and go to: **http://localhost:7860**

- Try uploading a PDF and asking questions
- Test web search: "Latest news on AI"
- Test ArXiv: "Recent papers on transformers"
- View logs at: http://localhost:7860/logs

---

## Option 2: Docker Deployment (Production-Ready)

This method uses Docker to containerize the application, making it easy to deploy anywhere.

### Step 1: Install Docker
- Download from: https://www.docker.com/products/docker-desktop

### Step 2: Build the Docker Image
```bash
docker build -t multi-agentic-system .
```

### Step 3: Run the Container
```bash
docker run -p 7860:7860 \
  -e GOOGLE_API_KEY=your_actual_key \
  -e GEMINI_MODEL=gemini-2.5-flash \
  -e SERPAPI_API_KEY=your_serpapi_key \
  multi-agentic-system
```

### Step 4: Access the Application
Open: **http://localhost:7860**

---

## Option 3: Deploy to Hugging Face Spaces (Free Hosting)

Hugging Face Spaces provides free hosting for ML/AI demos.

### Step 1: Create a Hugging Face Account
- Sign up at: https://huggingface.co/join

### Step 2: Create a New Space
1. Go to: https://huggingface.co/new-space
2. Configure:
   - **Space name**: `multi-agent-system` (or any name)
   - **License**: Apache 2.0
   - **Space SDK**: **Docker**
   - **Docker template**: **Blank/From Scratch**
   - **Visibility**: Public (or Private)

### Step 3: Push Your Code
```bash
# Add HF remote (replace YOUR_USERNAME with your HF username)
git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/multi-agent-system

# Push to Hugging Face
git push hf main
```

### Step 4: Add API Keys as Secrets
1. Go to your Space → **Settings** → **Repository secrets**
2. Add these secrets:
   - `GOOGLE_API_KEY`: Your Gemini API key
   - `GEMINI_MODEL`: `gemini-2.5-flash` (optional)
   - `SERPAPI_API_KEY`: Your SerpAPI key (optional)

### Step 5: Wait for Build
- Hugging Face will automatically build your Docker image (~5-10 min)
- Once done, your app will be live at:
  `https://huggingface.co/spaces/YOUR_USERNAME/multi-agent-system`

---

## Option 4: Deploy to Render (Alternative Cloud Platform)

### Step 1: Create Render Account
- Sign up at: https://render.com
- Connect your GitHub account

### Step 2: Create Web Service
1. Dashboard → **New** → **Web Service**
2. Connect your GitHub repository
3. Configure:
   - **Name**: `multi-agent-system`
   - **Environment**: Docker
   - **Branch**: main
   - **Plan**: Free (or paid for production)

### Step 3: Add Environment Variables
In the "Environment" tab, add:
- `GOOGLE_API_KEY`: Your API key
- `GEMINI_MODEL`: `gemini-2.5-flash` (optional)
- `SERPAPI_API_KEY`: Your SerpAPI key (optional)

### Step 4: Deploy
- Click **Create Web Service**
- Render auto-detects Dockerfile and deploys
- Access via the provided `.onrender.com` URL

---

## Troubleshooting

### Common Issues

**1. "Mock LLM Response" in output**
- **Cause**: Invalid or missing `GOOGLE_API_KEY`
- **Fix**: Verify your API key is correct and active
- **Check logs**: Visit http://localhost:7860/logs for detailed error info

**2. Module not found errors**
- **Cause**: Dependencies not installed
- **Fix**: Make sure you're in the virtual environment and run:
  ```bash
  pip install -r requirements.txt
  ```

**3. FAISS installation fails on Windows**
- **Cause**: No pre-built wheel for your Python version
- **Fix**: Use Python 3.10 or 3.12 (not 3.13)
- **Alternative**: Install Visual Studio Build Tools

**4. Port 7860 already in use**
- **Fix**: Change the port:
  ```bash
  uvicorn backend.main:app --port 8000
  ```

**5. Slow first startup**
- **Normal**: The app downloads ~90MB sentence-transformers model on first run
- **Wait**: 1-2 minutes for model download and sample PDF generation

**6. Docker build fails**
- **Check**: Docker Desktop is running
- **Check**: You're in the project root directory
- **Retry**: Sometimes network issues cause timeouts, just retry

---

## Running Tests

To verify everything works correctly:

```bash
# Make sure you're in the virtual environment
pytest -v
```

Tests cover:
- API endpoints (`/ask`, `/upload_pdf`, `/logs`)
- Controller routing logic
- RAG retrieval with re-ranking

---

## Security Best Practices

⚠️ **Important Reminders:**

1. **Never commit API keys to git**
   - Use `.env` locally (already in `.gitignore`)
   - Use platform secrets for cloud deployment

2. **Rotate exposed keys immediately**
   - If you accidentally commit a key, revoke it at:
     - Google AI Studio: https://aistudio.google.com/app/apikey
     - SerpAPI: https://serpapi.com/dashboard

3. **Monitor API usage**
   - Keep an eye on your quota to avoid unexpected charges

---

## API Limits (Free Tier)

- **Google Gemini**: 15 requests/min, 1,500 requests/day
- **SerpAPI**: 100 searches/month
- **Hugging Face Spaces**: 2GB RAM, 16GB disk, CPU only
- **Render Free**: 512MB RAM, sleeps after 15min inactivity

💡 **Tip**: For a demo/assessment, free tiers are more than sufficient.

---

## Next Steps

1. **Test all features**:
   - Upload a PDF and ask questions
   - Try: "Latest news on renewable energy"
   - Try: "Recent papers on transformers"
   - Check logs at `/logs` endpoint

2. **Customize for your use case**:
   - Add more sample PDFs relevant to your domain
   - Tune the retrieval parameters in `rag_pdf.py`
   - Adjust model temperature in `controller.py`

3. **Share your deployment**:
   - If deployed to HF Spaces: share the public URL
   - Add a badge to your README

---

## Need Help?

If you encounter issues:
1. Check the **Troubleshooting** section above
2. Review logs at http://localhost:7860/logs
3. Verify your API keys are valid
4. Ensure all dependencies are installed correctly
