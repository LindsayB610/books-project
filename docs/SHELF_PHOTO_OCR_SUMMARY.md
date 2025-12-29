# Shelf Photo OCR Ingestion Implementation

**Date:** January 2025  
**Feature:** Physical Shelf Photo OCR

---

## Overview

Implemented `scripts/ingest_shelf_photos.py` to extract book titles and authors from photos of bookshelves using OCR (Optical Character Recognition).

This feature was planned as a "future" feature in `PROJECT_BACKGROUND.md` and enables users to inventory their physical books by taking photos.

---

## What Was Built

### New Script: `scripts/ingest_shelf_photos.py`

A script that:
- Accepts image file(s) of bookshelves (JPEG, PNG, etc.)
- Uses OCR (pytesseract) to extract text from images
- Parses titles and authors from extracted text using heuristics
- Creates canonical entries and marks `physical_owned=1`
- Writes to `sources/shelves_canonical.csv` for integration with merge pipeline

### Dependencies Added

- `pillow>=9.0.0` - Image processing
- `pytesseract>=0.3.10` - OCR wrapper

**Note:** Also requires Tesseract OCR to be installed on the system:
- macOS: `brew install tesseract`
- Linux: `sudo apt-get install tesseract-ocr`
- Windows: Download from https://github.com/tesseract-ocr/tesseract

---

## Usage

### Basic Usage

```bash
# Process single image
python scripts/ingest_shelf_photos.py --dataset datasets/lindsay shelf1.jpg

# Process multiple images
python scripts/ingest_shelf_photos.py --dataset datasets/lindsay shelf1.jpg shelf2.jpg shelf3.jpg

# Dry run to see what would be extracted
python scripts/ingest_shelf_photos.py --dataset datasets/lindsay --dry-run shelf1.jpg

# Process all images in directory
python scripts/ingest_shelf_photos.py --dataset datasets/lindsay shelves/*.jpg
```

### Workflow

1. Take photos of your bookshelves
2. Run OCR script to extract books:
   ```bash
   python scripts/ingest_shelf_photos.py --dataset datasets/lindsay shelf1.jpg
   ```
3. Review the extracted books in `sources/shelves_canonical.csv`
4. Run merge pipeline to add to `books.csv`:
   ```bash
   python scripts/merge_and_dedupe.py --dataset datasets/lindsay
   ```
5. The merge pipeline will:
   - Deduplicate against existing books
   - Mark `physical_owned=1` on matched books
   - Add new books from shelf photos

---

## How It Works

### 1. Image Processing
- Uses PIL (Pillow) to load and process images
- Configures pytesseract for better book spine reading (single column, vertical text)

### 2. Text Extraction
- Extracts raw text from images using OCR
- Handles various image formats (JPEG, PNG, etc.)

### 3. Book Parsing (Heuristic)
The script uses heuristics to parse book titles and authors from OCR text:

**Supported Patterns:**
- `"Title by Author"` - Most common pattern
- `"Title - Author"` or `"Title – Author"` - Alternative format
- `"Title\nAuthor"` - Title and author on separate lines
- `"Title"` only - Author missing or on next line

**Challenges:**
- Book spines vary widely in format
- OCR accuracy depends on image quality, lighting, font
- Vertical text on spines can be difficult for OCR
- Some books have decorative fonts that OCR struggles with

### 4. Canonical Entry Creation
- Creates entries with `physical_owned=1`
- Sets `sources=shelves`
- Leaves other metadata empty (can be enriched later)
- Uses standard canonical schema

### 5. Integration with Merge Pipeline
- Writes to `sources/shelves_canonical.csv`
- `merge_and_dedupe.py` now loads shelf canonical data
- Merges with existing books using standard deduplication logic
- Updates `physical_owned` flag on matched books

---

## Limitations & Considerations

### OCR Accuracy
- **Image quality matters**: Clear, well-lit photos work best
- **Font matters**: Decorative fonts, small text, or unusual orientations reduce accuracy
- **Parsing is heuristic**: The script tries to identify title/author patterns, but may miss or incorrectly parse some books

### What Works Best
- Clear photos with good lighting
- Books with standard fonts
- Photos taken straight-on (not angled)
- Books with clear title/author formatting

### What May Not Work
- Very decorative fonts
- Very small text
- Poor lighting or blurry photos
- Books where title/author are unclear
- Books with unusual formatting

### Manual Review Recommended
- **Always review** the extracted books in `sources/shelves_canonical.csv`
- The merge pipeline will deduplicate, but manual review helps catch parsing errors
- You can manually edit `shelves_canonical.csv` before running merge

---

## Design Principles

### Safety First
- Writes to separate canonical file (doesn't modify `books.csv` directly)
- Dry-run mode for safe preview
- Merge pipeline handles deduplication safely

### Incremental
- Can process photos incrementally
- Safe to run multiple times
- Merge pipeline handles duplicates

### User Control
- User reviews extracted books before merge
- Manual edits to canonical file are preserved
- Merge pipeline respects protected fields

---

## Files Changed

### Created
- `scripts/ingest_shelf_photos.py` - Main OCR ingestion script

### Modified
- `scripts/merge_and_dedupe.py` - Added shelf canonical loading
- `requirements.txt` - Added pillow and pytesseract dependencies
- `README.md` - Added shelf photo ingestion documentation

---

## Future Enhancements (Optional)

Potential improvements:
1. **Image preprocessing**: Better image enhancement for OCR (contrast, rotation correction)
2. **Better parsing**: Machine learning or more sophisticated heuristics for title/author extraction
3. **Spine detection**: Detect and crop individual book spines from full shelf photos
4. **Confidence scoring**: Score OCR confidence and flag low-confidence extractions
5. **ISBN lookup**: Attempt to match extracted titles to ISBNs for better deduplication

---

## Tips for Best Results

1. **Take clear photos**: Good lighting, in focus, straight-on angle
2. **One shelf at a time**: Process photos of individual shelves for better OCR accuracy
3. **Review results**: Always check `shelves_canonical.csv` before merging
4. **Edit if needed**: You can manually edit the canonical file to fix parsing errors
5. **Use dry-run first**: Preview what will be extracted before processing

---

## Example Workflow

```bash
# 1. Take photos of your bookshelves
# (Save as shelf1.jpg, shelf2.jpg, etc.)

# 2. Process photos (dry run first)
python scripts/ingest_shelf_photos.py --dataset datasets/lindsay --dry-run shelf1.jpg

# 3. Review output - if it looks good, run without --dry-run
python scripts/ingest_shelf_photos.py --dataset datasets/lindsay shelf1.jpg shelf2.jpg

# 4. Review extracted books
cat datasets/lindsay/sources/shelves_canonical.csv

# 5. Edit if needed (fix parsing errors)
# (Manually edit shelves_canonical.csv)

# 6. Merge into books.csv
python scripts/merge_and_dedupe.py --dataset datasets/lindsay

# 7. Validate
python scripts/validate_books_csv.py --dataset datasets/lindsay
```

---

## Summary

The shelf photo OCR feature enables users to inventory physical books by taking photos. While OCR accuracy depends on image quality, the feature provides a practical way to capture physical inventory that integrates safely with the existing merge pipeline.

**Key Points:**
- ✅ Extracts books from photos using OCR
- ✅ Marks `physical_owned=1` 
- ✅ Integrates with merge pipeline
- ✅ Safe and incremental
- ⚠️ Accuracy depends on image quality
- ⚠️ Manual review recommended

