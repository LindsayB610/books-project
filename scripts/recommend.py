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


def extract_preferences(positive_anchors: List[Dict], negative_anchors: List[Dict]) -> Dict:
    """
    Extract preference patterns from anchor books.
    Returns dict with positive genres (from favorites/hits) and negative genres (from misses/dnf).
    """
    positive_genres = set()
    negative_genres = set()
    
    # Extract genres from positive anchors (all_time_favorite, recent_hit)
    for book in positive_anchors:
        genres_str = book.get('genres', '').strip()
        if genres_str:
            # Handle both comma and pipe delimiters
            for genre in genres_str.replace('|', ',').split(','):
                genre_clean = genre.strip().lower()
                if genre_clean:
                    positive_genres.add(genre_clean)
    
    # Extract genres from negative anchors (recent_miss, dnf)
    for book in negative_anchors:
        genres_str = book.get('genres', '').strip()
        if genres_str:
            for genre in genres_str.replace('|', ',').split(','):
                genre_clean = genre.strip().lower()
                if genre_clean:
                    negative_genres.add(genre_clean)
    
    return {
        'positive_genres': positive_genres,
        'negative_genres': negative_genres
    }


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
    Score a book based on tag/genre overlap with anchor_type preferences.
    Scoring: positive_genres (from all_time_favorite, recent_hit) minus negative_genres (from recent_miss, dnf)
    Returns (score, reasons) tuple where score is 0.0 to 1.0 and reasons is a list of strings.
    """
    score = 0.0
    reasons = []
    
    # Query matching (if provided) - boosts score but doesn't guarantee inclusion
    if query:
        query_lower = query.lower()
        title = (book.get('title', '') or '').lower()
        author = (book.get('author', '') or '').lower()
        if query_lower in title or query_lower in author:
            score += 0.3
            reasons.append(f"Matches query: '{query}'")
    
    # Extract book genres/tags (handle both comma and pipe delimiters)
    book_genres = set()
    genres_str = book.get('genres', '').strip()
    if genres_str:
        for genre in genres_str.replace('|', ',').split(','):
            genre_clean = genre.strip().lower()
            if genre_clean:
                book_genres.add(genre_clean)
    
    if not book_genres:
        # No genres to match - minimal score
        if score == 0.0:
            score = 0.01
        return (score, reasons)
    
    # Positive genre overlap (from all_time_favorite, recent_hit)
    positive_genres = preferences.get('positive_genres', set())
    if positive_genres:
        positive_overlap = book_genres & positive_genres
        if positive_overlap:
            # Score based on overlap ratio
            overlap_ratio = len(positive_overlap) / max(len(book_genres), len(positive_genres))
            positive_score = overlap_ratio * 0.7  # Up to 0.7 points
            score += positive_score
            overlap_list = list(positive_overlap)[:3]
            reasons.append(f"Matches favorite genres: {', '.join(overlap_list)}")
    
    # Negative genre overlap (from recent_miss, dnf) - subtracts from score
    negative_genres = preferences.get('negative_genres', set())
    if negative_genres:
        negative_overlap = book_genres & negative_genres
        if negative_overlap:
            # Penalize for matching genres you didn't like
            overlap_ratio = len(negative_overlap) / max(len(book_genres), len(negative_genres))
            negative_penalty = overlap_ratio * 0.4  # Up to -0.4 points
            score -= negative_penalty
            overlap_list = list(negative_overlap)[:2]
            reasons.append(f"Warning: also matches disliked genres: {', '.join(overlap_list)}")
    
    # Ensure score is non-negative
    score = max(0.0, score)
    
    # If no matches at all, give minimal score
    if score == 0.0:
        score = 0.01
        reasons.append("No genre overlap with preferences")
    
    return (min(1.0, score), reasons)


def generate_recommendations(books: List[Dict], num_recommendations: int = 5, query: str = None) -> List[Tuple[Dict, float, List[str]]]:
    """
    Generate book recommendations based on anchor books.
    Scoring: tag/genre overlap with anchor_type in {all_time_favorite, recent_hit} 
    minus overlap with {recent_miss, dnf}
    Returns list of (book, score, reasons) tuples.
    """
    # Load anchor books
    anchors_by_type = load_anchor_books(books)
    
    # Positive anchors (what user likes)
    positive_anchors = anchors_by_type['all_time_favorite'] + anchors_by_type['recent_hit']
    
    # Negative anchors (what user doesn't like)
    negative_anchors = anchors_by_type['recent_miss'] + anchors_by_type['dnf']
    
    if not positive_anchors:
        print("⚠️  No anchor books found (all_time_favorite or recent_hit).")
        print("   Please enrich some books with anchor_type in books.csv")
        return []
    
    print(f"📚 Found {len(positive_anchors)} positive anchor book(s)")
    if negative_anchors:
        print(f"   Found {len(negative_anchors)} negative anchor book(s) (to avoid)")
    
    # Extract preferences (positive and negative genres)
    preferences = extract_preferences(positive_anchors, negative_anchors)
    
    print(f"   Preferences extracted:")
    if preferences['positive_genres']:
        print(f"   - Favorite genres/tags: {', '.join(list(preferences['positive_genres'])[:5])}")
    if preferences['negative_genres']:
        print(f"   - Disliked genres/tags: {', '.join(list(preferences['negative_genres'])[:5])}")
    
    # Build exclude set (all anchor books)
    all_anchors = positive_anchors + negative_anchors
    exclude_titles = {f"{b.get('title', '')}|{b.get('author', '')}" for b in all_anchors}
    
    # Find candidates (unread/want_to_read/reading only)
    candidates = find_candidate_books(books, preferences, exclude_titles, query)
    
    if not candidates:
        print("⚠️  No candidate books found (all books are read or are anchor books)")
        if query:
            print(f"   (filtered by query: '{query}')")
        return []
    
    print(f"   Found {len(candidates)} candidate book(s)")
    if query:
        print(f"   (filtered by query: '{query}')")
    
    # Score candidates using tag/genre overlap
    scored = []
    for book in candidates:
        score, reasons = score_book(book, preferences, query)
        scored.append((book, score, reasons))
    
    # Sort by score (highest first)
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

