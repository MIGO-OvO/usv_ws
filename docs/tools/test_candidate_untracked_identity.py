"""Candidate identity uses real Git discovery, not just a dirty boolean."""
import subprocess
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from check_workspace_compatibility import compare_snapshot, snapshot


class UntrackedCandidateTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.repo = self.root / 'repo'
        self.repo.mkdir()
        self.git('init', '-q')
        self.git('-c', 'user.name=Test', '-c', 'user.email=test@example.invalid',
                 'commit', '--allow-empty', '-qm', 'baseline')
        self.patch = patch('check_workspace_compatibility.REPOS', {'test': ('repo', [])})
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.repo), *args])

    def test_untracked_content_changes_candidate_even_while_both_are_dirty(self):
        source = self.repo / 'new worker.py'
        source.write_bytes(b'output = 1\n')
        before = snapshot(self.root)
        source.write_bytes(b'output = 2\n')
        after = snapshot(self.root)
        self.assertTrue(before['repositories']['test']['dirty'])
        self.assertTrue(after['repositories']['test']['dirty'])
        self.assertTrue(compare_snapshot(after, before))

    def test_untracked_rename_changes_candidate(self):
        source = self.repo / 'old.py'
        source.write_bytes(b'same bytes\n')
        before = snapshot(self.root)
        source.rename(self.repo / 'new.py')
        self.assertTrue(compare_snapshot(snapshot(self.root), before))

    def test_paths_types_hashes_and_ignored_exclusion(self):
        self.git('config', 'core.quotePath', 'true')
        (self.repo / '.gitignore').write_text('cache/\n', encoding='utf-8')
        (self.repo / 'cache').mkdir()
        (self.repo / 'cache' / 'ignored.bin').write_bytes(b'ignored')
        directory = self.repo / '目录 with space'
        directory.mkdir()
        (directory / 'worker.py').write_bytes(b'payload\r\n')
        files = snapshot(self.root)['repositories']['test']['untracked_files']
        self.assertEqual(set(files), {'.gitignore', '目录 with space/worker.py'})
        self.assertEqual(files['目录 with space/worker.py']['type'], 'file')
        self.assertEqual(files['目录 with space/worker.py']['sha256'],
                         hashlib.sha256(b'payload\r\n').hexdigest())

    def test_symlink_identity_does_not_follow_outside_target(self):
        link = self.repo / 'link'
        try:
            link.symlink_to('../not-in-candidate')
        except OSError as error:
            self.skipTest('symlink creation unavailable: %s' % error)
        before = snapshot(self.root)
        entry = before['repositories']['test']['untracked_files']['link']
        self.assertEqual(entry, {'type': 'symlink', 'sha256':
                                hashlib.sha256(b'../not-in-candidate').hexdigest()})
        link.unlink()
        link.write_bytes(b'../not-in-candidate')
        self.assertTrue(compare_snapshot(snapshot(self.root), before))

    def test_release_gate_still_rejects_dirty_candidate(self):
        (self.repo / 'new.py').write_bytes(b'new')
        current = snapshot(self.root)
        current.update(field_verified=True, evidence_ref='test')
        self.assertIn('release requires clean, committed child repositories',
                      compare_snapshot(current, current, require_release=True))


if __name__ == '__main__':
    unittest.main()
