# AI Small Business Opportunity Finder

A Streamlit web app that uses Google Gemini to suggest 5 realistic small business ideas
based on your budget, location, skills, interests and available time.

Features: idea generator, startup budget analyzer (totals calculated in Python),
market opportunity analyzer, profit and revenue simulator, and a Pakistan market mode.

> The AI output is a set of **assumptions**. No live market research is performed.
> Always check prices and demand locally before investing money.

## Files
- `app.py` - the whole application
- `requirements.txt` - Python packages
- `README.md` - this file

## Step 1: Get a Gemini API key
1. Open https://aistudio.google.com and sign in with your Google account.
2. Click **Get API key** > **Create API key**.
3. Copy the key and keep it private. Never put it inside `app.py`.

## Step 2: Upload the files to GitHub (no coding tools needed)
1. Sign in at https://github.com and click **New repository**.
2. Give it a name, for example `ai-business-opportunity-finder`, choose **Public**, and click **Create repository**.
3. Click **uploading an existing file**.
4. Drag and drop `app.py`, `requirements.txt` and `README.md` into the page.
5. Click **Commit changes**.

## Step 3: Deploy on Streamlit Community Cloud
1. Go to https://share.streamlit.io and sign in with GitHub.
2. Click **Create app** and choose your repository.
3. Set branch to `main` and main file path to `app.py`.
4. Open **Advanced settings** > **Secrets** and paste:
   ```
   GEMINI_API_KEY = "your-key-here"
   ```
5. Click **Deploy** and wait a few minutes. You will get a public link.

## Updating the app later
Open the file on GitHub, click the pencil icon (edit), change it, and click **Commit changes**.
Streamlit redeploys automatically.

## Troubleshooting
- **"Gemini API key not found":** The secret is missing or misspelled. Fix it in the app's **Settings > Secrets**, then reboot the app.
- **404 model not found:** Google retired the model. Edit the `MODEL` line near the top of `app.py`.
- **503 busy:** Google is overloaded. The app retries automatically; wait a minute and try again.
- **429 quota:** The free tier allows about 20 requests per day per model. Wait, use a new key from another Google project, or enable billing.
