"""
Semantic Content Workflow
A Streamlit application for keyword clustering, category detection, and content validation.

Two-mode workflow:
1. Cluster & Define: DISCOVER natural categories or POPULATE against targets
2. Validate Draft: QA tool for content validation with iterative optimization
"""

import os
import streamlit as st
import pandas as pd
import json
import tempfile
from dotenv import load_dotenv

from analyzers.cluster_engine import ClusterEngine
from analyzers.draft_validator import DraftValidator
from core.categories import ALL_CATEGORIES

# Load environment variables (for local development)
load_dotenv()

# ============================================================================
# CREDENTIAL HANDLING - Supports both Streamlit Cloud and local development
# ============================================================================

def get_credentials():
    """
    Get API credentials from Streamlit secrets (cloud) or environment variables (local).
    Returns: (openai_key_default, google_creds_path_default)
    """
    openai_key_default = ""
    google_creds_path_default = ""

    # Try Streamlit secrets first (for cloud deployment)
    try:
        if "OPENAI_API_KEY" in st.secrets:
            openai_key_default = st.secrets["OPENAI_API_KEY"]

        # Handle Google credentials JSON from secrets
        if "GOOGLE_APPLICATION_CREDENTIALS_JSON" in st.secrets:
            google_creds_json = st.secrets["GOOGLE_APPLICATION_CREDENTIALS_JSON"]

            # Write JSON to a temporary file
            temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
            json.dump(json.loads(google_creds_json), temp_file)
            temp_file.close()

            google_creds_path_default = temp_file.name
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = temp_file.name
    except Exception:
        # Secrets not available (local development) - use environment variables
        pass

    # Fall back to environment variables if secrets not found
    if not openai_key_default:
        openai_key_default = os.getenv("OPENAI_API_KEY", "")

    if not google_creds_path_default:
        google_creds_path_default = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")

    return openai_key_default, google_creds_path_default

# Get default credentials
openai_key_default, google_creds_path_default = get_credentials()

# Page config
st.set_page_config(
    page_title="Semantic Content Workflow",
    page_icon="🎯",
    layout="wide"
)

# Title
st.title("🎯 Semantic Content Workflow")
st.markdown("*Build smarter content strategies with AI-powered semantic analysis*")

# Sidebar for API credentials
with st.sidebar:
    st.header("⚙️ Configuration")

    # Show credential source info
    if openai_key_default and google_creds_path_default:
        st.success("✅ Credentials loaded from Streamlit secrets")
    elif openai_key_default or google_creds_path_default:
        st.info("🔑 Using credentials from environment/secrets")

    openai_key = st.text_input(
        "OpenAI API Key",
        value=openai_key_default,
        type="password",
        help="Required for generating embeddings (Part 1). Auto-loaded from secrets if configured."
    )

    google_creds_path = st.text_input(
        "Google Cloud Credentials Path",
        value=google_creds_path_default,
        help="Path to your service account JSON file. Auto-loaded from secrets if configured."
    )

    if google_creds_path and os.path.exists(google_creds_path):
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = google_creds_path
        st.success("✅ Google credentials loaded")
    elif google_creds_path:
        st.error("❌ Credentials file not found")

    st.divider()

    st.header("📊 Advanced Settings")

    cluster_threshold = st.slider(
        "Cluster Tightness",
        min_value=0.3,
        max_value=0.7,
        value=0.5,
        step=0.05,
        help="Lower = tighter clusters, Higher = looser clusters"
    )

    min_volume = st.number_input(
        "Minimum Search Volume",
        min_value=0,
        value=10,
        step=10,
        help="Filter out keywords below this volume"
    )

# Main content - Two tabs
tab1, tab2 = st.tabs(["📦 Cluster & Define", "✅ Validate Draft"])

# ============================================================================
# TAB 1: CLUSTER & DEFINE
# ============================================================================

with tab1:
    st.header("Part 1: Cluster & Define Engine")

    st.markdown("""
    **Choose your workflow:**
    - **DISCOVER**: "I have a broad topic; what content spokes should I build?"
    - **POPULATE**: "My IA is set; I need to populate my /Travel/Family hub"
    """)

    # Mode selection
    mode = st.radio(
        "Select Mode:",
        ["DISCOVER - Find Natural Categories", "POPULATE - Match to Target Category"],
        horizontal=True
    )

    # File upload
    uploaded_file = st.file_uploader(
        "Upload Keywords CSV",
        type=['csv'],
        help="Flexible column mapping: works with 'Keyword', 'Query', 'Search Term', etc. and 'Volume', 'MSV', 'Search Volume', etc.",
        key="cluster_csv"
    )

    # Target category input (only for POPULATE mode)
    target_category = None
    if "POPULATE" in mode:
        st.write("**Target Category** (searchable dropdown):")
        target_category = st.selectbox(
            "Select or search for your target category",
            options=[""] + ALL_CATEGORIES,
            help="Start typing to search Google's predefined categories",
            label_visibility="collapsed"
        )
        if not target_category:
            st.info("💡 Start typing in the dropdown to search categories (e.g., 'travel', 'family', etc.)")

    # Run button
    run_cluster = st.button("🚀 Run Analysis", type="primary", key="run_cluster")

    if run_cluster:
        if not openai_key:
            st.error("❌ Please provide OpenAI API key in the sidebar")
        elif not uploaded_file:
            st.error("❌ Please upload a keywords CSV file")
        elif "POPULATE" in mode and not target_category:
            st.error("❌ Please provide a target category for POPULATE mode")
        else:
            try:
                # Load data
                df_raw = pd.read_csv(uploaded_file)
                st.success(f"✅ Loaded {len(df_raw)} rows from CSV")

                # Show column detection preview
                with st.expander("📋 Column Detection Preview", expanded=False):
                    st.write("**Original columns:**", ", ".join(df_raw.columns.tolist()))

                    # Try to detect which columns will be used
                    cols_lower = df_raw.columns.str.lower().str.strip()
                    keyword_candidates = [c for c in df_raw.columns if any(
                        kw in c.lower().replace('_', ' ').replace('-', ' ')
                        for kw in ['keyword', 'query', 'term', 'phrase']
                    )]
                    volume_candidates = [c for c in df_raw.columns if any(
                        v in c.lower().replace('_', ' ').replace('-', ' ')
                        for v in ['volume', 'search', 'msv', 'sv']
                    )]

                    if keyword_candidates:
                        st.write(f"**Keyword column detected:** `{keyword_candidates[0]}`")
                    if volume_candidates:
                        st.write(f"**Volume column detected:** `{volume_candidates[0]}`")

                    st.write("**Sample data:**")
                    st.dataframe(df_raw.head(3), use_container_width=True)

                # Initialize engine
                engine = ClusterEngine(
                    openai_api_key=openai_key,
                    distance_threshold=cluster_threshold
                )

                # Run appropriate mode
                if "DISCOVER" in mode:
                    strategic_brief = engine.run_discover_mode(df_raw, min_volume=min_volume)
                else:
                    strategic_brief = engine.run_populate_mode(
                        df_raw,
                        target_category,
                        min_volume=min_volume
                    )

                # Display results
                st.success("✅ Analysis Complete!")

                # Show summary
                st.subheader("📊 Strategic Brief Summary")
                st.dataframe(strategic_brief, use_container_width=True)

                # Save to session state
                st.session_state['strategic_brief'] = strategic_brief

                # Download buttons
                col1, col2 = st.columns(2)

                with col1:
                    csv = strategic_brief.to_csv(index=False)
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv,
                        file_name="strategic_brief.csv",
                        mime="text/csv"
                    )

                with col2:
                    json = strategic_brief.to_json(orient='records', indent=2)
                    st.download_button(
                        label="📥 Download JSON",
                        data=json,
                        file_name="strategic_brief.json",
                        mime="application/json"
                    )

                # Show opinionated recommendations
                st.subheader("💡 Recommendations")

                for _, row in strategic_brief.head(5).iterrows():
                    with st.expander(f"Cluster: {row['cluster_name']}"):
                        st.write(f"**Hub Keyword:** {row['hub_keyword']}")
                        st.write(f"**Total Keywords:** {row['total_keywords']}")
                        st.write(f"**Total Volume:** {row['total_volume']:,.0f}")
                        st.write(f"**Coherence:** {row['coherence']:.2%}")

                        if "DISCOVER" in mode:
                            st.write(f"**Detected Category:** {row['detected_category']}")
                            st.write(f"**Confidence:** {row['category_confidence']:.2%}")
                        else:
                            matches = row['matches_target']
                            if matches:
                                st.success(f"✅ Matches target: {row['confidence_for_target']:.2%}")
                            else:
                                st.warning(f"❌ Doesn't match. Detected: {row['detected_category']}")

                        st.write(f"**Primary Keywords:** {row['primary_keywords']}")
                        st.write(f"**Top Entities:** {row['top_entities']}")

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.exception(e)

# ============================================================================
# TAB 2: VALIDATE DRAFT
# ============================================================================

with tab2:
    st.header("Part 2: Draft Validator")

    st.markdown("""
    **QA your content against target categories**
    - Check if your draft hits the target category
    - Analyze keyword coverage (if you have a strategic brief)
    - Run iterative drag analysis to find what's pulling category confidence down
    """)

    # Input fields
    draft_text = st.text_area(
        "Draft Content",
        height=300,
        placeholder="Paste your draft content here (text or HTML)...",
        help="Your draft page content (title, meta description, body copy)"
    )

    st.write("**Target Category** (searchable dropdown):")
    target_category_val = st.selectbox(
        "Select or search for your target category",
        options=[""] + ALL_CATEGORIES,
        help="Start typing to search Google's predefined categories",
        label_visibility="collapsed",
        key="val_target"
    )
    if not target_category_val:
        st.info("💡 Start typing in the dropdown to search categories (e.g., 'travel', 'family', etc.)")

    # Optional: Upload strategic brief
    st.subheader("Optional: Keyword Coverage Analysis")

    strategic_brief_file = st.file_uploader(
        "Upload Strategic Brief (from Part 1)",
        type=['csv'],
        help="Optional: Upload the strategic_brief.csv to check keyword coverage",
        key="brief_upload"
    )

    cluster_id_input = None
    if strategic_brief_file:
        strategic_brief_df = pd.read_csv(strategic_brief_file)
        st.success(f"✅ Loaded strategic brief with {len(strategic_brief_df)} clusters")

        # Let user select cluster
        cluster_names = strategic_brief_df['cluster_name'].tolist()
        cluster_ids = strategic_brief_df['cluster_id'].tolist()

        selected_cluster = st.selectbox(
            "Select Cluster to Validate Against",
            options=range(len(cluster_names)),
            format_func=lambda i: f"Cluster {cluster_ids[i]}: {cluster_names[i]}"
        )

        cluster_id_input = cluster_ids[selected_cluster]
    else:
        strategic_brief_df = None

    # Drag analysis option
    run_drag = st.checkbox(
        "🔥 Run Iterative Drag Analysis (expensive!)",
        help="This will make many API calls to find what's dragging your category confidence down"
    )

    # Run validation
    col1, col2 = st.columns([3, 1])
    with col1:
        run_validation = st.button("🚀 Validate Draft", type="primary", key="run_validate")
    with col2:
        if st.button("🔄 Clear Results", key="clear_results"):
            # Clear all session state for validation
            if 'validation_results' in st.session_state:
                del st.session_state['validation_results']
            if 'last_validation_inputs' in st.session_state:
                del st.session_state['last_validation_inputs']
            st.rerun()

    if run_validation:
        if not draft_text:
            st.error("❌ Please provide draft content")
        elif not target_category_val:
            st.error("❌ Please provide a target category")
        else:
            try:
                # Clear any previous results to force fresh display
                if 'validation_results' in st.session_state:
                    del st.session_state['validation_results']

                # Create unique key based on inputs to ensure fresh analysis
                import hashlib
                input_hash = hashlib.md5(
                    f"{draft_text}{target_category_val}{cluster_id_input}{run_drag}".encode()
                ).hexdigest()

                # Store current inputs to detect changes
                current_inputs = {
                    'text_hash': input_hash,
                    'category': target_category_val,
                    'cluster': cluster_id_input
                }

                # Only run if inputs changed
                last_inputs = st.session_state.get('last_validation_inputs', {})
                if last_inputs.get('text_hash') == input_hash:
                    st.info("💡 Same inputs detected. If results look wrong, click 'Clear Results' and try again.")

                st.session_state['last_validation_inputs'] = current_inputs

                validator = DraftValidator()

                results = validator.validate_draft(
                    draft_text=draft_text,
                    target_category=target_category_val,
                    strategic_brief_df=strategic_brief_df,
                    cluster_id=cluster_id_input,
                    run_drag_analysis=run_drag
                )

                # Results are displayed within the validate_draft method
                st.success("✅ Validation Complete!")

                # Save results to session state
                st.session_state['validation_results'] = results

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.exception(e)

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>Built with ❤️ using Streamlit, OpenAI, and Google Cloud Natural Language API</p>
    <p><small>Semantic Content Workflow v1.0</small></p>
</div>
""", unsafe_allow_html=True)
