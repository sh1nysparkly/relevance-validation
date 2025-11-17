"""
Google NLP Analysis Module
Handles entity extraction and content classification using Google Cloud Natural Language API.
"""

import time
from typing import Dict, List, Optional
from google.cloud import language_v1
import streamlit as st


class NLPAnalyzer:
    """Wrapper for Google Cloud Natural Language API."""

    def __init__(self):
        self.client = language_v1.LanguageServiceClient()

    def analyze_text(
        self,
        text: str,
        extract_entities: bool = True,
        classify_content: bool = True
    ) -> Dict:
        """
        Analyze text with Google NLP API.

        Args:
            text: Text content to analyze
            extract_entities: Whether to extract entities
            classify_content: Whether to classify content categories

        Returns:
            Dict with 'entities', 'categories', and 'error' keys
        """
        if not text or not text.strip():
            return {
                'categories': [],
                'entities': [],
                'error': 'Input text was empty'
            }

        try:
            document = language_v1.Document(
                content=text,
                type_=language_v1.Document.Type.PLAIN_TEXT
            )

            features = {
                'extract_entities': extract_entities,
                'classify_text': classify_content
            }

            response = self.client.annotate_text(
                document=document,
                features=features,
                encoding_type=language_v1.EncodingType.UTF8
            )

            # Extract categories with confidence
            categories = []
            if classify_content and response.categories:
                for category in response.categories:
                    categories.append({
                        'name': category.name,
                        'confidence': round(category.confidence, 4)
                    })
                categories.sort(key=lambda x: x['confidence'], reverse=True)

            # Extract entities with salience
            entities = []
            if extract_entities and response.entities:
                for entity in response.entities:
                    entities.append({
                        'name': entity.name,
                        'type': language_v1.Entity.Type(entity.type_).name,
                        'salience': round(entity.salience, 4),
                        'wikipedia_url': entity.metadata.get('wikipedia_url', ''),
                        'mid': entity.metadata.get('mid', ''),
                    })
                entities.sort(key=lambda x: x['salience'], reverse=True)

            return {
                'categories': categories,
                'entities': entities,
                'error': None
            }

        except Exception as e:
            return {
                'categories': [],
                'entities': [],
                'error': str(e)
            }

    def test_category_match(
        self,
        text: str,
        target_category: str
    ) -> Dict:
        """
        Test if text matches a target category.

        Args:
            text: Text content to analyze
            target_category: Target category to match (e.g., "/Travel/Family")

        Returns:
            Dict with match results including confidence and detected category
        """
        result = self.analyze_text(text, extract_entities=False, classify_content=True)

        if result['error']:
            return {
                'matches_target': False,
                'confidence': 0.0,
                'detected_category': None,
                'all_categories': [],
                'error': result['error']
            }

        categories = result['categories']

        if not categories:
            return {
                'matches_target': False,
                'confidence': 0.0,
                'detected_category': None,
                'all_categories': [],
                'error': 'No categories detected'
            }

        # Check if target category matches any detected category
        target_lower = target_category.lower()
        matched = False
        matched_confidence = 0.0
        matched_category = None

        for cat in categories:
            if target_lower in cat['name'].lower():
                matched = True
                matched_confidence = cat['confidence']
                matched_category = cat['name']
                break

        return {
            'matches_target': matched,
            'confidence': matched_confidence if matched else categories[0]['confidence'],
            'detected_category': categories[0]['name'],
            'matched_category': matched_category,
            'all_categories': categories[:5],
            'error': None
        }

    def iterative_drag_analysis(
        self,
        text: str,
        target_category: str,
        entities_to_test: Optional[List[str]] = None,
        official_keywords: Optional[List[str]] = None,
        min_keywords: int = 5,
        show_progress: bool = True
    ) -> Dict:
        """
        Iteratively remove keywords/entities to find what's "dragging" category confidence.

        This is the expensive "remove-and-test" approach that finds the worst offenders
        one at a time, locking in wins progressively.

        Separates entities into two lists:
        - List A (Official Keywords): Terms from your strategic brief
        - List B (Other Entities): Everything else detected in the copy

        Args:
            text: Original draft text
            target_category: Target category to optimize for
            entities_to_test: List of entities/keywords to test (if None, extracts from text)
            official_keywords: List of official keywords from strategic brief (for dual-list analysis)
            min_keywords: Minimum number of keywords to keep
            show_progress: Whether to show progress in Streamlit

        Returns:
            Dict with iterative analysis results and recommendations, separated by list
        """
        # Get baseline
        baseline = self.test_category_match(text, target_category)
        baseline_confidence = baseline['confidence']
        baseline_category = baseline['detected_category']

        # Extract entities to test if not provided
        if entities_to_test is None:
            analysis = self.analyze_text(text, extract_entities=True, classify_content=False)
            entities_to_test = [e['name'] for e in analysis['entities']]

        if not entities_to_test:
            return {
                'baseline_confidence': baseline_confidence,
                'baseline_category': baseline_category,
                'iterations': [],
                'final_confidence': baseline_confidence,
                'removed_terms': [],
                'removed_official_keywords': [],
                'removed_other_entities': [],
                'error': 'No entities found to test'
            }

        # Categorize entities into List A (official) and List B (other)
        official_keywords_lower = [kw.lower() for kw in (official_keywords or [])]
        list_a_entities = []  # Official keywords
        list_b_entities = []  # Other entities

        for entity in entities_to_test:
            if entity.lower() in official_keywords_lower:
                list_a_entities.append(entity)
            else:
                list_b_entities.append(entity)

        # Iterative removal
        current_text = text
        current_confidence = baseline_confidence
        removed_terms = []
        removed_official = []  # Track List A removals
        removed_other = []     # Track List B removals
        iterations = []
        remaining_entities = entities_to_test.copy()

        if show_progress:
            progress_bar = st.progress(0)
            status_text = st.empty()

        iteration_num = 0
        max_iterations = len(entities_to_test)

        while remaining_entities and iteration_num < max_iterations:
            iteration_num += 1

            if show_progress:
                progress = iteration_num / max_iterations
                progress_bar.progress(progress)
                status_text.text(f"Testing iteration {iteration_num}/{max_iterations}...")

            # Test removing each remaining entity
            best_improvement = 0
            best_entity = None
            best_new_confidence = current_confidence

            for entity in remaining_entities:
                # Remove this entity from current text
                test_text = current_text.replace(entity, "").strip()

                # Make sure we're not removing too much
                word_count = len(test_text.split())
                if word_count < min_keywords:
                    continue

                # Test the modified text
                test_result = self.test_category_match(test_text, target_category)
                new_confidence = test_result['confidence']

                improvement = new_confidence - current_confidence

                if improvement > best_improvement:
                    best_improvement = improvement
                    best_entity = entity
                    best_new_confidence = new_confidence

                # Small delay to avoid rate limiting
                time.sleep(0.05)

            # If we found an improvement, lock it in
            if best_improvement > 0.01:  # Threshold: at least 1% improvement
                current_text = current_text.replace(best_entity, "").strip()
                removed_terms.append(best_entity)
                remaining_entities.remove(best_entity)

                # Track which list this term came from
                is_official = best_entity in list_a_entities
                if is_official:
                    removed_official.append(best_entity)
                else:
                    removed_other.append(best_entity)

                iterations.append({
                    'iteration': iteration_num,
                    'removed': best_entity,
                    'is_official_keyword': is_official,
                    'old_confidence': current_confidence,
                    'new_confidence': best_new_confidence,
                    'improvement': best_improvement
                })

                current_confidence = best_new_confidence
            else:
                # No more improvements found
                break

        if show_progress:
            progress_bar.progress(1.0)
            status_text.text(f"✅ Completed {len(iterations)} iterations")

        return {
            'baseline_confidence': baseline_confidence,
            'baseline_category': baseline_category,
            'iterations': iterations,
            'final_confidence': current_confidence,
            'total_improvement': current_confidence - baseline_confidence,
            'removed_terms': removed_terms,
            'removed_official_keywords': removed_official,
            'removed_other_entities': removed_other,
            'list_a_count': len(list_a_entities),
            'list_b_count': len(list_b_entities),
            'error': None
        }
