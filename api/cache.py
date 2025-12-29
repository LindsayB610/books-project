"""
Simple in-memory cache for books.csv data.
Refreshes on each request (can be enhanced later with file watching).
"""

from typing import List, Dict, Optional
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.csv_utils import read_csv_safe


class BooksCache:
    """
    Simple cache for books.csv data.
    Reads fresh on each request (stateless).
    Can be enhanced later with file watching or TTL.
    """
    
    def __init__(self, dataset_path: str = "datasets/default"):
        self.dataset_path = Path(dataset_path)
        self._books: Optional[List[Dict]] = None
    
    def get_books(self) -> List[Dict]:
        """
        Get all books from books.csv.
        Reads fresh each time (stateless API design).
        """
        books_csv = self.dataset_path / "books.csv"
        if not books_csv.exists():
            return []
        
        books = read_csv_safe(str(books_csv))
        return books
    
    def refresh(self):
        """Force refresh of cache (for future use)."""
        self._books = None

