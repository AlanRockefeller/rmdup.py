# Changelog

## Version 1.1 - March 30, 2025

### Added
- Progress bar for processing large file collections
  - Shows automatically when processing >250MB of files or >250 files
  - Includes file processing status, speed, and estimated time remaining
  - Updates every 0.1 seconds for smooth display
- Symbolic link support
  - Added `-L` / `--follow-links` flag to follow symbolic links (default: don't follow)
  - Properly identifies and handles symbolic links throughout the codebase
- Disk space tracking
  - Shows total space saved when files are deleted
  - Shows per-group disk space freed in interactive mode
  - Uses human-readable formats (KB, MB, GB, etc.)
- File statistics
  - Shows total file count and disk space usage after scanning
  - Provides detailed duplicate statistics including number of duplicate files and groups
  - Shows statistics even when no duplicates are found
- Minimum file size filter
  - Added `-s` / `--min-size` option to skip files below a specified size
  - Supports human-readable formats (KB, MB, GB, etc.)
  - Shows summary of how many small files were skipped
- Better command-line help
  - Added detailed description of what the script does
  - Improved command line argument descriptions
  - Added usage examples and file selection strategy explanation
- Better error handling
  - More informative error messages for unknown command line arguments
  - Improved handling of errors during file processing
  - Added helpful fallbacks when tqdm library is not available

### Changed
- Increased progress bar appearance threshold from 100MB to 250MB
- Added file count threshold (>250 files) as an alternative trigger for progress bar
- Improved display of matched duplicate files
  - Shows which file is a duplicate of which other file
  - Displays file sizes in human-readable format
- Optimized file checksum calculations for better performance

### Fixed
- Fixed interactive mode user interface
  - Better formatting of file group displays
  - Clearer information about original vs. duplicate files
  - Improved handling of user input for file selection
- Fixed error handling for invalid command line arguments
- Fixed progress bar output in verbose mode
  - Eliminated duplicate progress bar displays
  - Better integration of verbose output with progress information

## Version 1.0 - July 25, 2024

### Initial Release
- Basic duplicate file finding functionality
- MD5-based file comparison
- Interactive and batch mode operation
- Parenthesis-based file deletion priority
