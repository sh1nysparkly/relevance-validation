"""
Utility functions for data processing and validation.
"""

import pandas as pd
from typing import List, Dict


def validate_keywords_csv(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate and clean keywords CSV.

    Args:
        df: Input DataFrame

    Returns:
        Cleaned DataFrame with standardized columns

    Raises:
        ValueError: If required columns are missing
    """
    # Standardize column names
    df.columns = df.columns.str.lower().str.strip()

    # Check for required columns
    if 'keyword' not in df.columns:
        raise ValueError("CSV must have a 'keyword' column")

    # Add volume column if missing
    if 'volume' not in df.columns:
        df['volume'] = 0

    # Clean data
    df = df.dropna(subset=['keyword'])
    df['keyword'] = df['keyword'].str.strip().str.lower()
    df = df.drop_duplicates(subset=['keyword'])
    df['volume'] = pd.to_numeric(df['volume'], errors='coerce').fillna(0)

    # Remove empty keywords
    df = df[df['keyword'] != '']

    return df


def calculate_keyword_coverage(
    draft_text: str,
    primary_keywords: List[str],
    secondary_keywords: List[str],
    tertiary_keywords: List[str]
) -> Dict:
    """
    Calculate how well a draft covers target keywords.

    Args:
        draft_text: The draft content
        primary_keywords: List of primary keywords
        secondary_keywords: List of secondary keywords
        tertiary_keywords: List of tertiary keywords

    Returns:
        Dict with coverage percentages and missing keywords
    """
    draft_lower = draft_text.lower()

    def check_coverage(keywords: List[str]) -> tuple:
        if not keywords:
            return 0, 0, []
        found = [kw for kw in keywords if kw.lower() in draft_lower]
        missing = [kw for kw in keywords if kw.lower() not in draft_lower]
        return len(found), len(keywords), missing

    primary_found, primary_total, primary_missing = check_coverage(primary_keywords)
    secondary_found, secondary_total, secondary_missing = check_coverage(secondary_keywords)
    tertiary_found, tertiary_total, tertiary_missing = check_coverage(tertiary_keywords)

    return {
        'primary': {
            'found': primary_found,
            'total': primary_total,
            'percentage': primary_found / primary_total if primary_total > 0 else 0,
            'missing': primary_missing
        },
        'secondary': {
            'found': secondary_found,
            'total': secondary_total,
            'percentage': secondary_found / secondary_total if secondary_total > 0 else 0,
            'missing': secondary_missing
        },
        'tertiary': {
            'found': tertiary_found,
            'total': tertiary_total,
            'percentage': tertiary_found / tertiary_total if tertiary_total > 0 else 0,
            'missing': tertiary_missing
        }
    }


def format_category_hierarchy(category: str) -> str:
    """
    Format a category path for display.

    Args:
        category: Category path (e.g., "/Travel/Cruises")

    Returns:
        Formatted string with indentation
    """
    if not category:
        return ""

    parts = category.strip('/').split('/')
    depth = len(parts) - 1
    indent = "  " * depth
    return f"{indent}• {parts[-1]}"


def export_to_csv(data: List[Dict], filename: str) -> str:
    """
    Export data to CSV.

    Args:
        data: List of dictionaries
        filename: Output filename

    Returns:
        Path to saved file
    """
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)
    return filename
