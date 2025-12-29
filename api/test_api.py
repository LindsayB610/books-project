#!/usr/bin/env python3
"""
Simple test script to verify API endpoints work.
Run this after starting the server.
"""

import requests
import json

BASE_URL = "http://localhost:8000"


def test_root():
    """Test root endpoint."""
    print("Testing root endpoint...")
    response = requests.get(f"{BASE_URL}/")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()


def test_list_books():
    """Test list books endpoint."""
    print("Testing GET /api/books...")
    response = requests.get(f"{BASE_URL}/api/books", params={"limit": 5})
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Total books: {data.get('total')}")
    print(f"Returned: {len(data.get('books', []))}")
    if data.get('books'):
        print(f"First book: {data['books'][0].get('title')} by {data['books'][0].get('author')}")
    print()


def test_search():
    """Test search endpoint."""
    print("Testing GET /api/books/search...")
    response = requests.get(f"{BASE_URL}/api/books/search", params={"q": "witches", "limit": 3})
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Query: {data.get('query')}")
    print(f"Results: {data.get('total')}")
    if data.get('results'):
        for book in data['results'][:3]:
            print(f"  - {book.get('title')} by {book.get('author')}")
    print()


def test_stats():
    """Test stats endpoint."""
    print("Testing GET /api/stats...")
    response = requests.get(f"{BASE_URL}/api/stats")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Total books: {data.get('total_books')}")
    print(f"Read: {data.get('read')}")
    print(f"Unread: {data.get('unread')}")
    print(f"Anchor books: {data.get('anchor_books')}")
    print()


def test_filter_options():
    """Test filter options endpoint."""
    print("Testing GET /api/filters/options...")
    response = requests.get(f"{BASE_URL}/api/filters/options")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Read statuses: {len(data.get('read_statuses', []))}")
    print(f"Genres: {len(data.get('genres', []))}")
    print(f"Tones: {len(data.get('tones', []))}")
    print()


def test_recommendations():
    """Test recommendations endpoint."""
    print("Testing POST /api/recommendations...")
    payload = {
        "query": "fantasy",
        "limit": 3
    }
    response = requests.post(f"{BASE_URL}/api/recommendations", json=payload)
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Recommendations: {len(data)}")
    for rec in data[:3]:
        print(f"  - {rec.get('title')} by {rec.get('author')}")
        print(f"    Why: {rec.get('why', 'N/A')[:80]}...")
    print()


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Books API")
    print("=" * 60)
    print()
    
    try:
        test_root()
        test_list_books()
        test_search()
        test_stats()
        test_filter_options()
        test_recommendations()
        
        print("=" * 60)
        print("All tests completed!")
        print("=" * 60)
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to API server.")
        print("Make sure the server is running:")
        print("  python -m api.server")
        print("  or")
        print("  uvicorn api.server:app --reload")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

