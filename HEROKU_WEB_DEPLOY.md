# Deploy to Heroku Without CLI (Web Dashboard Method)

## Prerequisites
- A Heroku account (sign up at https://signup.heroku.com/)
- Git installed on your computer
- Your code pushed to GitHub

## Step 1: Push Your Code to GitHub

1. Initialize git repository (if not already done):
```powershell
cd "C:\Users\L108094\Desktop\Hackathon\pdf-extraction-website"
git init
git add .
git commit -m "Initial commit for Heroku deployment"
```

2. Create a new repository on GitHub:
   - Go to https://github.com/new
   - Name it `lilly-pdf-extractor` (or any name you prefer)
   - Don't initialize with README (since you already have code)
   - Click "Create repository"

3. Push your code to GitHub:
```powershell
git remote add origin https://github.com/YOUR_USERNAME/lilly-pdf-extractor.git
git branch -M master
git push -u origin master
```

## Step 2: Create Heroku App via Web Dashboard

1. Go to https://dashboard.heroku.com/
2. Click "New" → "Create new app"
3. Enter app name: `lilly-pdf-extractor` (or your preferred name)
4. Choose region (United States or Europe)
5. Click "Create app"

## Step 3: Connect to GitHub

1. In your new Heroku app dashboard, go to the "Deploy" tab
2. Under "Deployment method", click "GitHub"
3. Click "Connect to GitHub" and authorize Heroku
4. Search for your repository: `lilly-pdf-extractor`
5. Click "Connect" next to your repository

## Step 4: Add Buildpacks

1. Go to the "Settings" tab
2. Scroll to "Buildpacks" section
3. Click "Add buildpack"
4. Enter: `https://github.com/heroku/heroku-buildpack-apt`
5. Click "Save changes"
6. Click "Add buildpack" again
7. Select "python" from the official buildpacks
8. Click "Save changes"
9. **IMPORTANT**: Drag the apt buildpack to be FIRST (above python)

## Step 5: Deploy

1. Go back to the "Deploy" tab
2. Scroll to "Manual deploy" section
3. Select the branch: `master`
4. Click "Deploy Branch"
5. Wait for the build to complete (this may take 5-10 minutes)

## Step 6: Upgrade to Hobby Dyno (REQUIRED)

⚠️ **CRITICAL**: The free tier will crash due to memory requirements (EasyOCR needs >512MB)

1. Go to the "Resources" tab
2. Click "Change Dyno Type"
3. Select "Hobby" ($7/month)
4. Click "Save"
5. Make sure the dyno is toggled ON (purple switch)

## Step 7: View Your App

1. Click "Open app" button at top right
2. Your app should open at: `https://lilly-pdf-extractor.herokuapp.com`

## Step 8: Enable Automatic Deploys (Optional)

1. Go to "Deploy" tab
2. Under "Automatic deploys", select your branch
3. Click "Enable Automatic Deploys"
4. Now every push to GitHub will auto-deploy

## Monitoring

View logs in real-time:
1. Go to "More" → "View logs" in top right
2. Or go to: https://dashboard.heroku.com/apps/YOUR_APP_NAME/logs

## Troubleshooting

### If build fails:
1. Check logs under "More" → "View logs"
2. Verify buildpacks are in correct order (apt first, python second)
3. Ensure all required files exist: `requirements.txt`, `Procfile`, `Aptfile`, `runtime.txt`

### If app crashes (R14 memory errors):
1. Upgrade to Standard-2X dyno ($50/month) for 1GB RAM
2. Go to Resources → Change Dyno Type → Standard-2X

### If app shows "Application Error":
1. Check you're using Hobby or higher dyno (not Free)
2. View logs to see the error
3. Ensure PORT environment variable is being read correctly

## Cost Summary

- **Free Tier**: ❌ Will crash (insufficient memory)
- **Hobby**: ✅ $7/month (1GB RAM) - Minimum viable
- **Standard-1X**: $25/month (512MB RAM) - May still have memory issues
- **Standard-2X**: ✅ $50/month (1GB RAM) - Recommended for production

## Alternative: Manual Git Deploy (Without GitHub)

If you don't want to use GitHub:

1. Install Git: https://git-scm.com/download/win
2. Install Heroku CLI anyway (it's the easiest for git-based deploys)
3. Or use Heroku's direct Git URL provided in the dashboard

The GitHub method is recommended as it's the easiest without CLI and provides automatic deploys.
