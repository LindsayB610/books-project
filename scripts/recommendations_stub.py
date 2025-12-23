#!/usr/bin/env python3
"""
Recommendations stub: generates structured prompt for 12-book "advent calendar" recommendations.
Reads anchor_type books and outputs Markdown/JSON suitable for human-AI conversation.
"""

import sys
import json
from pathlib import Path
from typing import List, Dict
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.csv_utils import read_csv_safe


def load_anchor_books(books: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Load books by anchor_type.
    Returns dict mapping anchor_type to list of books.
    """
    anchors = defaultdict(list)
    
    for book in books:
        anchor_type = book.get('anchor_type', '').strip()
        if anchor_type:
            anchors[anchor_type].append(book)
    
    return dict(anchors)


def extract_preference_signals(book: Dict) -> Dict:
    """
    Extract key preference signals from a book.
    """
    signals = {
        'title': book.get('title', ''),
        'author': book.get('author', ''),
        'rating': book.get('rating', ''),
        'tone': book.get('tone', ''),
        'vibe': book.get('vibe', ''),
        'pacing_rating': book.get('pacing_rating', ''),
        'favorite_elements': book.get('favorite_elements', ''),
        'pet_peeves': book.get('pet_peeves', ''),
        'what_i_wanted': book.get('what_i_wanted', ''),
        'did_it_deliver': book.get('did_it_deliver', ''),
        'dnf_reason': book.get('dnf_reason', ''),
        'would_recommend': book.get('would_recommend', ''),
        'genres': book.get('genres', ''),
        'notes': book.get('notes', '')
    }
    
    # Remove empty fields
    return {k: v for k, v in signals.items() if v and v.strip()}


def generate_markdown_prompt(anchors_by_type: Dict[str, List[Dict]]) -> str:
    """
    Generate a Markdown prompt for recommendation generation.
    """
    lines = []
    lines.append("# Book Recommendation Request: 12-Book Advent Calendar")
    lines.append("")
    lines.append("Based on my reading history and preferences, generate a 12-book recommendation list.")
    lines.append("")
    
    # All-time favorites
    if 'all_time_favorite' in anchors_by_type:
        lines.append("## All-Time Favorites")
        lines.append("")
        for book in anchors_by_type['all_time_favorite']:
            signals = extract_preference_signals(book)
            lines.append(f"### {signals.get('title', 'Unknown')} by {signals.get('author', 'Unknown')}")
            if signals.get('rating'):
                lines.append(f"- **Rating**: {signals['rating']}/5")
            if signals.get('tone'):
                lines.append(f"- **Tone**: {signals['tone']}")
            if signals.get('vibe'):
                lines.append(f"- **Vibe**: {signals['vibe']}")
            if signals.get('pacing_rating'):
                lines.append(f"- **Pacing**: {signals['pacing_rating']}/5")
            if signals.get('favorite_elements'):
                lines.append(f"- **What worked**: {signals['favorite_elements']}")
            if signals.get('would_recommend') == '1':
                lines.append(f"- **Would recommend**: Yes")
            if signals.get('genres'):
                lines.append(f"- **Genres**: {signals['genres']}")
            if signals.get('notes'):
                # Truncate long notes
                notes = signals['notes'][:200] + "..." if len(signals['notes']) > 200 else signals['notes']
                lines.append(f"- **Notes**: {notes}")
            lines.append("")
    
    # Recent hits
    if 'recent_hit' in anchors_by_type:
        lines.append("## Recent Hits")
        lines.append("")
        for book in anchors_by_type['recent_hit']:
            signals = extract_preference_signals(book)
            lines.append(f"### {signals.get('title', 'Unknown')} by {signals.get('author', 'Unknown')}")
            if signals.get('rating'):
                lines.append(f"- **Rating**: {signals['rating']}/5")
            if signals.get('tone'):
                lines.append(f"- **Tone**: {signals['tone']}")
            if signals.get('vibe'):
                lines.append(f"- **Vibe**: {signals['vibe']}")
            if signals.get('what_i_wanted'):
                lines.append(f"- **What I wanted**: {signals['what_i_wanted']}")
            if signals.get('did_it_deliver') == '1':
                lines.append(f"- **Did it deliver**: Yes")
            if signals.get('favorite_elements'):
                lines.append(f"- **What worked**: {signals['favorite_elements']}")
            lines.append("")
    
    # Recent misses
    if 'recent_miss' in anchors_by_type:
        lines.append("## Recent Misses")
        lines.append("")
        for book in anchors_by_type['recent_miss']:
            signals = extract_preference_signals(book)
            lines.append(f"### {signals.get('title', 'Unknown')} by {signals.get('author', 'Unknown')}")
            if signals.get('rating'):
                lines.append(f"- **Rating**: {signals['rating']}/5")
            if signals.get('what_i_wanted'):
                lines.append(f"- **What I wanted**: {signals['what_i_wanted']}")
            if signals.get('did_it_deliver') == '0':
                lines.append(f"- **Did it deliver**: No")
            if signals.get('pet_peeves'):
                lines.append(f"- **What didn't work**: {signals['pet_peeves']}")
            lines.append("")
    
    # DNF books
    if 'dnf' in anchors_by_type:
        lines.append("## Did Not Finish")
        lines.append("")
        for book in anchors_by_type['dnf']:
            signals = extract_preference_signals(book)
            lines.append(f"### {signals.get('title', 'Unknown')} by {signals.get('author', 'Unknown')}")
            if signals.get('dnf_reason'):
                lines.append(f"- **Why I stopped**: {signals['dnf_reason']}")
            if signals.get('pet_peeves'):
                lines.append(f"- **What didn't work**: {signals['pet_peeves']}")
            lines.append("")
    
    # Summary section
    lines.append("## Request")
    lines.append("")
    lines.append("Based on these preferences, generate a 12-book \"advent calendar\" style recommendation list.")
    lines.append("The list should:")
    lines.append("- Include diverse genres and styles")
    lines.append("- Match the tones and vibes I enjoy")
    lines.append("- Avoid elements I've identified as pet peeves")
    lines.append("- Include a mix of well-known and lesser-known titles")
    lines.append("")
    lines.append("For each recommendation, provide:")
    lines.append("- Title and author")
    lines.append("- Brief explanation of why it matches my preferences")
    lines.append("- What elements from my favorites it shares")
    lines.append("")
    
    return "\n".join(lines)


def generate_json_prompt(anchors_by_type: Dict[str, List[Dict]]) -> Dict:
    """
    Generate a JSON structure for recommendation generation.
    """
    data = {
        'request_type': '12_book_advent_calendar',
        'anchor_books': {}
    }
    
    for anchor_type, books in anchors_by_type.items():
        data['anchor_books'][anchor_type] = []
        for book in books:
            signals = extract_preference_signals(book)
            data['anchor_books'][anchor_type].append(signals)
    
    return data


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate structured prompt for book recommendations')
    parser.add_argument('--format', choices=['markdown', 'json'], default='markdown',
                       help='Output format (default: markdown)')
    parser.add_argument('--csv', type=str, help='Path to books.csv (default: books.csv in project root)')
    parser.add_argument('--output', type=str, help='Output file (default: print to stdout)')
    
    args = parser.parse_args()
    
    project_root = Path(__file__).parent.parent
    books_csv = Path(args.csv) if args.csv else project_root / 'books.csv'
    
    if not books_csv.exists():
        print(f"Error: {books_csv} not found.", file=sys.stderr)
        print("Please run merge_and_dedupe.py first to create books.csv", file=sys.stderr)
        sys.exit(1)
    
    print(f"Loading {books_csv}...", file=sys.stderr)
    books = read_csv_safe(str(books_csv))
    
    if not books:
        print("No books found in CSV.", file=sys.stderr)
        sys.exit(1)
    
    anchors_by_type = load_anchor_books(books)
    
    if not anchors_by_type:
        print("No anchor books found (books with anchor_type set).", file=sys.stderr)
        print("Please enrich some books with anchor_type in books.csv", file=sys.stderr)
        sys.exit(1)
    
    # Generate output
    if args.format == 'markdown':
        output = generate_markdown_prompt(anchors_by_type)
    else:
        output = json.dumps(generate_json_prompt(anchors_by_type), indent=2, ensure_ascii=False)
    
    # Write to file or stdout
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"Output written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == '__main__':
    main()

