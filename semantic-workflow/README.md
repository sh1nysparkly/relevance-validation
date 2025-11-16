# 🎯 Semantic Content Workflow

A powerful Streamlit application for building smarter content strategies through AI-powered semantic analysis.

## What This Does

This tool helps you:
1. **Cluster keywords semantically** - Group related keywords using OpenAI embeddings
2. **Detect natural categories** - Let Google NLP tell you what topics emerge from your keyword clusters
3. **Validate content against targets** - QA your drafts to ensure they hit the right topical categories
4. **Optimize content iteratively** - Find which terms are "dragging" your category confidence down

## The Factory: Two-Part Workflow

### Part 1: Cluster & Define Engine

**Two modes to solve the "chicken-and-egg" problem:**

#### DISCOVER Mode
*"I have a broad topic; what content spokes should I build?"*

- Upload your keywords CSV (10k-50k keywords supported)
- The tool clusters them semantically
- For each cluster, it detects the **natural category** Google NLP identifies
- Outputs a strategic brief with hub keywords, category confidence, and top entities

**Use this when:** You're exploring a topic space and want data-driven insights on what content to create.

#### POPULATE Mode
*"My IA is set; I need to populate my /Travel/Family hub"*

- Upload keywords CSV + provide your target category (e.g., `/Travel/Family`)
- The tool clusters keywords AND tests each cluster against your target
- Identifies which clusters match your target and which don't
- Outputs match confidence scores to help you prioritize

**Use this when:** You have a defined content structure and need to assign keywords strategically.

**Features:**
- Cannibalization detection (flags clusters with >80% overlap)
- Opinionated recommendations (tells you which keyword to use as H1 vs body copy)
- CSV + JSON export for downstream use

---

### Part 2: Validate Draft

**Your QA tool for content validation**

**Inputs:**
- Draft content (paste text/HTML)
- Target category
- Optional: Strategic brief from Part 1 (for keyword coverage analysis)

**Features:**

1. **Category Detection**
   - Tests if your draft hits the target category
   - Shows detected category + confidence score
   - Lists all categories detected (top 5)

2. **Entity Analysis**
   - Extracts key entities with salience scores
   - Links to Wikipedia where available
   - Helps you understand what topical signals your content is sending

3. **Keyword Coverage Score** (if brief provided)
   - Checks which primary/secondary/tertiary keywords are present
   - Flags missing keywords
   - Provides actionable recommendations

4. **Iterative Drag Analysis** 🔥 (THE $1,000 FEATURE)
   - Remove-and-test approach to find "drag" terms
   - Locks in wins progressively
   - Shows you exactly which terms to remove for maximum category confidence
   - **WARNING:** This makes MANY API calls (expensive!)

---

## Installation

### Prerequisites

- Python 3.9+
- OpenAI API key (for embeddings)
- Google Cloud service account with Natural Language API enabled

### Setup

1. **Clone the repository**
```bash
cd relevance-validation/semantic-workflow
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment**

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env`:
```
OPENAI_API_KEY=your_openai_key_here
GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/service-account-key.json
```

4. **Run the app**
```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

---

## Usage Guide

### Part 1: Cluster & Define

#### Input Format

Your CSV should have these columns:
- `keyword` (required): The keyword text
- `volume` (optional): Monthly search volume

Example:
```csv
keyword,volume
family vacation,12000
family beach vacation,850
all inclusive family resort,2400
```

#### Workflow

1. **Choose your mode:** DISCOVER or POPULATE
2. **Upload CSV:** Drag and drop your keywords file
3. **(POPULATE only)** Enter target category like `/Travel/Family`
4. **Adjust settings** in the sidebar:
   - Cluster tightness (0.3 = tight, 0.7 = loose)
   - Minimum search volume filter
5. **Click "Run Analysis"**
6. **Review results:**
   - Strategic brief table with all clusters
   - Cannibalization warnings
   - Opinionated recommendations
7. **Download outputs:** CSV or JSON

#### Output Columns

- `cluster_id`: Numeric cluster identifier
- `cluster_name`: Hub keyword (most representative)
- `hub_keyword`: Same as cluster_name
- `total_keywords`: Count of keywords in cluster
- `total_volume`: Sum of search volume
- `coherence`: How tight the cluster is (0-1)
- `primary_keywords`: Top keywords for H1/title
- `secondary_keywords`: Supporting keywords
- `tertiary_keywords`: Count of additional keywords
- `detected_category`: What Google NLP detected (DISCOVER mode)
- `category_confidence`: Confidence score
- `matches_target`: True/False (POPULATE mode)
- `top_entities`: Key entities extracted

---

### Part 2: Validate Draft

#### Workflow

1. **Paste your draft** in the text area
2. **Enter target category** (e.g., `/Travel/Family`)
3. **(Optional)** Upload strategic brief CSV
   - If uploaded, select which cluster to validate against
4. **(Optional)** Check "Run Iterative Drag Analysis"
   - ⚠️ This is expensive! Only use when optimizing critical content
5. **Click "Validate Draft"**
6. **Review results:**
   - Category match: ✅ or ❌
   - Entity list with salience scores
   - Keyword coverage (if brief provided)
   - Drag analysis recommendations (if requested)

#### Understanding Drag Analysis

The iterative drag analyzer:
1. Tests your full draft → gets baseline confidence
2. Systematically removes each entity/keyword
3. Finds which removal gives the BIGGEST confidence boost
4. Locks in that win and repeats on the new baseline
5. Continues until no more improvements found

**Example output:**
```
Baseline Confidence: 27.1%

Optimization Steps:
1. Remove "cooking class" → 27.1% → 32.4% (+5.3%)
2. Remove "culinary tours" → 32.4% → 36.1% (+3.7%)

Recommendation:
Remove these terms:
- ❌ cooking class
- ❌ culinary tours

Potential Final Confidence: 36.1%
```

---

## Advanced Configuration

### Clustering Parameters

In the sidebar, you can adjust:

- **Cluster Tightness (0.3-0.7)**
  - 0.3-0.4: Tight clusters (very similar keywords)
  - 0.5: Balanced (default)
  - 0.6-0.7: Loose clusters (broader semantic groupings)

- **Minimum Search Volume**
  - Filter out low-volume keywords
  - Recommended: 10-50 for most use cases

### Rate Limiting

The tool includes automatic rate limiting for API calls. For very large datasets (50k+ keywords):

- OpenAI embeddings: Batched at 100 per request
- Google NLP: 0.05s delay between calls in drag analysis
- Progress bars show real-time status

---

## Cost Estimation

### OpenAI (Embeddings)
- Model: `text-embedding-3-small`
- Cost: ~$0.00002 per 1k tokens
- 10k keywords ≈ $0.20
- 50k keywords ≈ $1.00

### Google NLP (Category Detection + Entity Analysis)
- Cost: $1.00 per 1k requests (first 5k free per month)
- 100 clusters × 1 test = $0.10
- Drag analysis with 50 entities = 50+ requests = $0.05

### Iterative Drag Analysis (The Expensive One)
- If draft has 50 entities
- Max iterations: 50
- Each iteration tests all remaining entities
- Worst case: ~1,250 API calls = **$1.25** per draft

**Budget guidance for $1,000 in credits:**
- DISCOVER mode on 50k keywords: ~$1.20
- POPULATE mode on 50k keywords: ~$1.30
- Validate 10 drafts (with drag analysis): ~$12.50
- **You can validate ~80 drafts with full drag analysis** before hitting $1,000

---

## Troubleshooting

### "No categories detected"
- Google NLP requires at least 20 words
- Make sure your draft has enough content
- Check that keywords are relevant (not just entity names)

### "Embedding generation failed"
- Check your OpenAI API key
- Verify you have available credits
- Try reducing batch size (edit `core/embeddings.py`)

### "Google Cloud authentication error"
- Verify your service account JSON path is correct
- Ensure Natural Language API is enabled in Google Cloud Console
- Check that credentials file has proper permissions

### Slow performance
- Large datasets (50k+ keywords) take time
- Disable drag analysis for faster validation
- Increase minimum volume threshold to reduce keyword count

---

## Tips & Best Practices

### For Part 1 (Clustering)

1. **Start with DISCOVER** to understand your topic space
2. **Review cannibalization warnings** - merge similar clusters
3. **Trust the coherence score** - low coherence = loose cluster, consider splitting
4. **Use hub_keyword for page titles/H1s** - it's the most representative
5. **POPULATE mode works best with specific targets** like `/Travel/Cruises`, not just `/Travel`

### For Part 2 (Validation)

1. **Run without drag analysis first** - see if you're close to target
2. **Only use drag analysis when optimizing critical pages** - it's expensive
3. **Don't blindly follow drag recommendations** - removing all entities can make content thin
4. **Keep at least 5-10 primary keywords** even if drag analysis suggests removal
5. **Use entity Wikipedia links** to enrich your content with authoritative sources

### General Workflow

**The Factory Process:**
1. Run DISCOVER on your full keyword set → export strategic brief
2. Review clusters, merge/split as needed
3. For each cluster, write draft content
4. Validate each draft in Part 2
5. Iterate based on coverage scores and category matches
6. (Optional) Run drag analysis on top-priority pages
7. Publish optimized content 🚀

---

## Architecture

```
semantic-workflow/
├── core/                    # Core modules
│   ├── embeddings.py       # OpenAI embedding generation
│   ├── nlp_analysis.py     # Google NLP API wrapper
│   ├── clustering.py       # Keyword clustering logic
│   └── utils.py            # Helper functions
├── analyzers/              # High-level analyzers
│   ├── cluster_engine.py   # Part 1: Cluster & Define
│   └── draft_validator.py  # Part 2: Validate Draft
├── app.py                  # Main Streamlit application
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variable template
└── README.md              # This file
```

---

## Credits

Built with:
- [Streamlit](https://streamlit.io/) - Web interface
- [OpenAI API](https://openai.com/api/) - Embeddings
- [Google Cloud Natural Language API](https://cloud.google.com/natural-language) - Category detection & entity extraction
- [scikit-learn](https://scikit-learn.org/) - Clustering algorithms

---

## License

MIT License - use freely for your content strategy needs!

---

## Support

For questions, issues, or feature requests, please open an issue in the repository.

**Happy semantic analysis!** 🎯
