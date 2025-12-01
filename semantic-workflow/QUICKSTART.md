# 🚀 QUICKSTART GUIDE

Get up and running in 5 minutes.

## Prerequisites

- Python 3.9+ installed
- OpenAI API key
- Google Cloud service account JSON file with Natural Language API enabled

## Installation

```bash
cd relevance-validation/semantic-workflow

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
```

Edit `.env` with your credentials:
```
OPENAI_API_KEY=sk-your-key-here
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

## Launch

```bash
streamlit run app.py
```

Opens at: http://localhost:8501

## Your First Analysis

### Part 1: DISCOVER Mode (Find Natural Categories)

1. **Prepare your CSV** with these columns:
   ```csv
   keyword,volume
   family vacation,12000
   beach family trip,850
   all inclusive family,2400
   ```

2. In the app:
   - Go to **"Cluster & Define"** tab
   - Select **"DISCOVER - Find Natural Categories"**
   - Upload your CSV
   - Click **"Run Analysis"**

3. Wait for processing (progress bars will show status)

4. **Download strategic_brief.csv** with your cluster analysis

### Part 2: Validate a Draft

1. In the app:
   - Go to **"Validate Draft"** tab
   - Paste your draft content
   - Enter target category (e.g., `/Travel/Family`)
   - (Optional) Upload the strategic_brief.csv from Part 1
   - Click **"Validate Draft"**

2. Review results:
   - ✅ or ❌ for category match
   - Entity list with salience scores
   - Keyword coverage (if brief provided)

## Cost Estimates (for your $1,000 budget)

- **DISCOVER on 50k keywords:** ~$1.30
- **Validate 1 draft (no drag analysis):** ~$0.002
- **Validate 1 draft (WITH drag analysis):** ~$1.25

**With $1,000 you can:**
- Run DISCOVER on 750k+ keywords, OR
- Validate 500,000 drafts (basic), OR
- Validate 80 drafts with full iterative drag analysis

## Quick Tips

1. **Start small** - Test with 1,000 keywords first
2. **Set min volume** - Filter to volume >= 10 to reduce noise
3. **DISCOVER before POPULATE** - Understand your topic space first
4. **Drag analysis is EXPENSIVE** - Only use on critical pages
5. **Save your strategic briefs** - You'll reference them for all drafts

## Troubleshooting

**"No categories detected"**
- Make sure text has 20+ words
- Check keywords are relevant

**"OpenAI API error"**
- Verify API key in .env
- Check you have credits

**"Google auth error"**
- Verify credentials path
- Ensure Natural Language API is enabled

## Next Steps

Read the full [README.md](README.md) for:
- Detailed feature descriptions
- Advanced configuration
- Best practices
- Architecture overview

## Support

Questions? Check the README or open an issue!

**Now go build something amazing!** 🎯
