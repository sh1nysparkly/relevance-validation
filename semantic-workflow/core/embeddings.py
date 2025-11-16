"""
OpenAI Embeddings Module
Handles batch generation of embeddings with rate limiting and error handling.
"""

import time
from typing import List, Optional
from openai import OpenAI
import streamlit as st


class EmbeddingGenerator:
    """Generates embeddings using OpenAI's API with batching and rate limiting."""

    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def get_embedding(self, text: str) -> List[float]:
        """Get embedding for a single text string."""
        text = text.replace("\n", " ").strip()
        if not text:
            raise ValueError("Cannot generate embedding for empty text")

        response = self.client.embeddings.create(
            input=[text],
            model=self.model
        )
        return response.data[0].embedding

    def get_embeddings_batch(
        self,
        texts: List[str],
        batch_size: int = 100,
        show_progress: bool = True
    ) -> List[List[float]]:
        """
        Get embeddings for multiple texts in batches.

        Args:
            texts: List of text strings to embed
            batch_size: Number of texts to process per API call
            show_progress: Whether to show progress in Streamlit

        Returns:
            List of embeddings (same order as input texts)
        """
        embeddings = []
        total_batches = (len(texts) - 1) // batch_size + 1

        if show_progress:
            progress_bar = st.progress(0)
            status_text = st.empty()

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            batch_num = i // batch_size + 1

            if show_progress:
                progress = batch_num / total_batches
                progress_bar.progress(progress)
                status_text.text(f"Generating embeddings: batch {batch_num}/{total_batches}")

            # Clean batch texts
            clean_batch = [t.replace("\n", " ").strip() for t in batch if t.strip()]

            # Get embeddings for this batch
            try:
                response = self.client.embeddings.create(
                    input=clean_batch,
                    model=self.model
                )
                batch_embeddings = [item.embedding for item in response.data]
                embeddings.extend(batch_embeddings)

            except Exception as e:
                st.error(f"Error processing batch {batch_num}: {e}")
                # Return None for failed embeddings
                embeddings.extend([None] * len(clean_batch))

            # Rate limiting: small delay between batches
            if i + batch_size < len(texts):
                time.sleep(0.1)

        if show_progress:
            progress_bar.progress(1.0)
            status_text.text(f"✅ Generated {len(embeddings)} embeddings")

        return embeddings
