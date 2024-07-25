#!/usr/bin/python3

# Remove duplicate files 

# Version 1.0
# By Alan Rockefeller - July 25, 2024

# This script recursively looks for duplicate files in the current directory and offers to delete them.   
# If you give it the -i option it asks about each file - if you don't it lists all the files it plans to delete and lets you decide if you want to go ahead.

# It prioritizes deleting files with parenthesis, as these are often extra files that were downloaded or saved, and it's usually best to keep the original filename rather than the one with (1) or (2), etc.


import os
import hashlib
from collections import defaultdict
from argparse import ArgumentParser

def get_md5(file_path):
    """Calculate the MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def get_file_size(file_path):
    """Get the size of a file in a human-readable format."""
    size = os.path.getsize(file_path)
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} TB"

def find_duplicates(directory):
    """Find duplicate files in the specified directory."""
    checksums = defaultdict(list)
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            file_checksum = get_md5(file_path)
            checksums[file_checksum].append(file_path)
    
    return {k: v for k, v in checksums.items() if len(v) > 1}

def delete_files(files):
    """Delete files from the filesystem."""
    for file in files:
        try:
            os.remove(file)
            print(f"Deleted: {file}")
        except FileNotFoundError:
            print(f"File not found: {file}")
        except Exception as e:
            print(f"Error deleting file {file}: {e}")

def prioritize_deletion(duplicates, debug=False):
    """Prioritize files with parentheses for deletion."""
    files_to_delete = []
    for paths in duplicates.values():
        if debug:
            print("Paths in current group:", paths)
        
        with_parentheses = [p for p in paths if any(char in '()' for char in os.path.basename(p))]
        
        if debug:
            print("Files with parentheses:", with_parentheses)
        
        if with_parentheses:
            files_to_delete.extend(with_parentheses)
        else:
            # If no file with parentheses is found, delete all but the first file
            files_to_delete.extend(paths[1:])  # Keep the first file, delete the rest
    
    if debug:
        print("Files to delete after prioritization:", files_to_delete)
    
    return files_to_delete

def interactive_delete(files):
    """Interactively ask the user for confirmation to delete each file."""
    for file in files:
        size = get_file_size(file)
        print(f"File: {file} ({size})")
        confirmation = input("Do you want to delete this file? (y/n) ").strip().lower()
        if confirmation == 'y':
            try:
                os.remove(file)
                print(f"Deleted: {file}")
            except FileNotFoundError:
                print(f"File not found: {file}")
            except Exception as e:
                print(f"Error deleting file {file}: {e}")
        else:
            print(f"Skipped: {file}")

def main(directory, interactive=False, debug=False):
    duplicates = find_duplicates(directory)
    if not duplicates:
        print("No duplicate files found.")
        return
    
    files_to_delete = prioritize_deletion(duplicates, debug)
    
    if files_to_delete:
        if interactive:
            print("Interactive mode enabled. Files proposed for deletion:")
            interactive_delete(files_to_delete)
        else:
            print("Files proposed for deletion:")
            for file in files_to_delete:
                print(file)
            
            confirmation = input("Are you sure you want to delete these files? (y/n) ").strip().lower()
            if confirmation == 'y':
                delete_files(files_to_delete)
            else:
                print("No files were deleted.")

if __name__ == "__main__":
    parser = ArgumentParser(description="Find and delete duplicate files.")
    parser.add_argument('directory', nargs='?', default='.', help="Directory to scan for duplicate files.")
    parser.add_argument('-i', '--interactive', action='store_true', help="Enable interactive mode to confirm deletions.")
    parser.add_argument('--debug', action='store_true', help="Enable debugging output.")

    args = parser.parse_args()
    main(args.directory, interactive=args.interactive, debug=args.debug)
