# Duplicate File Remover

A simple Python script to find and delete duplicate files in your directories.

**Author:** Alan Rockefeller  
**Version:** 1.1 (Note: Script version is 1.1, documentation reflects ongoing changes towards 1.2)
**Date:** March 30, 2025  
**GitHub:** https://github.com/AlanRockefeller/rmdup.py

## What does it do?

This script scans through a directory (and all subdirectories) looking for files that are *exactly* the same, then offers to delete the extras for you. It's pretty handy for cleaning up your Downloads folder, photos, or anywhere you might have accumulated multiple copies of the same files.

## How does it work?

The script:
1. Scans through all the files in a directory
2. Calculates an MD5 checksum for each file (a unique fingerprint based on the file's contents)
3. Groups files that have the same checksum (meaning they're 100% identical)
4. Uses some smart rules to suggest which copy to keep and which to delete
5. Asks for your confirmation before deleting anything

## What's special about it?

- **Smart File Prioritization:** When deciding which duplicate file to keep, the script is designed to make the most common-sense choice:
    - It prioritizes keeping files *without* parentheses (e.g., `(1)`, `(copy)`) in their names.
    - Among those, or if all files are similar in naming, it prioritizes keeping the *oldest* version of the file.
    - This means if a choice exists between an older file with a clean name and a newer file (or one with parentheses), it will recommend keeping the older, cleaner-named one.
- **Clear Interactive Choices:** In interactive mode (`-i`), the script highlights a "[recommended to keep]" file in each duplicate group based on these prioritization rules, making decisions easier.
- **Progress Bar:** Shows progress when working on big directories.
- **Space Saved:** Tells you how much disk space you freed up.
- **Confirmation:** You ALWAYS get to confirm before anything is deleted.

## How to use it

Basic usage:
```
./rmdup.py
```

This will check the current directory for duplicate files.

### Options

```
./rmdup.py [directory]   # Check a specific directory
./rmdup.py -i            # Interactive mode - decide file by file
./rmdup.py -v            # Verbose mode - see all the details
./rmdup.py -L            # Follow symbolic links (default: don't follow them)
./rmdup.py -s1M          # Only look at files larger than 1MB
./rmdup.py -s "500 KB"   # Only look at files larger than 500KB
# Note: The -s option also supports formats like -s10M, -s2.5G etc.
```

## Interactive mode

In interactive mode (`-i`), you'll see each group of identical files one at a time. The script will also highlight a "[recommended to keep]" file in each duplicate group based on its prioritization rules (favoring older files, especially those without parentheses in their names). You can then choose which specific files to delete. This is useful when you want more granular control.

## Examples

Find duplicates in your Downloads folder:
```
./rmdup.py ~/Downloads
```

Find duplicates larger than 10MB (to focus on the big files first):
```
./rmdup.py -s 10MB ~/Pictures
```

Interactively clean up your Documents folder:
```
./rmdup.py -i ~/Documents
```

## Installation

No installation needed! Just:

1. Download the script
2. Run it

I suggest putting it in your path.

## Warning

While I've tried to make this script safe, you're still deleting files. Try it on non-critical stuff first, and always keep backups.   I use Backblaze to back up all my data, so if something gets hosed I can always log in and download it again.

## Requirements

- Python 3

## Known limitations

- Very large files might take a while to checksum - 30 gigs takes 27 minutes on my SSD
- Symbolic links are skipped by default (use `-L` to follow them)

## Contributing

Got ideas to make this better? Great! Feel free to:

- Submit a pull request on GitHub: https://github.com/AlanRockefeller/rmdup.py
- Contact me via Instagram, Facebook, LinkedIn or email

I'm always open to suggestions and improvements!
