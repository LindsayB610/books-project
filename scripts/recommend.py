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
    Returns dict with positive genres/tags, tones, vibes (from favorites/hits) 
    and negative genres, tones, vibes, pet_peeves (from misses/dnf).
    """
    positive_genres = set()
    positive_tones = set()
    positive_vibes = set()
    negative_genres = set()
    negative_tones = set()
    negative_vibes = set()
    negative_pet_peeves = set()
    
    # Extract from positive anchors (all_time_favorite, recent_hit)
    for book in positive_anchors:
        # Tags (preferred) and genres (fallback for future enrichment)
        tags_str = book.get('tags', '').strip()
        if tags_str:
            for tag in tags_str.split('|'):
                tag_clean = tag.strip().lower()
                if tag_clean:
                    positive_genres.add(tag_clean)
        
        # Also check genres (for future enrichment)
        genres_str = book.get('genres', '').strip()
        if genres_str:
            for genre in genres_str.split('|'):
                genre_clean = genre.strip().lower()
                if genre_clean:
                    positive_genres.add(genre_clean)
        
        # Tones
        tone = book.get('tone', '').strip()
        if tone:
            positive_tones.add(tone.lower())
        
        # Vibes
        vibe = book.get('vibe', '').strip()
        if vibe:
            positive_vibes.add(vibe.lower())
    
    # Extract from negative anchors (recent_miss, dnf)
    for book in negative_anchors:
        # Tags (preferred) and genres (fallback for future enrichment)
        tags_str = book.get('tags', '').strip()
        if tags_str:
            for tag in tags_str.split('|'):
                tag_clean = tag.strip().lower()
                if tag_clean:
                    negative_genres.add(tag_clean)
        
        # Also check genres (for future enrichment)
        genres_str = book.get('genres', '').strip()
        if genres_str:
            for genre in genres_str.split('|'):
                genre_clean = genre.strip().lower()
                if genre_clean:
                    negative_genres.add(genre_clean)
        
        # Tones
        tone = book.get('tone', '').strip()
        if tone:
            negative_tones.add(tone.lower())
        
        # Vibes
        vibe = book.get('vibe', '').strip()
        if vibe:
            negative_vibes.add(vibe.lower())
        
        # Pet peeves
        pet_peeves = book.get('pet_peeves', '').strip()
        if pet_peeves:
            # Split by common delimiters
            for peeve in pet_peeves.replace(';', ',').split(','):
                peeve_clean = peeve.strip().lower()
                if peeve_clean:
                    negative_pet_peeves.add(peeve_clean)
    
    return {
        'positive_genres': positive_genres,
        'positive_tones': positive_tones,
        'positive_vibes': positive_vibes,
        'negative_genres': negative_genres,
        'negative_tones': negative_tones,
        'negative_vibes': negative_vibes,
        'negative_pet_peeves': negative_pet_peeves
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
    Score a book based on tag/genre overlap + tone/vibe matching with anchor_type preferences.
    Scoring: positive anchors (genres/tags/tones/vibes) minus negative anchors (genres/tones/vibes/pet_peeves)
    Query keywords boost matching tags/genres.
    Returns (score, reasons) tuple where score is 0.0 to 1.0 and reasons is a list of strings.
    """
    score = 0.0
    reasons = []
    
    # Extract query keywords (simple word extraction)
    query_keywords = set()
    if query:
        query_lower = query.lower()
        # Extract words from query
        for word in query_lower.split():
            # Remove common stop words
            if word not in ['i', 'am', 'looking', 'for', 'an', 'a', 'the', 'to', 'get', 'into', 'want', 'something', 'but', 'not']:
                query_keywords.add(word)
    
    # Query matching in title/author (if provided)
    if query:
        query_lower = query.lower()
        title = (book.get('title', '') or '').lower()
        author = (book.get('author', '') or '').lower()
        if query_lower in title or query_lower in author:
            score += 0.2
            reasons.append(f"Matches query: '{query}'")
    
    # Extract book tags (preferred) and genres (fallback)
    # Handle both comma and pipe delimiters
    book_genres = set()
    
    # Prefer tags (user shelves/labels)
    tags_str = book.get('tags', '').strip()
    if tags_str:
        for tag in tags_str.split('|'):
            tag_clean = tag.strip().lower()
            if tag_clean:
                book_genres.add(tag_clean)
    
    # Also check genres (for future enrichment)
    genres_str = book.get('genres', '').strip()
    if genres_str:
        for genre in genres_str.split('|'):
            genre_clean = genre.strip().lower()
            if genre_clean:
                book_genres.add(genre_clean)
    
    # Extract book tone and vibe
    book_tone = (book.get('tone', '') or '').strip().lower()
    book_vibe = (book.get('vibe', '') or '').strip().lower()
    
    # Query keyword boost: if query keywords match genres/tags, boost score
    if query_keywords and book_genres:
        keyword_matches = query_keywords & book_genres
        if keyword_matches:
            score += 0.3
            reasons.append(f"Query keywords match: {', '.join(list(keyword_matches)[:2])}")
    
    # Positive genre/tag overlap (from all_time_favorite, recent_hit)
    positive_genres = preferences.get('positive_genres', set())
    if positive_genres and book_genres:
        positive_overlap = book_genres & positive_genres
        if positive_overlap:
            overlap_ratio = len(positive_overlap) / max(len(book_genres), len(positive_genres))
            positive_score = overlap_ratio * 0.5  # Up to 0.5 points
            score += positive_score
            overlap_list = list(positive_overlap)[:3]
            reasons.append(f"Matches favorite tags: {', '.join(overlap_list)}")
    
    # Positive tone/vibe matching (simple substring match)
    positive_tones = preferences.get('positive_tones', set())
    positive_vibes = preferences.get('positive_vibes', set())
    
    if book_tone:
        for tone in positive_tones:
            if tone in book_tone or book_tone in tone:
                score += 0.15
                reasons.append(f"Matches favorite tone: {tone}")
                break  # Only count once
    
    if book_vibe:
        for vibe in positive_vibes:
            if vibe in book_vibe or book_vibe in vibe:
                score += 0.15
                reasons.append(f"Matches favorite vibe: {vibe}")
                break  # Only count once
    
    # Negative genre/tag overlap (from recent_miss, dnf) - subtracts from score
    negative_genres = preferences.get('negative_genres', set())
    if negative_genres and book_genres:
        negative_overlap = book_genres & negative_genres
        if negative_overlap:
            overlap_ratio = len(negative_overlap) / max(len(book_genres), len(negative_genres))
            negative_penalty = overlap_ratio * 0.3  # Up to -0.3 points
            score -= negative_penalty
            overlap_list = list(negative_overlap)[:2]
            reasons.append(f"Warning: matches disliked tags/genres: {', '.join(overlap_list)}")
    
    # Negative tone/vibe/pet_peeves matching (simple substring match)
    negative_tones = preferences.get('negative_tones', set())
    negative_vibes = preferences.get('negative_vibes', set())
    negative_pet_peeves = preferences.get('negative_pet_peeves', set())
    
    # Check book fields against negative preferences
    book_text = f"{book_tone} {book_vibe}".lower()
    for tone in negative_tones:
        if tone in book_text:
            score -= 0.2
            reasons.append(f"Warning: matches disliked tone: {tone}")
            break
    
    for vibe in negative_vibes:
        if vibe in book_text:
            score -= 0.2
            reasons.append(f"Warning: matches disliked vibe: {vibe}")
            break
    
    for peeve in negative_pet_peeves:
        if peeve in book_text:
            score -= 0.15
            reasons.append(f"Warning: matches pet peeve: {peeve}")
            break
    
    # Ensure score is non-negative
    score = max(0.0, score)
    
    # If no matches at all, give minimal score
    if score == 0.0:
        score = 0.01
        reasons.append("No overlap with preferences")
    
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
        tags = book.get('tags', 'N/A')
        genres = book.get('genres', 'N/A')
        isbn13 = book.get('isbn13', 'N/A')
        
        print(f"{idx}. {title}")
        print(f"   by {author}")
        if tags and tags != 'N/A':
            print(f"   Tags: {tags}")
        elif genres and genres != 'N/A':
            print(f"   Genres: {genres}")
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
    parser.add_argument('--dataset', type=str, default='datasets/default',
                       help='Dataset root directory (default: datasets/default)')
    parser.add_argument('--csv', type=str, help='Path to books.csv (overrides --dataset)')
    
    args = parser.parse_args()
    
    # Limit to 3-5 recommendations
    num_recs = max(3, min(5, args.limit))
    
    project_root = Path(__file__).parent.parent
    if args.csv:
        books_csv = Path(args.csv)
    else:
        dataset_root = project_root / args.dataset
        books_csv = dataset_root / 'books.csv'
    
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

