# Deployment Guide for Lilly PDF Extraction Tool

## ⚠️ Important: Netlify is NOT Recommended

**Netlify does not support:**
- Python Flask applications (backend frameworks)
- Heavy computational libraries (OCR, PDF processing)
- File upload/processing workflows
- Long-running processes

## ✅ Recommended Deployment Platforms

### Option 1: Heroku (Recommended)
**Best for:** Full-featured Flask apps with file processing

**Steps:**
1. Install Heroku CLI: https://devcenter.heroku.com/articles/heroku-cli
2. Login to Heroku:
   ```bash
   heroku login
   ```
3. Create a new Heroku app:
   ```bash
   heroku create lilly-pdf-extractor
   ```
4. Add buildpacks for Poppler (PDF processing):
   ```bash
   heroku buildpacks:add --index 1 https://github.com/heroku/heroku-buildpack-apt
   ```
5. Create `Aptfile` in root directory:
   ```
   poppler-utils
   ```
6. Deploy:
   ```bash
   git add .
   git commit -m "Prepare for Heroku deployment"
   git push heroku master
   ```
7. Open your app:
   ```bash
   heroku open
   ```

**Note:** Heroku Dynos sleep after 30 minutes of inactivity on free tier.

---

### Option 2: Render (Free Tier Available)
**Best for:** Modern deployment with automatic scaling

**Steps:**
1. Go to https://render.com
2. Sign up and connect your GitHub repository
3. Create a new "Web Service"
4. Configure:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app --timeout 300`
   - **Environment:** Python 3
5. Add environment variable:
   - `PYTHON_VERSION=3.11.9`
6. Deploy!

**Advantages:**
- Free tier with no sleep time
- Automatic SSL
- Easy GitHub integration

---

### Option 3: Railway (Easy & Modern)
**Best for:** Quick deployment with simple interface

**Steps:**
1. Go to https://railway.app
2. Sign in with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your repository
5. Railway auto-detects Python and deploys
6. Done!

**Advantages:**
- $5 free credit monthly
- Automatic deployments
- Simple dashboard

---

### Option 4: Google Cloud Run (Scalable)
**Best for:** Production-grade deployment

**Steps:**
1. Install Google Cloud SDK
2. Create Dockerfile:
   ```dockerfile
   FROM python:3.11-slim
   
   RUN apt-get update && apt-get install -y \\
       poppler-utils \\
       libgl1-mesa-glx \\
       libglib2.0-0
   
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   
   COPY . .
   
   CMD gunicorn app:app --bind 0.0.0.0:$PORT --timeout 300
   ```
3. Deploy:
   ```bash
   gcloud run deploy lilly-pdf-extractor --source .
   ```

---

### Option 5: Azure App Service
**Best for:** Enterprise deployment with Microsoft integration

**Steps:**
1. Install Azure CLI
2. Login:
   ```bash
   az login
   ```
3. Create resource group:
   ```bash
   az group create --name lilly-pdf-rg --location eastus
   ```
4. Create App Service plan:
   ```bash
   az appservice plan create --name lilly-pdf-plan --resource-group lilly-pdf-rg --sku B1 --is-linux
   ```
5. Create web app:
   ```bash
   az webapp create --resource-group lilly-pdf-rg --plan lilly-pdf-plan --name lilly-pdf-extractor --runtime "PYTHON|3.11"
   ```
6. Deploy:
   ```bash
   az webapp up --name lilly-pdf-extractor --resource-group lilly-pdf-rg
   ```

---

## 🔧 Files Already Created for Deployment

- ✅ `Procfile` - Heroku/Render deployment configuration
- ✅ `runtime.txt` - Python version specification
- ✅ `requirements.txt` - Updated with gunicorn and fixed dependencies

## 🚫 Why Not Netlify?

Netlify is designed for:
- Static HTML/CSS/JS sites
- JAMstack applications
- Frontend frameworks (React, Vue, etc.)
- Serverless functions (limited Node.js/Go/Rust)

Your app needs:
- Backend processing (Flask)
- File uploads/storage
- Heavy computation (OCR, PDF parsing)
- Long-running processes (>10 seconds)

## 📝 Next Steps

1. Choose a platform above (Render or Railway recommended for ease)
2. Follow the platform-specific steps
3. Monitor the deployment logs
4. Test with a sample PDF

## 🆘 Troubleshooting

**If OCR fails on deployment:**
- Check if Poppler is installed (needed for pdf2image)
- Verify EasyOCR models download correctly
- Consider disabling OCR for faster deployment testing

**If memory issues occur:**
- Upgrade to paid tier with more RAM
- Optimize PDF processing (reduce image sizes)
- Process files in chunks

**If build times are too long:**
- Use Docker for faster rebuilds
- Cache pip dependencies
- Pre-build OCR models in Docker image
