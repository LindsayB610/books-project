#!/usr/bin/env python3
"""
Simple recommendation stub using anchor_type books.
Generates recommendations based on enriched anchor books.
"""

import sys
from pathlib import Path
from typing import List, Dict, Set, Tuple
import random

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.csv_utils import read_csv_safe


def load_anchor_books(books: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Load books by anchor_type.
    Returns dict mapping anchor_type to list of books.
    """
    anchors = {
        'all_time_favorite': [],
        'recent_hit': [],
        'recent_miss': [],
        'dnf': []
    }
    
    for book in books:
        anchor_type = book.get('anchor_type', '').strip()
        if anchor_type in anchors:
            anchors[anchor_type].append(book)
    
    return anchors


def extract_preferences(anchor_books: List[Dict]) -> Dict:
    """
    Extract preference patterns from anchor books.
    Returns dict with aggregated preferences.
    """
    preferences = {
        'tones': set(),
        'vibes': set(),
        'favorite_elements': set(),
        'pet_peeves': set(),
        'genres': set(),
        'ratings': [],
        'what_worked': [],
        'what_didnt_work': []
    }
    
    for book in anchor_books:
        # Collect tones and vibes
        tone = book.get('tone', '').strip()
        if tone:
            preferences['tones'].add(tone.lower())
        
        vibe = book.get('vibe', '').strip()
        if vibe:
            preferences['vibes'].add(vibe.lower())
        
        # Collect favorite elements
        elements = book.get('favorite_elements', '').strip()
        if elements:
            # Split by common delimiters
            for elem in elements.replace(';', ',').split(','):
                preferences['favorite_elements'].add(elem.strip().lower())
        
        # Collect pet peeves
        peeves = book.get('pet_peeves', '').strip()
        if peeves:
            for peeve in peeves.replace(';', ',').split(','):
                preferences['pet_peeves'].add(peeve.strip().lower())
        
        # Collect genres
        genres = book.get('genres', '').strip()
        if genres:
            for genre in genres.split(','):
                preferences['genres'].add(genre.strip().lower())
        
        # Collect ratings
        rating = book.get('rating', '').strip()
        if rating:
            try:
                preferences['ratings'].append(float(rating))
            except (ValueError, TypeError):
                pass
        
        # What worked (from favorite_elements or notes)
        if elements:
            preferences['what_worked'].append(elements)
        
        # What didn't work (from pet_peeves or dnf_reason)
        if peeves:
            preferences['what_didnt_work'].append(peeves)
        dnf_reason = book.get('dnf_reason', '').strip()
        if dnf_reason:
            preferences['what_didnt_work'].append(dnf_reason)
    
    return preferences


def find_candidate_books(books: List[Dict], preferences: Dict, exclude_anchors: Set[str], query: str = None) -> List[Dict]:
    """
    Find candidate books for recommendations.
    Excludes already-read books and anchor books.
    Optionally filters by query string.
    """
    candidates = []
    query_lower = query.lower() if query else None
    
    for book in books:
        # Skip if already read
        read_status = book.get('read_status', '').strip().lower()
        if read_status in ['read', 'dnf']:
            continue
        
        # Skip anchor books
        title_author = f"{book.get('title', '')}|{book.get('author', '')}"
        if title_author in exclude_anchors:
            continue
        
        # Skip if no title/author
        if not book.get('title') or not book.get('author'):
            continue
        
        # Filter by query if provided
        if query_lower:
            title = (book.get('title', '') or '').lower()
            author = (book.get('author', '') or '').lower()
            if query_lower not in title and query_lower not in author:
                continue
        
        candidates.append(book)
    
    return candidates


def score_book(book: Dict, preferences: Dict, query: str = None) -> Tuple[float, List[str]]:
    """
    Score a book based on how well it matches preferences.
    Returns (score, reasons) tuple where score is 0.0 to 1.0 and reasons is a list of strings.
    """
    score = 0.0
    reasons = []
    
    # Query matching (if provided)
    if query:
        query_lower = query.lower()
        title = (book.get('title', '') or '').lower()
        author = (book.get('author', '') or '').lower()
        if query_lower in title or query_lower in author:
            score += 0.5
            reasons.append(f"Matches query: '{query}'")
    
    # Genre/tag matching (primary scoring factor)
    book_genres = set()
    genres_str = book.get('genres', '').strip()
    if genres_str:
        book_genres = {g.strip().lower() for g in genres_str.split(',')}
    
    if book_genres and preferences['genres']:
        genre_overlap = book_genres & preferences['genres']
        if genre_overlap:
            overlap_ratio = len(genre_overlap) / max(len(book_genres), len(preferences['genres']))
            genre_score = min(0.5, overlap_ratio * 0.5)
            score += genre_score
            reasons.append(f"Genre match: {', '.join(list(genre_overlap)[:3])}")
    
    # Boost for books with tags/genres (even if no match)
    if book_genres and not preferences['genres']:
        score += 0.1
        reasons.append("Has genre tags")
    
    # Base score for unread books
    if score == 0.0:
        score = 0.05
    
    return (min(1.0, score), reasons)


def generate_recommendations(books: List[Dict], num_recommendations: int = 5, query: str = None) -> List[Tuple[Dict, float, List[str]]]:
    """
    Generate book recommendations based on anchor books.
    Returns list of (book, score, reasons) tuples.
    """
    # Load anchor books
    anchors_by_type = load_anchor_books(books)
    
    # Focus on favorites and recent hits
    positive_anchors = anchors_by_type['all_time_favorite'] + anchors_by_type['recent_hit']
    
    if not positive_anchors:
        print("⚠️  No anchor books found (all_time_favorite or recent_hit).")
        print("   Please enrich some books with anchor_type in books.csv")
        return []
    
    print(f"📚 Found {len(positive_anchors)} positive anchor book(s)")
    
    # Extract preferences
    preferences = extract_preferences(positive_anchors)
    
    print(f"   Preferences extracted:")
    if preferences['genres']:
        print(f"   - Genres/Tags: {', '.join(list(preferences['genres'])[:5])}")
    if preferences['tones']:
        print(f"   - Tones: {', '.join(list(preferences['tones'])[:5])}")
    if preferences['vibes']:
        print(f"   - Vibes: {', '.join(list(preferences['vibes'])[:5])}")
    if preferences['ratings']:
        avg_rating = sum(preferences['ratings']) / len(preferences['ratings'])
        print(f"   - Average rating of favorites: {avg_rating:.1f}")
    
    # Build exclude set
    exclude_titles = {f"{b.get('title', '')}|{b.get('author', '')}" for b in positive_anchors}
    
    # Find candidates
    candidates = find_candidate_books(books, preferences, exclude_titles, query)
    
    if not candidates:
        print("⚠️  No candidate books found (all books are read or are anchor books)")
        if query:
            print(f"   (filtered by query: '{query}')")
        return []
    
    print(f"   Found {len(candidates)} candidate book(s)")
    if query:
        print(f"   (filtered by query: '{query}')")
    
    # Score candidates
    scored = []
    for book in candidates:
        score, reasons = score_book(book, preferences, query)
        scored.append((book, score, reasons))
    
    scored.sort(key=lambda x: x[1], reverse=True)
    
    # Select top recommendations (3-5)
    top_n = min(max(3, num_recommendations), min(5, len(scored)))
    recommendations = scored[:top_n]
    
    return recommendations


def print_recommendations(recommendations: List[Tuple[Dict, float, List[str]]]):
    """Print formatted recommendations with reasons."""
    if not recommendations:
        return
    
    print("\n" + "=" * 80)
    print(f"📖 Recommendations ({len(recommendations)} books)")
    print("=" * 80)
    print()
    
    for idx, (book, score, reasons) in enumerate(recommendations, 1):
        title = book.get('title', 'Unknown')
        author = book.get('author', 'Unknown')
        genres = book.get('genres', 'N/A')
        isbn13 = book.get('isbn13', 'N/A')
        
        print(f"{idx}. {title}")
        print(f"   by {author}")
        if genres and genres != 'N/A':
            print(f"   Tags/Genres: {genres}")
        if isbn13 and isbn13 != 'N/A':
            print(f"   ISBN13: {isbn13}")
        print(f"   Score: {score:.2f}")
        if reasons:
            print(f"   Why: {', '.join(reasons)}")
        print()


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate book recommendations from anchor books')
    parser.add_argument('-n', '--limit', type=int, default=5, help='Number of recommendations (default: 5, max: 5)')
    parser.add_argument('-q', '--query', type=str, help='Filter recommendations by query string (searches title/author)')
    parser.add_argument('--csv', type=str, help='Path to books.csv (default: books.csv in project root)')
    
    args = parser.parse_args()
    
    # Limit to 3-5 recommendations
    num_recs = max(3, min(5, args.limit))
    
    project_root = Path(__file__).parent.parent
    books_csv = Path(args.csv) if args.csv else project_root / 'books.csv'
    
    if not books_csv.exists():
        print(f"Error: {books_csv} not found.")
        print("Please run merge_and_dedupe.py first to create books.csv")
        return
    
    print(f"Loading {books_csv}...")
    books = read_csv_safe(str(books_csv))
    
    if not books:
        print("No books found in CSV.")
        return
    
    print(f"Loaded {len(books)} books\n")
    
    recommendations = generate_recommendations(books, num_recommendations=num_recs, query=args.query)
    print_recommendations(recommendations)
    
    if recommendations:
        print("\n💡 Tip: These recommendations are based on your anchor books' genres/tags and preferences.")
        print("   The more anchor books you enrich, the better the recommendations!")


if __name__ == '__main__':
    main()

