# Quick Deploy to Render.com

## Steps:

1. **Go to https://render.com and sign up**

2. **Connect your GitHub repository**
   - Click "New +" → "Web Service"
   - Connect to GitHub and select `pdf-extraction-website` repo

3. **Configure the service:**
   - **Name:** lilly-pdf-extractor
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT --timeout 300 --workers 2`

4. **Add environment variables:**
   - `PYTHON_VERSION` = `3.11.9`
   - `SECRET_KEY` = (generate a random string)

5. **Click "Create Web Service"**

6. **Wait for deployment** (5-10 minutes first time)

7. **Your app will be live at:** `https://lilly-pdf-extractor.onrender.com`

## Notes:
- Free tier: Service spins down after 15 minutes of inactivity
- First request after spin-down takes ~30 seconds to wake up
- Upgrade to paid tier ($7/month) for always-on service
- SSL certificate included automatically

## Test it:
Once deployed, visit your URL and upload a PDF!
