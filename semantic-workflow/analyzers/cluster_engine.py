"""
Part 1: Cluster & Define Engine
Handles both DISCOVER and POPULATE modes for keyword clustering and category detection.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import streamlit as st

from core.embeddings import EmbeddingGenerator
from core.clustering import KeywordClusterer
from core.nlp_analysis import NLPAnalyzer
from core.utils import validate_keywords_csv


class ClusterEngine:
    """
    Main engine for clustering keywords and detecting/validating categories.
    Supports two modes: DISCOVER (find natural categories) and POPULATE (match to target).
    """

    def __init__(
        self,
        openai_api_key: str,
        distance_threshold: float = 0.5
    ):
        self.embedding_gen = EmbeddingGenerator(openai_api_key)
        self.clusterer = KeywordClusterer(distance_threshold)
        self.nlp_analyzer = NLPAnalyzer()

    def run_discover_mode(
        self,
        df: pd.DataFrame,
        min_volume: int = 10
    ) -> pd.DataFrame:
        """
        DISCOVER MODE: Find natural categories for keyword clusters.

        Args:
            df: DataFrame with 'keyword' and 'volume' columns
            min_volume: Minimum search volume threshold

        Returns:
            DataFrame with cluster analysis and detected categories
        """
        st.header("🔍 DISCOVER MODE: Finding Natural Categories")

        # Validate and clean data
        df = validate_keywords_csv(df)

        # Filter by volume
        if min_volume > 0:
            df_filtered = df[df['volume'] >= min_volume].copy()
            st.info(f"Filtered to {len(df_filtered)} keywords (volume >= {min_volume})")
        else:
            df_filtered = df.copy()

        # Generate embeddings
        st.subheader("Step 1: Generating Embeddings")
        keywords_list = df_filtered['keyword'].tolist()
        embeddings = self.embedding_gen.get_embeddings_batch(keywords_list)
        df_filtered['embedding'] = embeddings

        # Cluster keywords
        st.subheader("Step 2: Clustering Keywords")
        df_filtered = self.clusterer.cluster_keywords(df_filtered, embeddings)

        # Analyze clusters
        st.subheader("Step 3: Analyzing Clusters")
        cluster_analyses = self.clusterer.analyze_all_clusters(df_filtered, embeddings)

        # Detect natural categories for each cluster
        st.subheader("Step 4: Detecting Natural Categories")
        strategic_brief = self._detect_cluster_categories(df_filtered, cluster_analyses)

        # Detect cannibalization
        st.subheader("Step 5: Detecting Cannibalization")
        cannibalization = self.clusterer.detect_cannibalization(df_filtered, embeddings)

        if cannibalization:
            st.warning(f"⚠️ Found {len(cannibalization)} potential cannibalization pairs")
            for cluster_a, cluster_b, similarity in cannibalization:
                hub_a = cluster_analyses[cluster_a]['hub_keyword']
                hub_b = cluster_analyses[cluster_b]['hub_keyword']
                st.write(f"- Cluster '{hub_a}' ↔ '{hub_b}' (similarity: {similarity:.2%}) → Consider merging")
        else:
            st.success("✅ No cannibalization detected")

        return strategic_brief

    def run_populate_mode(
        self,
        df: pd.DataFrame,
        target_category: str,
        min_volume: int = 10
    ) -> pd.DataFrame:
        """
        POPULATE MODE: Match clusters to a target category.

        Args:
            df: DataFrame with 'keyword' and 'volume' columns
            target_category: Target category to match (e.g., "/Travel/Family")
            min_volume: Minimum search volume threshold

        Returns:
            DataFrame with cluster analysis and target matching
        """
        st.header(f"🎯 POPULATE MODE: Matching to '{target_category}'")

        # Validate and clean data
        df = validate_keywords_csv(df)

        # Filter by volume
        if min_volume > 0:
            df_filtered = df[df['volume'] >= min_volume].copy()
            st.info(f"Filtered to {len(df_filtered)} keywords (volume >= {min_volume})")
        else:
            df_filtered = df.copy()

        # Generate embeddings
        st.subheader("Step 1: Generating Embeddings")
        keywords_list = df_filtered['keyword'].tolist()
        embeddings = self.embedding_gen.get_embeddings_batch(keywords_list)
        df_filtered['embedding'] = embeddings

        # Cluster keywords
        st.subheader("Step 2: Clustering Keywords")
        df_filtered = self.clusterer.cluster_keywords(df_filtered, embeddings)

        # Analyze clusters
        st.subheader("Step 3: Analyzing Clusters")
        cluster_analyses = self.clusterer.analyze_all_clusters(df_filtered, embeddings)

        # Test clusters against target category
        st.subheader(f"Step 4: Testing Against Target '{target_category}'")
        strategic_brief = self._test_cluster_targets(df_filtered, cluster_analyses, target_category)

        return strategic_brief

    def _detect_cluster_categories(
        self,
        df: pd.DataFrame,
        cluster_analyses: Dict[int, Dict]
    ) -> pd.DataFrame:
        """
        Detect natural categories for each cluster.

        Args:
            df: DataFrame with cluster assignments
            cluster_analyses: Dict of cluster analyses

        Returns:
            DataFrame with strategic brief
        """
        brief_data = []

        cluster_ids = sorted(cluster_analyses.keys())
        progress_bar = st.progress(0)
        status_text = st.empty()

        for idx, cluster_id in enumerate(cluster_ids):
            progress = (idx + 1) / len(cluster_ids)
            progress_bar.progress(progress)

            analysis = cluster_analyses[cluster_id]
            hub_keyword = analysis['hub_keyword']

            status_text.text(f"Testing cluster {idx + 1}/{len(cluster_ids)}: '{hub_keyword}'")

            # Combine all keywords in cluster
            cluster_keywords = analysis['primary'] + analysis['secondary'] + analysis['tertiary']
            combined_text = ' '.join(cluster_keywords)

            # Analyze with Google NLP
            result = self.nlp_analyzer.analyze_text(combined_text)

            detected_category = None
            category_confidence = 0.0
            top_entities = []

            if result['categories']:
                detected_category = result['categories'][0]['name']
                category_confidence = result['categories'][0]['confidence']

            if result['entities']:
                top_entities = [e['name'] for e in result['entities'][:5]]

            brief_data.append({
                'cluster_id': cluster_id,
                'cluster_name': hub_keyword,
                'hub_keyword': hub_keyword,
                'total_keywords': analysis['total_keywords'],
                'total_volume': analysis['total_volume'],
                'coherence': analysis['coherence'],
                'primary_keywords': ', '.join(analysis['primary']),
                'secondary_keywords': ', '.join(analysis['secondary'][:5]),  # Top 5 for display
                'tertiary_keywords': f"{len(analysis['tertiary'])} additional",
                'detected_category': detected_category,
                'category_confidence': category_confidence,
                'top_entities': ', '.join(top_entities)
            })

        progress_bar.progress(1.0)
        status_text.text(f"✅ Analyzed {len(cluster_ids)} clusters")

        return pd.DataFrame(brief_data)

    def _test_cluster_targets(
        self,
        df: pd.DataFrame,
        cluster_analyses: Dict[int, Dict],
        target_category: str
    ) -> pd.DataFrame:
        """
        Test clusters against a target category.

        Args:
            df: DataFrame with cluster assignments
            cluster_analyses: Dict of cluster analyses
            target_category: Target category to test against

        Returns:
            DataFrame with strategic brief including target matching
        """
        brief_data = []

        cluster_ids = sorted(cluster_analyses.keys())
        progress_bar = st.progress(0)
        status_text = st.empty()

        for idx, cluster_id in enumerate(cluster_ids):
            progress = (idx + 1) / len(cluster_ids)
            progress_bar.progress(progress)

            analysis = cluster_analyses[cluster_id]
            hub_keyword = analysis['hub_keyword']

            status_text.text(f"Testing cluster {idx + 1}/{len(cluster_ids)}: '{hub_keyword}'")

            # Combine all keywords in cluster
            cluster_keywords = analysis['primary'] + analysis['secondary'] + analysis['tertiary']
            combined_text = ' '.join(cluster_keywords)

            # Test against target category
            result = self.nlp_analyzer.test_category_match(combined_text, target_category)

            matches_target = result['matches_target']
            detected_category = result['detected_category']
            confidence = result['confidence']

            # Also get entities
            entity_result = self.nlp_analyzer.analyze_text(combined_text, extract_entities=True, classify_content=False)
            top_entities = [e['name'] for e in entity_result['entities'][:5]] if entity_result['entities'] else []

            brief_data.append({
                'cluster_id': cluster_id,
                'cluster_name': hub_keyword,
                'hub_keyword': hub_keyword,
                'total_keywords': analysis['total_keywords'],
                'total_volume': analysis['total_volume'],
                'coherence': analysis['coherence'],
                'primary_keywords': ', '.join(analysis['primary']),
                'secondary_keywords': ', '.join(analysis['secondary'][:5]),
                'tertiary_keywords': f"{len(analysis['tertiary'])} additional",
                'target_category': target_category,
                'matches_target': matches_target,
                'detected_category': detected_category,
                'confidence_for_target': confidence,
                'top_entities': ', '.join(top_entities)
            })

        progress_bar.progress(1.0)
        status_text.text(f"✅ Tested {len(cluster_ids)} clusters")

        return pd.DataFrame(brief_data)
