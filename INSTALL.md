# QUICK START GUIDE

## Step 1: Install Python

Since Python is not currently installed on this system, you need to install it first:

### Option A: Install from Python.org (Recommended)

1. Go to https://python.org/downloads/
2. Download Python 3.11 or later
3. **IMPORTANT**: During installation, check "Add Python to PATH"
4. Complete the installation

### Option B: Install from Microsoft Store

1. Open Microsoft Store
2. Search for "Python"
3. Install "Python 3.11" or later

## Step 2: Setup the Application

After Python is installed:

1. Open a new Command Prompt or PowerShell
2. Navigate to this folder
3. Run: `setup.bat`

## Step 3: Run the Application

1. Run: `start_server.bat`
2. Open your browser to: http://localhost:5000

## Alternative: Direct Installation (if you have Python)

If Python is already installed, you can run these commands directly:

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

## Testing Without Web Interface

If you want to test the PDF extraction directly:

1. Place your PDF file in this folder
2. Edit `example_usage.py` to point to your PDF file
3. Run: `python example_usage.py`

## Troubleshooting

- If you get "python not found" errors, Python is not in your PATH
- Restart your command prompt after installing Python
- Make sure you checked "Add Python to PATH" during installation
