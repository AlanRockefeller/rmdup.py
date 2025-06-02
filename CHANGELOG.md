# Changelog

## Version 1.2.0 - April 15, 2025

### Added
- **Comprehensive Unit Tests:** Introduced a new test suite (`test_rmdup.py`) with `unittest` to cover key functionalities including argument parsing (`parse_size`), size formatting (`get_human_size`), deletion prioritization (`prioritize_deletion`), and MD5 calculation (`get_md5`).
- **Content Sample Refinement (Interactive Mode):**
    - Smarter detection of binary/unrenderable content for file samples.
    - Displays a generic message (e.g., "Binary file or unrenderable content") instead of garbled text if a high percentage of replacement characters is detected in the UTF-8 decoded sample.

### Changed
- **Argument Parsing for `--min-size` / `-s`:** Internally refactored for improved robustness and direct use of `argparse` capabilities, maintaining existing user-facing syntax.
- **File Deletion Prioritization Logic (`prioritize_deletion`):**
    - Enhanced the logic to more reliably select a single "best" file to keep from duplicate sets.
    - The primary kept candidate is the oldest file that does not have parentheses in its filename.
    - If all files have parentheses or none do, the oldest among them is kept.
    - `match_info` now consistently maps each deleted file to the single kept master file.
- **Interactive Mode (`interactive_delete` & `get_user_choice`):**
    - Now clearly highlights a "[recommended to keep]" file in each duplicate group, based on the refined prioritization logic.
    - The "all" option in the deletion prompt now correctly means "delete all except the recommended file."
- **Output Messages (Non-Interactive Mode):** Improved clarity of messages when listing files proposed for deletion, indicating *why* a file is kept (e.g., older, no parentheses).
- **Verbose Logging:** Refined interaction between progress bar and verbose messages for cleaner output. `ProgressBar.set_description` now ensures its verbose output ends with a newline.
- **Symlink Logging:** Messages for skipping symlinks now include "(not following)" for better clarity.

### Removed
- **`get_file_size` function:** This function (which returned human-readable size strings) was removed after its usages were refactored to use `os.path.getsize` combined with `get_human_size`.

### Fixed
- Minor code style issues and clarity by introducing constants for magic numbers (e.g., `DEFAULT_CHUNK_SIZE`, `CONTENT_SAMPLE_SIZE`).

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
