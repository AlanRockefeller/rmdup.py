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
            print(f"Processing: {os.path.basename(self.current_file)}", end='')
            sys.stdout.flush()
    
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
                print(f"Skipping symlink: {file_path}")
            return None
            
        with open(file_path, 'rb') as f:
            file_size = os.path.getsize(file_path)
            chunk_size = 4096
            
            if pbar:
                # Update the progress bar description to show current file
                pbar.set_description(file_path)
            
            for chunk in iter(lambda: f.read(chunk_size), b""):
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


def get_file_size(file_path):
    """Get the size of a file in a human-readable format."""
    try:
        size = os.path.getsize(file_path)
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} TB"
    except (PermissionError, OSError):
        return "Unknown size"


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
                        print(f"Skipping symlink: {file_path}")
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
    
    # Show progress if total file size is larger than 250 MB OR if there are more than 250 files
    use_progress = (total_size > 250 * 1024 * 1024) or (len(all_files) > 250)
    
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
                print(f"Skipping symlink: {file}")
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
    """Prioritize files with parentheses for deletion and prefer keeping older files."""
    files_to_delete = []
    # Keep track of which files match with which
    match_info = {}
    
    for checksum, paths in duplicates.items():
        if debug:
            print("Paths in current group:", paths)

        # First check for files with parentheses
        with_parentheses = [p for p in paths if any(char in '()' for char in os.path.basename(p))]
        
        if with_parentheses:
            # If we have files with parentheses, prefer to delete those
            for p in with_parentheses:
                # Find a matching file without parentheses if possible
                non_paren_files = [f for f in paths if f != p and not any(char in '()' for char in os.path.basename(f))]
                if non_paren_files:
                    match_info[p] = non_paren_files[0]  # Match with first non-parenthesis file
                else:
                    # If all are parentheses, match with another parenthesis file
                    other_files = [f for f in paths if f != p]
                    if other_files:
                        match_info[p] = other_files[0]
            
            files_to_delete.extend(with_parentheses)
            if debug:
                print("Files with parentheses to delete:", with_parentheses)
        else:
            # Sort files by modification time, oldest first
            sorted_by_time = sorted(paths, key=lambda p: os.path.getmtime(p))
            
            if debug:
                print("Files sorted by time (oldest first):", sorted_by_time)
                
            # Keep the oldest file, suggest deleting the newer ones
            for p in sorted_by_time[1:]:
                match_info[p] = sorted_by_time[0]  # Match with the oldest file
            
            files_to_delete.extend(sorted_by_time[1:])

    if debug:
        print("Files to delete after prioritization:", files_to_delete)

    return files_to_delete, match_info


def get_file_info(file_path):
    """Get detailed file information including size and modification time."""
    try:
        size = get_file_size(file_path)
        mtime = os.path.getmtime(file_path)
        mtime_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(mtime))
        return f"{size}, modified: {mtime_str}"
    except (PermissionError, OSError):
        return "Unknown info"


def get_user_choice(files):
    """Show files to user and ask them what to delete."""
    # Sort files by modification time, oldest first
    sorted_files = sorted(files, key=lambda p: os.path.getmtime(p))
    
    print("\nFiles in this group:")
    
    for i, file in enumerate(sorted_files, 1):
        file_info = get_file_info(file)
        # Mark the oldest file
        if i == 1:
            print(f"{i}: {file} ({file_info}) [oldest]")
        else:
            print(f"{i}: {file} ({file_info})")

    while True:
        try:
            options = "/".join([str(i) for i in range(1, len(sorted_files)+1)])
            choice = input(f"\nWhich file(s) would you like to DELETE? (Enter numbers, 'all' except oldest, 'none' to keep all): ").strip().lower()
            
            if choice == 'all':
                # Delete all except the oldest
                return sorted_files[1:]
                
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
                # Read up to 100 bytes
                sample = f.read(min(100, file_size))
                if all(32 <= byte <= 126 for byte in sample):  # Check if ASCII printable
                    print(f"Content sample: {sample.decode('utf-8', errors='replace')[:60]}...")
        except Exception:
            pass  # Skip showing sample on error
        
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
                                print(f"Skipping symlink: {file}")
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
                    file_size = get_file_size(file)
                    if file in match_info:
                        matching_file = match_info[file]
                        print(f"{file} (duplicate of: {matching_file} ({file_size}))")
                    else:
                        print(f"{file}")  # Fallback if no match info

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
        parser.add_argument('-s', '--min-size', type=str, default='0',
                        help="Minimum file size to consider (e.g. '500K', '10M', '1.5G')")

        # Parse known args first
        args, remaining = parser.parse_known_args()
        
        # Check if we have arguments that might be joined like -s1M
        processed_args = []
        for arg in remaining:
            if arg.startswith('-s') and len(arg) > 2 and not arg.startswith('--'):
                # Split into -s and the value
                processed_args.extend(['-s', arg[2:]])
            else:
                processed_args.append(arg)
        
        # Re-parse with processed arguments
        if processed_args:
            # Combine original known args with processed remaining args
            import sys
            sys.argv = [sys.argv[0]] + [f"--{k.replace('_', '-')}={v}" if not isinstance(v, bool) else f"--{k.replace('_', '-')}" if v else "" 
                        for k, v in vars(args).items() if v and k != 'directory'] + processed_args
            if args.directory != '.':
                sys.argv.append(args.directory)
            
            # Re-parse all arguments
            args = parser.parse_args()
        
        try:
            min_size_bytes = parse_size(args.min_size)
        except ValueError as e:
            print(f"Error with --min-size: {str(e)}")
            print("Valid formats: '10B', '500K', '10M', '1.5G', etc.")
            sys.exit(1)
            
        main(args.directory, interactive=args.interactive, debug=args.debug, 
             verbose=args.verbose, follow_links=args.follow_links, min_size=min_size_bytes)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        print("\nRun with -h for help information.")
        sys.exit(1)
