import unittest
import os
import hashlib
from unittest.mock import patch, mock_open, MagicMock

# Assuming rmdup.py is in the same directory or accessible via PYTHONPATH
from rmdup import (
    parse_size,
    get_human_size,
    prioritize_deletion,
    get_md5,
    # If ProgressBar is needed for get_md5 testing:
    # ProgressBar 
)

# --- Constants from rmdup.py (if needed for test setup directly) ---
DEFAULT_CHUNK_SIZE = 4096


class TestParseSize(unittest.TestCase):
    def test_valid_sizes(self):
        self.assertEqual(parse_size('10B'), 10)
        self.assertEqual(parse_size('500K'), 500 * 1024)
        self.assertEqual(parse_size('10M'), 10 * 1024**2)
        self.assertEqual(parse_size('2G'), 2 * 1024**3)
        self.assertEqual(parse_size('1T'), 1 * 1024**4)
        self.assertEqual(parse_size('1.5GB'), int(1.5 * 1024**3))
        self.assertEqual(parse_size('1.5mb'), int(1.5 * 1024**2))
        self.assertEqual(parse_size('0'), 0)
        self.assertEqual(parse_size('1024'), 1024) # Assumes bytes if no unit

    def test_sizes_with_spaces(self):
        self.assertEqual(parse_size('5 MB'), 5 * 1024**2)
        self.assertEqual(parse_size('2.5 GB'), int(2.5 * 1024**3))

    def test_case_insensitivity(self):
        self.assertEqual(parse_size('1g'), 1 * 1024**3)
        self.assertEqual(parse_size('1gb'), 1 * 1024**3)
        self.assertEqual(parse_size('1Mb'), 1 * 1024**2)

    def test_invalid_sizes(self):
        with self.assertRaises(ValueError):
            parse_size('1X')
        with self.assertRaises(ValueError):
            parse_size('abc')
        with self.assertRaises(ValueError):
            parse_size('1.5XG')
        with self.assertRaises(ValueError):
            parse_size('1MK') # Invalid unit combination
        with self.assertRaises(ValueError): # no number
            parse_size('MB')

    def test_empty_input(self):
        self.assertEqual(parse_size(''), 0)
        self.assertEqual(parse_size(None), 0)


class TestGetHumanSize(unittest.TestCase):
    def test_various_sizes(self):
        self.assertEqual(get_human_size(0), "0 B")
        self.assertEqual(get_human_size(500), "500.0 B")
        self.assertEqual(get_human_size(1023), "1023.0 B")
        self.assertEqual(get_human_size(1024), "1.0 KB")
        self.assertEqual(get_human_size(1536), "1.5 KB") # 1.5 * 1024
        self.assertEqual(get_human_size(1024**2), "1.0 MB")
        self.assertEqual(get_human_size(int(1.5 * 1024**2)), "1.5 MB")
        self.assertEqual(get_human_size(1024**3), "1.0 GB")
        self.assertEqual(get_human_size(int(2.75 * 1024**3)), "2.75 GB")
        self.assertEqual(get_human_size(1024**4), "1.0 TB")
        self.assertEqual(get_human_size(1024**5), "1.0 PB")


class TestPrioritizeDeletion(unittest.TestCase):
    def _run_prio_test(self, paths_with_mtimes, expected_to_delete_basenames, expected_kept_basename):
        """
        Helper to run prioritize_deletion tests.
        paths_with_mtimes: list of (basename_str, mtime_float)
        expected_to_delete_basenames: list of basenames expected to be deleted.
        expected_kept_basename: basename of the file expected to be kept.
        """
        # Create full paths for testing, as basename is used internally
        # The actual paths don't matter beyond their basenames and mtimes for these tests
        base_dir = "/tmp/testdir" 
        full_paths_with_mtimes = [(os.path.join(base_dir, bn), mt) for bn, mt in paths_with_mtimes]
        
        # Input to prioritize_deletion is {checksum: [paths]}
        # We use a single dummy checksum.
        duplicate_paths = [fp for fp, mt in full_paths_with_mtimes]
        duplicates_dict = {"dummy_checksum": duplicate_paths}

        # Mock os.path.getmtime and os.path.basename
        # getmtime: return mtime based on path
        # basename: return basename part of path
        def mock_getmtime(path):
            for p, mt in full_paths_with_mtimes:
                if p == path:
                    return mt
            raise FileNotFoundError(f"Test setup error: mtime not found for {path}")

        # We don't need to mock os.path.basename if we structure inputs correctly,
        # but for robustness or more complex path structures, it could be.
        # The function under test `prioritize_deletion` uses os.path.basename(p)
        # So, the paths in `duplicate_paths` must be structured such that os.path.basename works as expected.

        with patch('rmdup.os.path.getmtime', side_effect=mock_getmtime):
            # If rmdup.py uses `from os.path import basename, getmtime` then patching `rmdup.basename` etc. is needed.
            # If it uses `os.path.basename` then `rmdup.os.path.basename` is needed.
            # Let's assume it uses os.path.basename directly as is common.
            files_to_delete, match_info = prioritize_deletion(duplicates_dict, debug=False)

        # Assertions
        # Check files_to_delete (compare basenames for simplicity)
        deleted_basenames = sorted([os.path.basename(f) for f in files_to_delete])
        self.assertListEqual(deleted_basenames, sorted(expected_to_delete_basenames))

        # Check match_info
        expected_kept_full_path = os.path.join(base_dir, expected_kept_basename)
        for deleted_file_path in files_to_delete:
            self.assertEqual(match_info[deleted_file_path], expected_kept_full_path)
        
        # Check that the kept file is not in files_to_delete
        self.assertNotIn(expected_kept_full_path, files_to_delete)


    def test_scenario1_clear_original(self):
        # Oldest, no parens = keep. Newer with parens = delete. Newer without parens = delete.
        paths = [
            ("file_original.txt", 100.0),  # Keep: oldest, no parens
            ("file_copy (1).txt", 110.0),  # Delete: has parens
            ("file_copy (2).txt", 120.0),  # Delete: has parens, newer
            ("file_newer_no_paren.txt", 130.0) # Delete: newer than original, no parens
        ]
        self._run_prio_test(paths, 
                            ["file_copy (1).txt", "file_copy (2).txt", "file_newer_no_paren.txt"],
                            "file_original.txt")

    def test_scenario2_all_no_parentheses(self):
        # All no parens, keep oldest
        paths = [
            ("archive.zip", 200.0),      # Delete: newer
            ("document.pdf", 100.0),     # Keep: oldest
            ("image.jpg", 150.0)         # Delete: newer
        ]
        self._run_prio_test(paths, 
                            ["archive.zip", "image.jpg"],
                            "document.pdf")

    def test_scenario3_all_with_parentheses(self):
        # All with parens, keep oldest
        paths = [
            ("report (1).doc", 150.0),   # Delete: newer
            ("report (final).doc", 100.0), # Keep: oldest
            ("report (backup).doc", 200.0) # Delete: newer
        ]
        self._run_prio_test(paths,
                            ["report (1).doc", "report (backup).doc"],
                            "report (final).doc")

    def test_scenario4_mixed_complex(self):
        # file_alpha.txt (no parens, oldest overall) -> should be kept
        # file_beta (1).txt (parens, newer than alpha) -> delete
        # file_gamma.txt (no parens, but newer than alpha) -> delete
        # file_delta (2).txt (parens, newest) -> delete
        paths = [
            ("file_alpha.txt", 10.0),      # Keep
            ("file_beta (1).txt", 20.0), # Delete
            ("file_gamma.txt", 30.0),    # Delete
            ("file_delta (2).txt", 40.0) # Delete
        ]
        self._run_prio_test(paths,
                            ["file_beta (1).txt", "file_gamma.txt", "file_delta (2).txt"],
                            "file_alpha.txt")

    def test_scenario5_two_files_no_paren(self):
        paths = [
            ("latest.txt", 20.0),  # Delete
            ("oldest.txt", 10.0)   # Keep
        ]
        self._run_prio_test(paths, ["latest.txt"], "oldest.txt")

    def test_scenario6_two_files_one_paren(self):
        # No paren should be preferred even if newer, if the other has parens and is older
        # Current logic: if without_paren list is not empty, oldest of *those* is kept.
        paths = [
            ("data (old_copy).dat", 10.0), # Delete (has parens)
            ("data_new.dat", 20.0)      # Keep (no parens, even if newer)
        ]
        self._run_prio_test(paths, ["data (old_copy).dat"], "data_new.dat")
        
    def test_scenario7_identical_mtimes_no_paren(self):
        # If mtimes are identical, tie-breaking is implicit (Python's sort stability or path string sort)
        # The test should reflect this by ensuring one is kept and others deleted.
        # For this test, we assume the first one in the input list if times are identical and it's string-wise smallest.
        # Let's make paths pre-sorted to make expectation clear.
        paths = [
            ("a_file.txt", 100.0), # Keep (due to name if times are same and it's sorted first)
            ("b_file.txt", 100.0), # Delete
            ("c_file.txt", 100.0)  # Delete
        ]
        # To make this deterministic for the test, mock getmtime to return distinct values for sort
        # or rely on path name sorting by providing them sorted.
        # The current _run_prio_test helper will use the given mtimes.
        # If paths are ('a', 100), ('b', 100), sort by mtime is stable.
        # If without_paren.sort(key=...) is stable, 'a_file.txt' will be first.
        self._run_prio_test(paths, ["b_file.txt", "c_file.txt"], "a_file.txt")

    def test_scenario8_one_file_no_action(self):
        # If a group has only one file, it shouldn't be deleted.
        paths = [("single_file.txt", 100.0)]
        # prioritize_deletion internally filters for groups with len(v) > 1
        # but if called directly with such a group:
        duplicate_paths = [os.path.join("/tmp/testdir", "single_file.txt")]
        duplicates_dict = {"dummy_checksum": duplicate_paths}
        
        def mock_getmtime(path): return 100.0

        with patch('rmdup.os.path.getmtime', side_effect=mock_getmtime):
            files_to_delete, match_info = prioritize_deletion(duplicates_dict, debug=False)
        
        self.assertEqual(len(files_to_delete), 0)
        self.assertEqual(len(match_info), 0)


class TestGetMD5(unittest.TestCase):
    @patch('rmdup.os.path.getsize', return_value=DEFAULT_CHUNK_SIZE * 2.5) # Mock file size
    @patch('rmdup.os.path.islink', return_value=False) # Mock not a symlink
    @patch('builtins.open', new_callable=mock_open, read_data=b"chunk1_data" + b"chunk2_data" + b"chunk3_data")
    def test_get_md5_reads_chunks(self, mock_file_open, mock_islink, mock_getsize):
        
        mock_hash_obj = MagicMock()
        mock_md5_constructor = MagicMock(return_value=mock_hash_obj)
        
        with patch('rmdup.hashlib.md5', mock_md5_constructor):
            checksum = get_md5("dummy_path.txt")

        # Check open was called
        mock_file_open.assert_called_once_with("dummy_path.txt", 'rb')
        
        # Check hashlib.md5 was called
        mock_md5_constructor.assert_called_once_with()
        
        # Check that update was called multiple times (for chunks)
        self.assertTrue(mock_hash_obj.update.call_count > 0)
        # Example: For DEFAULT_CHUNK_SIZE = 4096, and read_data supplied to mock_open
        # it will read in one go if not chunked by iter(lambda: f.read(), b"")
        # Let's refine read_data to simulate chunking
        
        # To test chunking properly, mock f.read behavior
        mock_file_obj = mock_file_open.return_value
        # Configure read to return data in chunks then empty byte string
        chunks = [b"A"*DEFAULT_CHUNK_SIZE, b"B"*DEFAULT_CHUNK_SIZE, b"C"*int(DEFAULT_CHUNK_SIZE*0.5)]
        mock_file_obj.read.side_effect = chunks + [b'']

        # Re-run with refined mock_file_obj for chunking test
        mock_hash_obj.reset_mock()
        mock_md5_constructor.reset_mock()
        mock_file_open.reset_mock()

        with patch('rmdup.hashlib.md5', mock_md5_constructor):
             checksum = get_md5("dummy_path.txt")
        
        mock_file_open.assert_called_once_with("dummy_path.txt", 'rb')
        self.assertEqual(mock_hash_obj.update.call_count, len(chunks))
        for i, call_args in enumerate(mock_hash_obj.update.call_args_list):
            args, _ = call_args
            self.assertEqual(args[0], chunks[i])
        
        mock_hash_obj.hexdigest.assert_called_once_with()
        self.assertEqual(checksum, mock_hash_obj.hexdigest.return_value)


    @patch('rmdup.os.path.islink', return_value=True) # Mock IS a symlink
    def test_get_md5_skip_symlink_if_not_following(self, mock_islink):
        checksum = get_md5("symlink.txt", follow_links=False, verbose=False)
        self.assertIsNone(checksum)
        mock_islink.assert_called_once_with("symlink.txt")

    @patch('rmdup.os.path.islink', return_value=True) # Mock IS a symlink
    @patch('builtins.open', new_callable=mock_open, read_data=b"symlink_content")
    @patch('rmdup.os.path.getsize', return_value=len(b"symlink_content"))
    def test_get_md5_follow_symlink(self, mock_getsize, mock_file_open, mock_islink):
        # This test assumes follow_links=True would make it not call os.path.islink check first,
        # or that the check passes. The current get_md5 has `if os.path.islink and not follow_links`.
        # So if follow_links is True, this check is skipped.
        
        mock_hash_obj = MagicMock()
        mock_md5_constructor = MagicMock(return_value=mock_hash_obj)
        
        with patch('rmdup.hashlib.md5', mock_md5_constructor):
            checksum = get_md5("symlink.txt", follow_links=True, verbose=False)

        mock_islink.assert_called_once_with("symlink.txt") # islink is still called
        mock_file_open.assert_called_once_with("symlink.txt", 'rb')
        mock_hash_obj.update.assert_called_once_with(b"symlink_content")
        self.assertIsNotNone(checksum)

    @patch('builtins.open', side_effect=PermissionError("Test permission error"))
    @patch('rmdup.os.path.islink', return_value=False)
    def test_get_md5_permission_error(self, mock_islink, mock_file_open):
        checksum = get_md5("protected_file.txt", verbose=False)
        self.assertIsNone(checksum)
        mock_file_open.assert_called_once_with("protected_file.txt", 'rb')

    @patch('builtins.open', new_callable=mock_open, read_data=b"data")
    @patch('rmdup.os.path.getsize', return_value=4)
    @patch('rmdup.os.path.islink', return_value=False)
    def test_get_md5_with_progress_bar(self, mock_islink, mock_getsize, mock_file_open):
        mock_pbar = MagicMock() # Mock ProgressBar instance
        
        mock_hash_obj = MagicMock()
        mock_md5_constructor = MagicMock(return_value=mock_hash_obj)

        with patch('rmdup.hashlib.md5', mock_md5_constructor):
            get_md5("file.txt", pbar=mock_pbar)

        mock_pbar.set_description.assert_called_once_with("file.txt")
        # update called for each chunk. If read_data is small, it's one chunk.
        mock_pbar.update.assert_called_once_with(len(b"data"))


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)

# Note: To run these tests from command line, you'd typically navigate to the directory
# and run `python -m unittest test_rmdup.py`.
# The `if __name__ == '__main__':` block allows running it as a script,
# but `unittest.main()` can be tricky in some environments if not handled carefully.
# `argv` and `exit` params are for compatibility in some notebook/scripting environments.
# For production test runners, this main block is often not strictly needed.
#
# Regarding patching: if rmdup.py uses "from os.path import basename, getmtime",
# then patching needs to be @patch('rmdup.basename'), @patch('rmdup.getmtime').
# If it uses "import os; os.path.basename", then @patch('rmdup.os.path.basename') is correct.
# The current tests assume the latter or direct `os.path.X` usage within functions.
# The `builtins.open` patch is standard. `hashlib.md5` patch is on `rmdup.hashlib.md5`.
