"""
Utility functions for data processing and validation.
"""

import pandas as pd
from typing import List, Dict


def validate_keywords_csv(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate and clean keywords CSV with flexible column mapping.

    Handles common variations like:
    - Keywords: "Keyword", "Keywords", "Query", "Search Term", "KW", etc.
    - Volume: "Volume", "Search Volume", "MSV", "SV", "Monthly Searches", etc.

    Args:
        df: Input DataFrame

    Returns:
        Cleaned DataFrame with standardized columns

    Raises:
        ValueError: If required columns are missing
    """
    # Common variations for keyword column
    KEYWORD_PATTERNS = [
        'keyword', 'keywords', 'query', 'queries', 'search query',
        'search queries', 'search term', 'search terms', 'term',
        'terms', 'kw', 'search', 'phrase', 'phrases'
    ]

    # Common variations for volume column
    VOLUME_PATTERNS = [
        'volume', 'search volume', 'monthly search volume', 'msv',
        'sv', 'searches', 'monthly searches', 'avg monthly searches',
        'search vol', 'monthly volume', 'avg searches', 'search count',
        'monthly search', 'monthly search count'
    ]

    # Standardize column names (lowercase, strip whitespace)
    df.columns = df.columns.str.lower().str.strip()

    # Find keyword column
    keyword_col = None
    for col in df.columns:
        # Remove common extra characters
        clean_col = col.replace('_', ' ').replace('-', ' ').strip()
        if clean_col in KEYWORD_PATTERNS:
            keyword_col = col
            break

    if not keyword_col:
        # Try partial matching as fallback
        for col in df.columns:
            clean_col = col.replace('_', ' ').replace('-', ' ').strip()
            if any(pattern in clean_col for pattern in ['keyword', 'query', 'term', 'phrase']):
                keyword_col = col
                break

    if not keyword_col:
        available_cols = ', '.join(df.columns.tolist())
        raise ValueError(
            f"Could not find keyword column. Available columns: {available_cols}\n"
            f"Expected one of: {', '.join(KEYWORD_PATTERNS[:5])}, etc."
        )

    # Find volume column
    volume_col = None
    for col in df.columns:
        clean_col = col.replace('_', ' ').replace('-', ' ').strip()
        if clean_col in VOLUME_PATTERNS:
            volume_col = col
            break

    if not volume_col:
        # Try partial matching as fallback
        for col in df.columns:
            clean_col = col.replace('_', ' ').replace('-', ' ').strip()
            if any(pattern in clean_col for pattern in ['volume', 'search', 'msv', 'sv']):
                # Make sure it's not the keyword column we already found
                if col != keyword_col:
                    volume_col = col
                    break

    # Rename columns to standard names
    rename_map = {keyword_col: 'keyword'}
    if volume_col:
        rename_map[volume_col] = 'volume'

    df = df.rename(columns=rename_map)

    # Add volume column if still missing
    if 'volume' not in df.columns:
        df['volume'] = 0

    # Keep only the columns we need (plus any extra for reference)
    # This prevents issues with many-column spreadsheets
    essential_cols = ['keyword', 'volume']
    extra_cols = [col for col in df.columns if col not in essential_cols]

    # Clean data
    df = df.dropna(subset=['keyword'])
    df['keyword'] = df['keyword'].astype(str).str.strip().str.lower()
    df = df.drop_duplicates(subset=['keyword'])
    df['volume'] = pd.to_numeric(df['volume'], errors='coerce').fillna(0)

    # Remove empty keywords
    df = df[df['keyword'] != '']

    # Keep only essential columns (drop the extra stuff from columns H, I, etc.)
    df = df[essential_cols]

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
