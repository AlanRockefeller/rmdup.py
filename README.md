# rmdup.py

Remove duplicate files in a directory and its subdirectories.

## Description

`rmdup.py` is a Python script that recursively scans a directory for duplicate files and offers to delete them. It uses MD5 checksums to identify duplicates and prioritizes deleting files with parentheses in their names, as these are often extra files that were downloaded or saved.

This script won't delete any files without asking you first.

## Features

- Recursively scans directories for duplicate files
- Uses MD5 checksums for file comparison
- Prioritizes deleting files with parentheses in their names
- Interactive mode for confirming deletions
- Debug mode for additional output
- Human-readable file size display

## Usage

python3 rmdup.py [directory] [-i] [--debug]

- `[directory]`: Optional. The directory to scan for duplicates. Defaults to the current directory.
- `-i, --interactive`: Enable interactive mode to confirm each deletion.
- `--debug`: Enable debug output for more detailed information.

## Examples

1. Scan the current directory:

python3 rmdup.py

2. Scan a specific directory:

python3 rmdup.py /path/to/directory

3. Use interactive mode:

python3 rmdup.py -i

4. Enable debug output:

python3 rmdup.py --debug

## Warning

This script permanently deletes files. Use with caution and ensure you have backups of important data before running it.

## Requirements

- Python 3.x

## Author

Alan Rockefeller

## Version

1.0 (July 25, 2024)

## License

This project is licensed under the GNU General Public License v3.0 (GPL-3.0).

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.

## Contributing

Contributions, issues, and feature requests are welcome. Feel free to check [issues page](https://github.com/AlanRockefeller/rmdup.py/issues) if you want to contribute.

## Show your support

Give a ⭐️ or send me an email if you found this useful.   Feel free to suggest changes.
