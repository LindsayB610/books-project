# Sources Directory

Place your input data files here:

- **`goodreads_export.csv`** - Export from Goodreads (My Books → Import and export → Export library)
- **`kindle_library.csv`** or **`kindle_library.json`** - Your Kindle library data
- **`physical_shelf_photos/`** - Photos of your physical bookshelves (for future OCR processing)

## Notes

- Source data files are gitignored to protect your personal information
- Only place input files here - the pipeline will process them and write to `books.csv` in the project root
- See `../README.md` for instructions on how to use these files

