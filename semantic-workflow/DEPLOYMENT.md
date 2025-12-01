# How to deploy your Streamlit app to the cloud

## Option 1: Streamlit Community Cloud (Recommended - FREE!)

### Prerequisites
- GitHub account (you already have this!)
- Your code is pushed to GitHub (done!)

### Steps

1. **Go to [share.streamlit.io](https://share.streamlit.io)**

2. **Sign in with GitHub**

3. **Click "New app"**

4. **Configure your app:**
   - Repository: `sh1nysparkly/relevance-validation`
   - Branch: `claude/consolidate-nlp-scripts-01MLTZjaBXk5QYaqeBUhXjGS` (or merge to main first)
   - Main file path: `semantic-workflow/app.py`

5. **Set up your secrets** (this is CRITICAL!):
   - Click "Advanced settings" button
   - In the "Secrets" section, paste your credentials
   - See `.streamlit/secrets.toml.example` for the full template
   - You need TWO secrets:

   **OpenAI API Key** (for keyword clustering):
   ```toml
   OPENAI_API_KEY = "sk-your-actual-key-here"
   ```

   **Google Cloud Service Account** (for NLP analysis):
   ```toml
   GOOGLE_APPLICATION_CREDENTIALS_JSON = '''
   {
     "type": "service_account",
     "project_id": "your-project-id",
     "private_key_id": "abc123...",
     "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
     "client_email": "your-service-account@your-project.iam.gserviceaccount.com",
     "client_id": "123456789",
     "auth_uri": "https://accounts.google.com/o/oauth2/auth",
     "token_uri": "https://oauth2.googleapis.com/token",
     "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
     "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/..."
   }
   '''
   ```

   **Important**: Copy your ENTIRE service account JSON file content (the one you downloaded from Google Cloud Console)

6. **Click "Deploy"**

7. **Wait 2-3 minutes** - Streamlit will build and deploy your app

8. **Get your URL**: `https://your-app-name.streamlit.app`

### App is now ready for deployment!

The app has been updated to support both Streamlit Cloud secrets and local environment variables. You can now deploy directly to Streamlit Cloud.

---

## Option 2: Docker + Cloud Run (More Control)

If you want more control or need to scale:

1. I'll create a Dockerfile
2. Deploy to Google Cloud Run or AWS Fargate
3. More complex but more flexible

---

## Option 3: Hugging Face Spaces (Also Free!)

Another easy option:
1. Create a Hugging Face account
2. Create a new "Space" with Streamlit template
3. Push your code
4. Add secrets in the Space settings

---

**Which option do you want? Streamlit Cloud is easiest and perfect for sharing with colleagues!**

Want me to:
1. Update the app to work with Streamlit Cloud secrets? (5 min)
2. Create Docker deployment files? (15 min)
3. Walk you through the Streamlit Cloud deployment step-by-step?
