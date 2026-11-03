# AI Small Business Opportunity Finder

A Streamlit app that uses Google Gemini to suggest 5 realistic small business ideas
based on your budget, location, skills, interests and time. It includes a budget
analyzer, a market analysis, and a profit simulator.

> AI output is a set of **assumptions**, not verified market research. Always check
> prices and demand locally before investing money.

## Run locally (Windows + VS Code)
1. Get a free API key from https://aistudio.google.com
2. Create the file `.streamlit/secrets.toml` and add:
   ```
   GEMINI_API_KEY = "your-key-here"
   ```
3. In the VS Code terminal:
   ```
   pip install -r requirements.txt
   streamlit run app.py
   ```

## Deploy
1. Push the 3 files to a GitHub repository (do NOT upload `secrets.toml`).
2. On https://share.streamlit.io click **New app** and choose your repo and `app.py`.
3. Open **Settings > Secrets** and paste `GEMINI_API_KEY = "your-key-here"`.
