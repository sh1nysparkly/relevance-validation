"""
Keyword Clustering Module
Handles semantic clustering of keywords using embeddings and hierarchical clustering.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import AgglomerativeClustering
import streamlit as st


class KeywordClusterer:
    """Clusters keywords based on semantic similarity using embeddings."""

    def __init__(self, distance_threshold: float = 0.5):
        """
        Initialize clusterer.

        Args:
            distance_threshold: Controls cluster tightness (0.3-0.4 = tight, 0.5-0.7 = loose)
        """
        self.distance_threshold = distance_threshold

    def cluster_keywords(
        self,
        df: pd.DataFrame,
        embeddings: List[List[float]],
        show_progress: bool = True
    ) -> pd.DataFrame:
        """
        Cluster keywords based on semantic similarity.

        Args:
            df: DataFrame with 'keyword' and 'volume' columns
            embeddings: List of embeddings (same order as df)
            show_progress: Whether to show progress in Streamlit

        Returns:
            DataFrame with added 'cluster' column
        """
        if show_progress:
            st.info("🔄 Clustering keywords by semantic similarity...")

        # Convert embeddings to numpy array
        embedding_matrix = np.array(embeddings)

        # Cluster using Agglomerative Clustering
        clustering = AgglomerativeClustering(
            n_clusters=None,
            distance_threshold=self.distance_threshold,
            metric='cosine',
            linkage='average'
        )

        df['cluster'] = clustering.fit_predict(embedding_matrix)

        num_clusters = df['cluster'].nunique()

        if show_progress:
            st.success(f"✅ Created {num_clusters} clusters")

        return df

    def analyze_cluster(
        self,
        cluster_df: pd.DataFrame,
        cluster_embeddings: np.ndarray
    ) -> Dict:
        """
        Analyze a single cluster to identify hub keyword and assign tiers.

        Args:
            cluster_df: DataFrame of keywords in this cluster
            cluster_embeddings: Embeddings for keywords in this cluster

        Returns:
            Dict with cluster analysis including hub keyword and tier assignments
        """
        if len(cluster_df) == 1:
            return {
                'hub_keyword': cluster_df.iloc[0]['keyword'],
                'primary': [cluster_df.iloc[0]['keyword']],
                'secondary': [],
                'tertiary': [],
                'coherence': 1.0,
                'total_keywords': 1,
                'total_volume': cluster_df.iloc[0].get('volume', 0)
            }

        # Calculate centroid
        centroid = cluster_embeddings.mean(axis=0).reshape(1, -1)

        # Calculate centrality (distance from centroid)
        centralities = cosine_similarity(cluster_embeddings, centroid).flatten()

        # Calculate coherence (average pairwise similarity)
        pairwise_sim = cosine_similarity(cluster_embeddings)
        coherence = (pairwise_sim.sum() - len(cluster_df)) / (len(cluster_df) * (len(cluster_df) - 1))

        # Add centrality scores
        cluster_df = cluster_df.copy()
        cluster_df['centrality'] = centralities

        # Calculate combined score: centrality * log(volume + 1)
        cluster_df['combined_score'] = cluster_df['centrality'] * np.log(cluster_df.get('volume', 0) + 1)

        # Sort by combined score
        cluster_df = cluster_df.sort_values('combined_score', ascending=False)

        # Hub keyword is the one with highest combined score
        hub_keyword = cluster_df.iloc[0]['keyword']

        # Assign tiers
        n = len(cluster_df)
        primary_count = min(3, n)
        secondary_count = min(10, n)

        primary = cluster_df.iloc[0:primary_count]['keyword'].tolist()
        secondary = cluster_df.iloc[primary_count:secondary_count]['keyword'].tolist()
        tertiary = cluster_df.iloc[secondary_count:]['keyword'].tolist()

        return {
            'hub_keyword': hub_keyword,
            'primary': primary,
            'secondary': secondary,
            'tertiary': tertiary,
            'coherence': float(coherence),
            'total_keywords': len(cluster_df),
            'total_volume': float(cluster_df.get('volume', 0).sum()),
            'keywords_detail': cluster_df[['keyword', 'volume', 'centrality', 'combined_score']].to_dict('records')
        }

    def detect_cannibalization(
        self,
        df: pd.DataFrame,
        embeddings: List[List[float]],
        overlap_threshold: float = 0.80
    ) -> List[Tuple[int, int, float]]:
        """
        Detect clusters that are too similar (potential cannibalization).

        Args:
            df: DataFrame with cluster assignments
            embeddings: List of embeddings
            overlap_threshold: Similarity threshold for flagging (0-1)

        Returns:
            List of tuples (cluster_id_1, cluster_id_2, similarity_score)
        """
        embedding_matrix = np.array(embeddings)
        cluster_ids = df['cluster'].unique()
        cannibalization_pairs = []

        # Compare each pair of clusters
        for i, cluster_a in enumerate(cluster_ids):
            for cluster_b in cluster_ids[i+1:]:
                # Get embeddings for each cluster
                emb_a = embedding_matrix[df['cluster'] == cluster_a]
                emb_b = embedding_matrix[df['cluster'] == cluster_b]

                # Calculate cross-similarity
                cross_sim = cosine_similarity(emb_a, emb_b)

                # Average of maximum similarities
                avg_max_sim = cross_sim.max(axis=1).mean()

                if avg_max_sim >= overlap_threshold:
                    cannibalization_pairs.append((cluster_a, cluster_b, float(avg_max_sim)))

        return cannibalization_pairs

    def analyze_all_clusters(
        self,
        df: pd.DataFrame,
        embeddings: List[List[float]],
        show_progress: bool = True
    ) -> Dict[int, Dict]:
        """
        Analyze all clusters in the dataset.

        Args:
            df: DataFrame with cluster assignments
            embeddings: List of embeddings
            show_progress: Whether to show progress

        Returns:
            Dict mapping cluster_id to cluster analysis
        """
        embedding_matrix = np.array(embeddings)
        cluster_analyses = {}

        cluster_ids = df['cluster'].unique()

        if show_progress:
            progress_bar = st.progress(0)
            status_text = st.empty()

        for idx, cluster_id in enumerate(cluster_ids):
            if show_progress:
                progress = (idx + 1) / len(cluster_ids)
                progress_bar.progress(progress)
                status_text.text(f"Analyzing cluster {idx + 1}/{len(cluster_ids)}...")

            cluster_df = df[df['cluster'] == cluster_id].copy()
            cluster_emb = embedding_matrix[df['cluster'] == cluster_id]

            analysis = self.analyze_cluster(cluster_df, cluster_emb)
            cluster_analyses[cluster_id] = analysis

        if show_progress:
            progress_bar.progress(1.0)
            status_text.text(f"✅ Analyzed {len(cluster_analyses)} clusters")

        return cluster_analyses
