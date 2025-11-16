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
from dotenv import load_dotenv

from analyzers.cluster_engine import ClusterEngine
from analyzers.draft_validator import DraftValidator

# Load environment variables
load_dotenv()

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

    openai_key = st.text_input(
        "OpenAI API Key",
        value=os.getenv("OPENAI_API_KEY", ""),
        type="password",
        help="Required for generating embeddings (Part 1)"
    )

    google_creds_path = st.text_input(
        "Google Cloud Credentials Path",
        value=os.getenv("GOOGLE_APPLICATION_CREDENTIALS", ""),
        help="Path to your service account JSON file"
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
        help="CSV should have 'keyword' and 'volume' columns",
        key="cluster_csv"
    )

    # Target category input (only for POPULATE mode)
    target_category = None
    if "POPULATE" in mode:
        target_category = st.text_input(
            "Target Category",
            placeholder="/Travel/Family",
            help="The category you want to match (e.g., /Travel/Family)"
        )

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
                df = pd.read_csv(uploaded_file)
                st.success(f"✅ Loaded {len(df)} keywords")

                # Initialize engine
                engine = ClusterEngine(
                    openai_api_key=openai_key,
                    distance_threshold=cluster_threshold
                )

                # Run appropriate mode
                if "DISCOVER" in mode:
                    strategic_brief = engine.run_discover_mode(df, min_volume=min_volume)
                else:
                    strategic_brief = engine.run_populate_mode(
                        df,
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

    target_category_val = st.text_input(
        "Target Category",
        placeholder="/Travel/Family",
        help="The category this content should match",
        key="val_target"
    )

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
    run_validation = st.button("🚀 Validate Draft", type="primary", key="run_validate")

    if run_validation:
        if not draft_text:
            st.error("❌ Please provide draft content")
        elif not target_category_val:
            st.error("❌ Please provide a target category")
        else:
            try:
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
