"""
Part 2: Draft Validator
QA tool for validating content drafts against target categories with iterative optimization.
"""

import pandas as pd
from typing import Dict, Optional
import streamlit as st

from core.nlp_analysis import NLPAnalyzer
from core.utils import calculate_keyword_coverage


class DraftValidator:
    """
    Validates draft content against target categories.
    Includes keyword coverage scoring and iterative drag analysis.
    """

    def __init__(self):
        self.nlp_analyzer = NLPAnalyzer()

    def validate_draft(
        self,
        draft_text: str,
        target_category: str,
        strategic_brief_df: Optional[pd.DataFrame] = None,
        cluster_id: Optional[int] = None,
        run_drag_analysis: bool = False
    ) -> Dict:
        """
        Validate a draft against a target category.

        Args:
            draft_text: The draft content to validate
            target_category: Target category (e.g., "/Travel/Family")
            strategic_brief_df: Optional strategic brief from Part 1
            cluster_id: Optional cluster ID to pull keywords from brief
            run_drag_analysis: Whether to run expensive iterative drag analysis

        Returns:
            Dict with validation results
        """
        st.header("📋 Draft Validation Report")

        results = {
            'target_category': target_category,
            'draft_length': len(draft_text),
            'word_count': len(draft_text.split())
        }

        # Step 1: Basic category detection
        st.subheader("Step 1: Category Detection")
        match_result = self.nlp_analyzer.test_category_match(draft_text, target_category)

        results['matches_target'] = match_result['matches_target']
        results['detected_category'] = match_result['detected_category']
        results['confidence'] = match_result['confidence']
        results['matched_category'] = match_result.get('matched_category')

        # Display results
        if match_result['matches_target']:
            st.success(f"✅ Draft matches target category!")
            st.write(f"**Matched:** {match_result['matched_category']}")
            st.write(f"**Confidence:** {match_result['confidence']:.2%}")
        else:
            st.warning(f"❌ Draft does NOT match target category")
            st.write(f"**Target:** {target_category}")
            st.write(f"**Detected:** {match_result['detected_category']}")
            st.write(f"**Confidence:** {match_result['confidence']:.2%}")

        # Show all categories
        with st.expander("View All Detected Categories"):
            for cat in match_result['all_categories']:
                st.write(f"- {cat['name']} ({cat['confidence']:.2%})")

        # Step 2: Entity analysis
        st.subheader("Step 2: Entity Analysis")
        entity_result = self.nlp_analyzer.analyze_text(
            draft_text,
            extract_entities=True,
            classify_content=False
        )

        results['entities'] = entity_result['entities']

        if entity_result['entities']:
            st.write("**Top Entities (by salience):**")
            for entity in entity_result['entities'][:10]:
                wiki_link = f" ([Wikipedia]({entity['wikipedia_url']}))" if entity['wikipedia_url'] else ""
                st.write(f"- **{entity['name']}** (salience: {entity['salience']:.3f}, type: {entity['type']}){wiki_link}")
        else:
            st.info("No entities detected")

        # Step 3: Keyword coverage (if brief provided)
        if strategic_brief_df is not None and cluster_id is not None:
            st.subheader("Step 3: Keyword Coverage Analysis")
            coverage = self._analyze_keyword_coverage(
                draft_text,
                strategic_brief_df,
                cluster_id
            )
            results['keyword_coverage'] = coverage

        # Step 4: Iterative Drag Analysis (if requested)
        if run_drag_analysis:
            st.subheader("Step 4: Iterative Drag Analysis (Optimization)")
            st.warning("⚠️ This is an expensive operation - it will make many API calls!")

            with st.spinner("Running iterative drag analysis..."):
                drag_results = self.nlp_analyzer.iterative_drag_analysis(
                    text=draft_text,
                    target_category=target_category,
                    entities_to_test=[e['name'] for e in entity_result['entities']],
                    show_progress=True
                )

            results['drag_analysis'] = drag_results
            self._display_drag_analysis(drag_results)

        return results

    def _analyze_keyword_coverage(
        self,
        draft_text: str,
        strategic_brief_df: pd.DataFrame,
        cluster_id: int
    ) -> Dict:
        """
        Analyze keyword coverage from strategic brief.

        Args:
            draft_text: Draft content
            strategic_brief_df: Strategic brief DataFrame
            cluster_id: Cluster ID to analyze

        Returns:
            Dict with coverage analysis
        """
        # Find cluster in brief
        cluster_row = strategic_brief_df[strategic_brief_df['cluster_id'] == cluster_id]

        if cluster_row.empty:
            st.error(f"Cluster ID {cluster_id} not found in strategic brief")
            return {}

        cluster_row = cluster_row.iloc[0]

        # Extract keywords
        primary = [k.strip() for k in str(cluster_row.get('primary_keywords', '')).split(',') if k.strip()]
        secondary = [k.strip() for k in str(cluster_row.get('secondary_keywords', '')).split(',') if k.strip()]
        tertiary = []  # Not storing full list in CSV

        coverage = calculate_keyword_coverage(
            draft_text,
            primary,
            secondary,
            tertiary
        )

        # Display coverage
        st.write("**Keyword Coverage:**")

        primary_pct = coverage['primary']['percentage']
        primary_status = "✅" if primary_pct >= 0.80 else "⚠️" if primary_pct >= 0.60 else "❌"
        st.write(f"{primary_status} **Primary:** {primary_pct:.0%} ({coverage['primary']['found']}/{coverage['primary']['total']})")

        if coverage['primary']['missing']:
            with st.expander("Missing Primary Keywords"):
                for kw in coverage['primary']['missing']:
                    st.write(f"- {kw}")

        secondary_pct = coverage['secondary']['percentage']
        secondary_status = "✅" if secondary_pct >= 0.60 else "⚠️" if secondary_pct >= 0.40 else "❌"
        st.write(f"{secondary_status} **Secondary:** {secondary_pct:.0%} ({coverage['secondary']['found']}/{coverage['secondary']['total']})")

        if coverage['secondary']['missing']:
            with st.expander("Missing Secondary Keywords"):
                for kw in coverage['secondary']['missing'][:10]:
                    st.write(f"- {kw}")

        return coverage

    def _display_drag_analysis(self, drag_results: Dict):
        """
        Display results of iterative drag analysis.

        Args:
            drag_results: Results from iterative_drag_analysis
        """
        if drag_results.get('error'):
            st.error(f"Error: {drag_results['error']}")
            return

        baseline = drag_results['baseline_confidence']
        final = drag_results['final_confidence']
        improvement = drag_results['total_improvement']

        st.write(f"**Baseline Confidence:** {baseline:.2%}")
        st.write(f"**Final Confidence:** {final:.2%}")

        if improvement > 0:
            st.success(f"**Total Improvement:** +{improvement:.2%}")
        else:
            st.info("No improvements found - your draft is already optimized!")
            return

        # Show iterations
        iterations = drag_results['iterations']

        if iterations:
            st.write(f"\n**Optimization Steps ({len(iterations)} iterations):**")

            for it in iterations:
                improvement_pct = it['improvement']
                st.write(
                    f"{it['iteration']}. Remove **'{it['removed']}'** → "
                    f"{it['old_confidence']:.2%} → {it['new_confidence']:.2%} "
                    f"(+{improvement_pct:.2%})"
                )

            # Final recommendation
            st.write("\n**📋 Recommendation:**")
            removed_terms = drag_results['removed_terms']

            st.write("Remove these terms from your draft:")
            for term in removed_terms:
                st.write(f"- ❌ **{term}**")

            st.write(f"\n**Potential Final Confidence:** {final:.2%}")

            # Warning if too many removals
            if len(removed_terms) > len(iterations) * 0.5:
                st.warning(
                    "⚠️ You're removing a lot of terms. Make sure your draft still has "
                    "enough substance and doesn't lose important context."
                )
