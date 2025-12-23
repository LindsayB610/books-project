"""
Safe CSV reading and writing utilities that preserve manual fields.
"""

import csv
from typing import List, Dict, Optional
from pathlib import Path


def read_csv_safe(filepath: str) -> List[Dict]:
    """
    Read CSV file safely, handling UTF-8 and empty files.
    """
    filepath = Path(filepath)
    if not filepath.exists():
        return []
    
    rows = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert empty strings to None for easier checking
            cleaned_row = {k: (v.strip() if v else None) for k, v in row.items()}
            rows.append(cleaned_row)
    
    return rows


def write_csv_safe(filepath: str, rows: List[Dict], fieldnames: List[str]):
    """
    Write CSV file safely with UTF-8 encoding.
    Sorts rows by author, then title for readability.
    """
    if not rows:
        # Write header only
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
        return
    
    # Sort by author, then title
    def sort_key(row):
        author = row.get('author', '') or ''
        title = row.get('title', '') or ''
        return (author.lower(), title.lower())
    
    sorted_rows = sorted(rows, key=sort_key)
    
    with open(filepath, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sorted_rows)


def is_manually_set(value: Optional[str]) -> bool:
    """
    Check if a field value was manually set (not empty/null).
    """
    return value is not None and value.strip() != ''


# Protected fields that should never be overwritten
PROTECTED_FIELDS = {
    'work_id',  # Stable identifier, preserve once set
    'rating', 'reread', 'reread_count', 'dnf', 'dnf_reason',
    'pacing_rating', 'tone', 'vibe', 'what_i_wanted', 'did_it_deliver',
    'favorite_elements', 'pet_peeves', 'notes', 'anchor_type',
    'read_status', 'date_read', 'would_recommend'
}


def safe_merge(existing: Dict, new: Dict) -> Dict:
    """
    Merge new data into existing row, preserving protected fields.
    
    Rules:
    - Protected fields: only update if existing is empty
    - Safe fields: update if new data is more complete (not empty)
    - Always combine formats and sources (union)
    - Preserve work_id from existing (stable identifier)
    """
    merged = existing.copy()
    
    # Always preserve existing work_id (stable identifier)
    if merged.get('work_id'):
        # Don't overwrite work_id
        pass
    elif new.get('work_id'):
        merged['work_id'] = new.get('work_id')
    
    for key, new_value in new.items():
        if key == 'work_id':
            continue  # Already handled above
        
        if key not in merged:
            merged[key] = new_value
            continue
        
        existing_value = merged.get(key)
        
        # Protected fields: only update if existing is empty
        if key in PROTECTED_FIELDS:
            if not is_manually_set(existing_value) and is_manually_set(new_value):
                merged[key] = new_value
            # Otherwise, keep existing value
        
        # Special handling for formats and sources (union)
        elif key == 'formats':
            existing_formats = set((existing_value or '').split(','))
            new_formats = set((new_value or '').split(','))
            combined = existing_formats | new_formats
            combined.discard('')  # Remove empty strings
            merged[key] = ','.join(sorted(combined)) if combined else None
        
        elif key == 'sources':
            existing_sources = set((existing_value or '').split(','))
            new_sources = set((new_value or '').split(','))
            combined = existing_sources | new_sources
            combined.discard('')
            merged[key] = ','.join(sorted(combined)) if combined else None
        
        # Safe fields: update if new value is more complete
        else:
            if not is_manually_set(existing_value) and is_manually_set(new_value):
                merged[key] = new_value
            # If both exist, prefer existing (it's already in the canonical CSV)
    
    return merged

