#!/usr/bin/python3

# Version 1.1
# By Alan Rockefeller - March 30, 2025

# This script recursively looks for duplicate files in the current directory and offers to delete them.
# If you give it the -i option it asks about each file - if you don't it lists all the files it plans to delete and lets you decide if you want to go ahead.

# It prioritizes deleting duplicate newer files and those with parenthesis, as these are often extra files that were downloaded or saved, and it's usually best to keep the original filename rather than the one with (1) or (2), etc.

# Version
SCRIPT_VERSION = "1.1"
SCRIPT_DATE = "March 30, 2025"
AUTHOR = "Alan Rockefeller"

# --- Constants ---
DEFAULT_CHUNK_SIZE = 4096
CONTENT_SAMPLE_SIZE = 100
PROGRESS_BAR_FILE_THRESHOLD = 250
PROGRESS_BAR_SIZE_THRESHOLD_BYTES = 250 * 1024 * 1024 # 250 MB

import os
import hashlib
import sys
import time
import argparse
import math
from collections import defaultdict
from argparse import ArgumentParser


def get_human_size(size_bytes):
    """Convert bytes to human readable format."""
    if size_bytes == 0:
        return "0 B"
    size_names = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    size = round(size_bytes / p, 2)
    return f"{size} {size_names[i]}"


def parse_size(size_str):
    """Parse a human-readable size string (like '5MB', '5M', or '2.5GB') into bytes."""
    if not size_str:
        return 0
    
    # Remove any spaces
    size_str = size_str.replace(' ', '')
    
    # Define the units and their multipliers
    units = {
        'B': 1,
        'K': 1024,
        'KB': 1024,
        'M': 1024 ** 2,
        'MB': 1024 ** 2,
        'G': 1024 ** 3,
        'GB': 1024 ** 3,
        'T': 1024 ** 4,
        'TB': 1024 ** 4,
    }
    
    # Check if the string ends with a known unit
    unit = None
    
    # Try to match the units (case-insensitive)
    size_upper = size_str.upper()
    for u in sorted(units.keys(), key=len, reverse=True):  # Sort by length to match longer units first
        if size_upper.endswith(u):
            unit = u
            size_str = size_str[:-len(u)]
            break
    
    # If no unit was found, assume bytes
    if unit is None:
        # Try to see if the last character is numeric
        if size_str and not size_str[-1].isdigit():
            # Last character might be a unit
            possible_unit = size_str[-1].upper()
            if possible_unit in ['K', 'M', 'G', 'T', 'P']:
                unit = possible_unit
                size_str = size_str[:-1]
            else:
                raise ValueError(f"Unrecognized unit in: {size_str}")
        else:
            unit = 'B'
    
    # Convert to float
    try:
        size = float(size_str)
    except ValueError:
        raise ValueError(f"Invalid size format: {size_str}")
    
    # Convert to bytes
    return int(size * units[unit])


class ProgressBar:
    """A text-based progress bar."""
    
    def __init__(self, total, width=50, prefix='Progress:', suffix='Complete', verbose=False):
        self.total = total
        self.width = width
        self.prefix = prefix
        self.suffix = suffix
        self.count = 0
        self.start_time = time.time()
        self.last_update = 0
        self.current_file = ""
        self.verbose = verbose
        self.last_line_length = 0
        self.bar_visible = False
        
    def update(self, progress):
        self.count += progress
        current_time = time.time()
        
        # Update the display every 0.1 seconds to make the progress bar smoother
        if current_time - self.last_update > 0.1 or self.count >= self.total:
            percent = min(100, int(self.count / self.total * 100))
            filled_length = int(self.width * self.count // self.total)
            bar = '█' * filled_length + '-' * (self.width - filled_length)
            
            # Calculate speed and ETA
            elapsed_time = current_time - self.start_time
            if elapsed_time > 0:
                speed = self.count / elapsed_time / (1024 * 1024)  # MB/s
                if self.count < self.total:
                    eta = (self.total - self.count) / (self.count / elapsed_time) if self.count > 0 else 0
                    eta_str = f"ETA: {int(eta // 60)}m {int(eta % 60)}s"
                else:
                    eta_str = f"Time: {int(elapsed_time // 60)}m {int(elapsed_time % 60)}s"
            else:
                speed = 0
                eta_str = "ETA: calculating..."
            
            # Create progress message
            message = f"\r{self.prefix} |{bar}| {percent}% {self.suffix} - {speed:.2f} MB/s - {eta_str}"
            
            # Only update the progress bar if we're not in verbose mode or if we're finishing
            if not self.verbose or self.count >= self.total:
                # Print the progress bar
                sys.stdout.write(message)
                sys.stdout.flush()
                self.bar_visible = True
            
            self.last_update = current_time
    
    def set_description(self, description):
        """Set the current file being processed."""
        self.current_file = description
        # Only display the file in verbose mode
        if self.verbose and self.current_file:
            # If we previously displayed a progress bar but haven't moved to a new line
            if self.bar_visible:
                sys.stdout.write('\n')
                self.bar_visible = False
                
            # Show processing message
            print(f"Processing: {os.path.basename(self.current_file)}") # Ensure newline in verbose
            # sys.stdout.flush() # Generally not needed after a print() with newline
    
    def close(self):
        """Finish the progress bar."""
        # Always make sure we're on a new line when done
        if self.bar_visible:
            sys.stdout.write('\n')
        
        # Add an extra blank line for separation
        if not self.verbose:
            sys.stdout.write('\n')
            
        sys.stdout.flush()


def get_md5(file_path, pbar=None, verbose=False, follow_links=False):
    """Calculate the MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    try:
        # If it's a symlink and we're not following links, handle differently
        if os.path.islink(file_path) and not follow_links:
            if verbose:
                print(f"Skipping symlink (not following): {file_path}")
            return None
            
        with open(file_path, 'rb') as f:
            file_size = os.path.getsize(file_path)
            # chunk_size = 4096 # Replaced by DEFAULT_CHUNK_SIZE
            
            if pbar:
                # Update the progress bar description to show current file
                pbar.set_description(file_path)
            
            for chunk in iter(lambda: f.read(DEFAULT_CHUNK_SIZE), b""):
                hash_md5.update(chunk)
                if pbar:
                    pbar.update(len(chunk))
    except (PermissionError, OSError) as e:
        if verbose:
            print(f"Error accessing file {file_path}: {e}", file=sys.stderr)
        return None
    
    checksum = hash_md5.hexdigest()
    if verbose:
        print(f"MD5 {checksum} - {file_path}")
    return checksum


def find_duplicates(directory, debug=False, verbose=False, follow_links=False, min_size=0):
    """Find duplicate files in the specified directory."""
    checksums = defaultdict(list)
    
    # First, gather all files to check
    all_files = []
    total_size = 0
    skipped_count = 0
    skipped_size = 0
    
    print("Scanning directory for files...")
    
    for root, dirs, files in os.walk(directory, followlinks=follow_links):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                # Skip symlinks if not following links (unless they're directory symlinks already handled by os.walk)
                if os.path.islink(file_path) and not follow_links:
                    if verbose:
                        print(f"Skipping symlink (not following): {file_path}")
                    continue
                
                file_size = os.path.getsize(file_path)
                
                # Skip files smaller than min_size
                if file_size < min_size:
                    skipped_count += 1
                    skipped_size += file_size
                    if verbose:
                        print(f"Skipping small file: {file_path} ({get_human_size(file_size)})")
                    continue
                
                all_files.append((file_path, file_size))
                total_size += file_size
            except (PermissionError, OSError) as e:
                if debug or verbose:
                    print(f"Could not access {file_path}: {e}")
    
    # Display summary of files found
    human_readable_size = get_human_size(total_size)
    print(f"Found {len(all_files)} files totaling {human_readable_size}")
    
    if skipped_count > 0:
        print(f"Skipped {skipped_count} files below size threshold ({get_human_size(skipped_size)}) of files")
    
    # Show progress if total file size is larger than threshold OR if there are more than threshold files
    use_progress = (total_size > PROGRESS_BAR_SIZE_THRESHOLD_BYTES) or \
                   (len(all_files) > PROGRESS_BAR_FILE_THRESHOLD)
    
    if use_progress:
        print(f"Need to process {len(all_files)} files totaling {total_size / (1024 * 1024):.2f} MB")
        
        pbar = ProgressBar(total=total_size, prefix='Progress:', suffix='Processed', verbose=verbose)
        for file_path, _ in all_files:
            if debug and verbose:
                print(f"Calculating checksum for: {file_path}")
            file_checksum = get_md5(file_path, pbar, verbose, follow_links)
            if file_checksum:  # Only add if checksum was calculated successfully
                checksums[file_checksum].append(file_path)
        pbar.close()
    else:
        for file_path, _ in all_files:
            if debug and verbose:
                print(f"Calculating checksum for: {file_path}")
            file_checksum = get_md5(file_path, None, verbose, follow_links)
            if file_checksum:  # Only add if checksum was calculated successfully
                checksums[file_checksum].append(file_path)
    
    duplicates = {k: v for k, v in checksums.items() if len(v) > 1}
    
    # Show statistics even if no duplicates are found
    if not duplicates:
        print("No duplicate files found in the scanned files.")
    else:
        duplicate_count = sum(len(files) for files in duplicates.values())
        duplicate_file_count = len(duplicates)
        print(f"Found {duplicate_count} duplicate files in {duplicate_file_count} groups.")
    
    return duplicates


def delete_files(files, follow_links=False):
    """Actually delete the files."""
    total_deleted = 0
    total_bytes_saved = 0
    
    for file in files:
        try:
            # Handle symlinks specially if not following links
            if os.path.islink(file) and not follow_links:
                print(f"Skipping symlink (not following): {file}")
                continue
            
            # Get file size before deletion
            try:
                file_size = os.path.getsize(file)
                total_bytes_saved += file_size
            except (PermissionError, OSError):
                # If we can't get size, just continue
                pass
                
            os.remove(file)
            print(f"Deleted: {file}")
            total_deleted += 1
        except FileNotFoundError:
            print(f"File not found: {file}")
        except Exception as e:
            print(f"Error deleting file {file}: {e}")
    
    # Calculate human-readable size
    human_size = get_human_size(total_bytes_saved)
    
    # Show summary
    print(f"\nTotal files deleted: {total_deleted}")
    print(f"Disk space freed: {human_size}")
    
    return total_deleted, total_bytes_saved


def prioritize_deletion(duplicates, debug=False):
    """
    Prioritize which duplicate files to delete, aiming to keep the best single copy.
    The "best" copy is typically the oldest file that does not have parentheses in its name.
    """
    all_files_to_delete = []
    match_info = {}  # Maps deleted_file_path -> kept_file_path

    for checksum, paths in duplicates.items():
        if not paths:
            continue

        if debug:
            print(f"\nProcessing group for checksum: {checksum}")
            print(f"Paths in current group: {paths}")

        # Separate files by parenthesis in basename
        with_paren = []
        without_paren = []
        for p in paths:
            if any(char in '()' for char in os.path.basename(p)):
                with_paren.append(p)
            else:
                without_paren.append(p)

        if debug:
            print(f"Files without parentheses: {without_paren}")
            print(f"Files with parentheses: {with_paren}")

        file_to_keep = None
        current_group_files_to_delete = []

        if without_paren:
            # Scenario 1: At least one file without parentheses. Keep the oldest of these.
            without_paren.sort(key=lambda p: os.path.getmtime(p))
            file_to_keep = without_paren[0]
            current_group_files_to_delete.extend(without_paren[1:]) # Add newer non-parenthesis files
            current_group_files_to_delete.extend(with_paren)      # Add all parenthesis files
        else:
            # Scenario 2: All files have parentheses (or list was empty, though caught by `if not paths`)
            # Keep the oldest among them.
            paths.sort(key=lambda p: os.path.getmtime(p))
            file_to_keep = paths[0]
            current_group_files_to_delete.extend(paths[1:])

        if debug:
            print(f"File chosen to keep: {file_to_keep}")
            print(f"Files in this group to delete: {current_group_files_to_delete}")

        # Populate match_info for this group and add to overall deletion list
        if file_to_keep: # Should always be true if paths is not empty
            for f_del in current_group_files_to_delete:
                if f_del == file_to_keep: # Should not happen with correct logic
                    if debug: print(f"Error: File to keep ({file_to_keep}) is also in deletion list ({f_del})")
                    continue
                match_info[f_del] = file_to_keep
                all_files_to_delete.append(f_del)
    
    if debug:
        print("\nFinal files_to_delete list:", all_files_to_delete)
        print("Final match_info map:", match_info)
        
    return all_files_to_delete, match_info


def get_file_info(file_path):
    """Get detailed file information including size and modification time."""
    try:
        # Get raw size in bytes
        raw_size = os.path.getsize(file_path)
        # Convert to human-readable format
        size_str = get_human_size(raw_size)
        mtime = os.path.getmtime(file_path)
        mtime_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(mtime))
        return f"{size_str}, modified: {mtime_str}"
    except (PermissionError, OSError):
        # This will catch errors from os.path.getsize() or os.path.getmtime()
        return "Unknown info"


def get_user_choice(files):
    """Show files to user and ask them what to delete, highlighting a recommended file to keep."""
    if not files:
        return []

    # Determine the recommended file to keep
    with_paren = []
    without_paren = []
    for p in files:
        if any(char in '()' for char in os.path.basename(p)):
            with_paren.append(p)
        else:
            without_paren.append(p)

    best_file_to_keep = None
    # Sort by modification time for consistent ordering in choice list
    # and for finding the oldest if needed.
    # We still need sorted_files for presenting the numbered list.
    # The best_file_to_keep logic should use unsorted lists then sort them.
    
    temp_sorted_files = sorted(files, key=lambda p: os.path.getmtime(p))


    if without_paren:
        without_paren.sort(key=lambda p: os.path.getmtime(p))
        best_file_to_keep = without_paren[0]
    else:
        # All files have parentheses or the list was initially empty (filtered by `if not files`)
        # Sort all files by modification time and pick the oldest.
        # This re-uses temp_sorted_files which is already sorted.
        if temp_sorted_files:
             best_file_to_keep = temp_sorted_files[0]

    print("\nFiles in this group:")
    # Present files sorted by original logic (oldest first overall) for user display
    # This is what sorted_files was doing.
    # Let's ensure the displayed list is consistently sorted, e.g. by path:
    # No, user expects oldest first. So temp_sorted_files is what we should enumerate.
    
    for i, file_path in enumerate(temp_sorted_files, 1):
        file_info = get_file_info(file_path)
        marker = ""
        if file_path == best_file_to_keep:
            marker = "[recommended to keep]"
        elif i == 1 and best_file_to_keep is None: 
            # Fallback if best_file_to_keep logic somehow failed, mark absolute oldest
            # This also covers the case where all files are without_paren and best_file_to_keep is temp_sorted_files[0]
             marker = "[oldest, consider keeping]" # Should be covered by recommended
        
        # If best_file_to_keep is the first in sorted list, marker will be set.
        # If not, and it's the first, it means it's not the recommended one.
        # The logic for [oldest] is now superseded by [recommended to keep]
        # if best_file_to_keep is indeed the oldest.
        print(f"{i}: {file_path} ({file_info}) {marker}")

    while True:
        try:
            # options_str = "/".join([str(i) for i in range(1, len(temp_sorted_files)+1)])
            # Prompt should reflect new 'all' behavior
            prompt_message = (
                f"\nWhich file(s) would you like to DELETE? "
                f"(Enter numbers, 'all' except recommended, 'none' to keep all): "
            )
            choice = input(prompt_message).strip().lower()
            
            if choice == 'all':
                # Delete all except the best_file_to_keep
                if best_file_to_keep:
                    return [f for f in temp_sorted_files if f != best_file_to_keep]
                else: # Should not happen if files list is not empty
                    return temp_sorted_files[1:] if len(temp_sorted_files) > 1 else []
                
            if choice == 'none' or choice == 'n' or choice == '':
                # Keep all files
                return []
                
            # Parse multiple selections
            try:
                selected_indices = [int(idx) for idx in choice.split()]
                if all(1 <= idx <= len(sorted_files) for idx in selected_indices):
                    # Convert indices to actual files
                    files_to_delete = [sorted_files[idx-1] for idx in selected_indices]
                    return files_to_delete
                else:
                    print(f"Invalid input. Please enter numbers between 1 and {len(sorted_files)}.")
            except ValueError:
                print("Invalid input. Please enter numbers only, 'all', or 'none'.")
        except KeyboardInterrupt:
            print("\nOperation cancelled by user.")
            return []


def interactive_delete(duplicates, follow_links=False):
    """Interactively ask the user for confirmation to delete files."""
    total_deleted = 0
    total_bytes_saved = 0
    
    # Process all checksums
    for checksum, files in duplicates.items():
        if len(files) < 2:
            continue  # Skip if somehow we don't have duplicates
            
        print("\n" + "="*80)
        print(f"Duplicate group: {len(files)} identical files")
        print("="*80)
        
        # Get sample of the file content for better identification
        try:
            sample_file = files[0]  # Use first file for the sample
            file_size = os.path.getsize(sample_file)
            file_type = os.path.splitext(sample_file)[1].lower()
            
            # Try to get the first few bytes of the file to help identify it
            with open(sample_file, 'rb') as f:
                sample_bytes = f.read(min(CONTENT_SAMPLE_SIZE, file_size))
            
            if sample_bytes:
                try:
                    # Try to decode as UTF-8
                    decoded_sample = sample_bytes.decode('utf-8', errors='replace')
                    
                    # Count replacement characters
                    num_bytes = len(sample_bytes)
                    replacement_char_count = decoded_sample.count('\uFFFD')
                    
                    # If more than 25% of original bytes led to replacement characters (or if sample is very short and has any)
                    # or if the decoded sample is empty (which can happen for some binary sequences)
                    if not decoded_sample.strip() or (num_bytes > 0 and replacement_char_count / num_bytes > 0.25) or \
                       (num_bytes <= 4 and replacement_char_count > 0): # Heuristic for very short files
                        print("Content sample: (Binary file or unrenderable content)")
                    else:
                        # Show up to 60 characters of the decoded sample
                        print(f"Content sample: {decoded_sample[:60].replace(chr(0), '[NUL]').strip()}...")
                except Exception:
                    # Catch any other decoding related errors, though decode with 'replace' is quite robust
                    print("Content sample: (Error during content preview)")
            else:
                print("Content sample: (File is empty or very short)")
                
        except Exception as e:
            print(f"Could not display content sample: {e}") # More specific error for sample reading
        
        try:
            # Get user's choice of which files to delete
            files_to_delete = get_user_choice(files)
            
            if files_to_delete:
                print("\nFiles to delete:")
                for file in files_to_delete:
                    print(f"- {file}")
                    
                confirmation = input("Proceed with deletion? (y/n): ").strip().lower()
                if confirmation == 'y':
                    group_deleted = 0
                    group_bytes = 0
                    
                    for file in files_to_delete:
                        try:
                            # Skip symlinks if not following them
                            if os.path.islink(file) and not follow_links:
                                print(f"Skipping symlink (not following): {file}")
                                continue
                            
                            # Get file size before deletion
                            try:
                                file_size = os.path.getsize(file)
                                group_bytes += file_size
                                total_bytes_saved += file_size
                            except (PermissionError, OSError):
                                # If we can't get size, just continue
                                pass
                                
                            os.remove(file)
                            print(f"Deleted: {file}")
                            group_deleted += 1
                            total_deleted += 1
                        except FileNotFoundError:
                            print(f"File not found: {file}")
                        except Exception as e:
                            print(f"Error deleting file {file}: {e}")
                    
                    # Show group summary
                    if group_deleted > 0:
                        print(f"Deleted {group_deleted} files in this group, freed {get_human_size(group_bytes)}")
                else:
                    print("Skipped deletion for this group.")
            else:
                print("No files deleted in this group.")
                
        except KeyboardInterrupt:
            print("\nOperation cancelled by user.")
            return False
    
    # Show final summary
    if total_deleted > 0:
        print(f"\nTotal files deleted: {total_deleted}")
        print(f"Total disk space freed: {get_human_size(total_bytes_saved)}")
    else:
        print("\nNo files were deleted.")
        
    return True


def main(directory, interactive=False, debug=False, verbose=False, follow_links=False, min_size=0):
    try:
        duplicates = find_duplicates(directory, debug, verbose, follow_links, min_size)
        
        # Add a blank line after progress bar completion if verbose
        if verbose:
            print()
        
        if not duplicates:
            # No need to print "No duplicate files found" as find_duplicates already does this
            return

        if interactive:
            print("Interactive mode activated.")
            if not interactive_delete(duplicates, follow_links):
                return
        else:
            files_to_delete, match_info = prioritize_deletion(duplicates, debug or verbose)
            if files_to_delete:
                print("Files proposed for deletion:")
                for file in files_to_delete:
                    try:
                        raw_size = os.path.getsize(file)
                        file_size_str = get_human_size(raw_size)
                    except (PermissionError, OSError):
                        file_size_str = "Unknown size"
                    
                    if file in match_info:
                        kept_file = match_info[file]
                        reason_paren = any(char in '()' for char in os.path.basename(file)) and \
                                       not any(char in '()' for char in os.path.basename(kept_file))
                        
                        reason_newer_str = ""
                        try:
                            is_newer = os.path.getmtime(file) > os.path.getmtime(kept_file)
                            if is_newer and not reason_paren: # Prioritize parenthesis reason if applicable
                                reason_newer_str = f" (newer than kept file: {os.path.basename(kept_file)})"
                        except OSError:
                            is_newer = False # Cannot determine, don't use this reason

                        if reason_paren:
                            reason_str = f" (has parentheses, keeping: {os.path.basename(kept_file)})"
                        elif is_newer: # Redundant due to reason_newer_str but clear
                            reason_str = f" (newer, keeping older: {os.path.basename(kept_file)})"
                        else:
                            # Fallback or if file to delete is older but kept file was better for other reasons (e.g. no parens)
                            # Or if times are identical.
                            reason_str = f" (duplicate of: {os.path.basename(kept_file)})"
                            
                        print(f"{file} (size: {file_size_str}) - will be deleted{reason_str}.")

                    else:
                        # This case should ideally not be reached if prioritize_deletion populates match_info correctly
                        print(f"{file} (size: {file_size_str}) - will be deleted (reason not determined).")

                confirmation = input("Are you sure you want to delete these files? (y/n) ").strip().lower()
                if confirmation == 'y':
                    delete_files(files_to_delete, follow_links)
                else:
                    print("No files were deleted.")
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    try:
        parser = ArgumentParser(
            description="""
Find and delete duplicate files in a directory and its subdirectories.

This script identifies duplicate files by calculating MD5 checksums and offers 
to delete redundant copies, helping you free up disk space while keeping only 
one copy of each unique file.

How It Works:
- Files with identical content (same MD5 checksum) are grouped together
- For each group of duplicate files, the script recommends which copies to delete
- You must confirm before any deletions occur

File Selection Strategy:
When identical files are found, the script uses these rules to suggest which 
copies to keep and which to delete:

1. Files with parentheses in their names (like 'document (1).pdf' or 'image (copy).jpg')
   are suggested for deletion, while files without parentheses are kept. This is because
   files with parentheses are typically auto-generated copies created by browsers or
   file systems.

2. If no files have parentheses (or all files have parentheses), the script suggests
   keeping the oldest file (by modification time) and deleting the newer copies.

Safety:
The script NEVER automatically deletes files without confirmation. You will 
always be prompted before any deletion occurs.
            """,
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  ./script.py                   # Check current directory
  ./script.py ~/Downloads       # Check Downloads folder
  ./script.py -i                # Interactive mode with file-by-file decisions
  ./script.py -v                # Verbose mode showing all processed files
  ./script.py -L                # Follow symbolic links (default: don't follow)
  ./script.py -s1M              # Only check files 1MB or larger
  ./script.py -s 500K           # Only check files 500KB or larger
  ./script.py -s "1.5G"         # Only check files 1.5GB or larger
            """
        )
        parser.add_argument('directory', nargs='?', default='.', 
                            help="Directory to scan for duplicate files (defaults to current directory)")
        parser.add_argument('-i', '--interactive', action='store_true', 
                            help="Enable interactive mode to select which duplicates to delete")
        parser.add_argument('--debug', action='store_true', 
                            help="Show debug information (for script development)")
        parser.add_argument('-v', '--verbose', action='store_true', 
                        help="Show detailed progress including all files checked and MD5 sums")
        parser.add_argument('-L', '--follow-links', action='store_true',
                        help="Follow symbolic links when searching for files (default: don't follow)")
        parser.add_argument('-s', '--min-size', type=parse_size, default=0,
                        help="Minimum file size to consider (e.g. '500K', '10M', '1.5G')")

        # Pre-process sys.argv to handle joined short options like -s1M
        # This must be done before parser.parse_args() or parser.parse_known_args()
        _original_argv = sys.argv.copy() 
        processed_argv = [_original_argv[0]] # Start with the script name
        i = 1
        while i < len(_original_argv):
            arg = _original_argv[i]
            # Check for -s<val> (e.g. -s1M, -s500K). Must be -s, then a digit.
            if arg.startswith('-s') and len(arg) > 2 and not arg.startswith('--') and arg[2].isdigit():
                processed_argv.append('-s')
                processed_argv.append(arg[2:])
            else:
                processed_argv.append(arg)
            i += 1
        sys.argv = processed_argv
        
        try:
            # Parse all arguments once. 
            # The pre-processing of sys.argv handles the -s<val> case.
            # parse_size will be automatically called by argparse for the --min-size argument.
            args = parser.parse_args()
            # The value from args.min_size is already an integer (bytes) due to type=parse_size
            min_size_bytes = args.min_size 
            
        except argparse.ArgumentError as e:
            # This will catch errors from argparse, including those raised by parse_size
            # if they are wrapped as ArgumentError. Typically, argparse will print
            # its own error message and exit for type errors.
            # Let's rely on argparse's default error handling.
            # If parse_size raises ValueError, argparse formats it as:
            # "usage: rmdup.py [-h] ... error: argument -s/--min-size: invalid parse_size value: 'XYZ'"
            # and then exits. So, we might not even need a specific try-except here if
            # the default behavior is acceptable.
            # For now, let's keep a generic error exit.
            # The parser itself will print the error.
            sys.exit(1) 
        except SystemExit as e:
            # This catches --help or --version, or errors that cause argparse to exit.
            sys.exit(e.code)
            
        main(args.directory, interactive=args.interactive, debug=args.debug, 
             verbose=args.verbose, follow_links=args.follow_links, min_size=min_size_bytes)

    # Catch SystemExit separately to allow argparse's --help/error exits to function as expected.
    except SystemExit as e:
        sys.exit(e.code)
    except Exception as e: # General catch-all for other unexpected errors
        print(f"An unexpected error occurred: {str(e)}", file=sys.stderr)
        print("\nRun with -h for help information.")
        sys.exit(1)
