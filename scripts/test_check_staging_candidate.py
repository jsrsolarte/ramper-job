import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).with_name('check_staging_candidate.py')
spec = importlib.util.spec_from_file_location('check_staging_candidate', SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class StagingCandidateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name)
        self.run_git('init', '-q')
        self.run_git('config', 'user.name', 'tester')
        self.run_git('config', 'user.email', 'tester@example.test')
        self.pin = self.path / module.PIN_PATH
        self.pin.parent.mkdir(parents=True)
        self.pin.write_text('original')
        (self.path / 'app.py').write_text('original')
        self.commit('base')
        self.base = self.run_git('rev-parse', 'HEAD')

    def run_git(self, *args):
        return subprocess.check_output(['git', *args], cwd=self.path, text=True).strip()

    def commit(self, message):
        self.run_git('add', '.')
        self.run_git('commit', '-qm', message)

    def check(self, candidate, head):
        return subprocess.run(['python3', str(SCRIPT), candidate, head], cwd=self.path,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0

    def test_current_candidate_and_verified_pin_only_commit_are_accepted(self):
        self.assertTrue(self.check(self.base, self.base))
        self.assertTrue(self.check(self.base, "HEAD"))
        self.run_git('config', 'user.email', module.BOT_EMAIL)
        self.pin.write_text('updated')
        self.commit('deploy(staging): candidate')
        self.assertTrue(self.check(self.base, self.run_git('rev-parse', 'HEAD')))

    def test_later_code_change_is_rejected_even_if_authored_by_bot(self):
        self.run_git('config', 'user.email', module.BOT_EMAIL)
        (self.path / 'app.py').write_text('new code')
        self.commit('deploy(staging): candidate')
        self.assertFalse(self.check(self.base, self.run_git('rev-parse', 'HEAD')))

    def test_pin_and_code_change_cannot_be_disguised_as_bot_pin(self):
        self.run_git('config', 'user.email', module.BOT_EMAIL)
        self.pin.write_text('updated')
        (self.path / 'app.py').write_text('new code')
        self.commit('deploy(staging): candidate')
        self.assertFalse(self.check(self.base, self.run_git('rev-parse', 'HEAD')))

    def test_old_writer_cannot_push_after_remote_branch_advances(self):
        remote = self.path.parent / (self.path.name + '-remote.git')
        self.addCleanup(lambda: __import__('shutil').rmtree(remote, ignore_errors=True))
        subprocess.check_call(['git', 'init', '--bare', '-q', str(remote)])
        self.run_git('remote', 'add', 'origin', str(remote))
        branch = self.run_git('branch', '--show-current')
        self.run_git('push', '-q', 'origin', 'HEAD:' + branch)
        self.run_git('checkout', '-qb', 'old-writer')
        self.pin.write_text('old candidate')
        self.commit('deploy(staging): old')
        self.run_git('checkout', '-q', branch)
        (self.path / 'app.py').write_text('new candidate')
        self.commit('new candidate')
        self.run_git('push', '-q', 'origin', 'HEAD:' + branch)
        rejected = subprocess.run(['git', 'push', 'origin', 'old-writer:' + branch], cwd=self.path,
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.assertNotEqual(rejected.returncode, 0)

    def test_untrusted_pin_update_and_unrelated_history_are_rejected(self):
        self.pin.write_text('manual change')
        self.commit('deploy(staging): candidate')
        self.assertFalse(self.check(self.base, self.run_git('rev-parse', 'HEAD')))
        self.assertFalse(self.check('0' * 40, self.run_git('rev-parse', 'HEAD')))


if __name__ == '__main__':
    unittest.main()

class ReleaseCandidateTests(StagingCandidateTests):
    def release_check(self, candidate, release, staging, main):
        script = SCRIPT.with_name('check_release_candidate.py')
        return subprocess.run(['python3', str(script), candidate, release, staging, main], cwd=self.path,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0

    def test_release_merge_commit_accepts_identical_application(self):
        self.run_git('checkout', '-qb', 'candidate')
        (self.path / 'app.py').write_text('tested application')
        self.commit('candidate')
        candidate = self.run_git('rev-parse', 'HEAD')
        self.run_git('checkout', '-qb', 'release', self.base)
        (self.path / 'deploy' / 'release-note').write_text('metadata only')
        self.commit('release metadata')
        self.run_git('merge', '--no-ff', '-qm', 'integrate tested candidate', 'candidate')
        release = self.run_git('rev-parse', 'HEAD')
        self.assertNotEqual(candidate, release)
        self.assertTrue(self.release_check(candidate, release, candidate, release))

    def test_release_rejects_code_changes_or_missing_ancestry(self):
        (self.path / 'app.py').write_text('different application')
        self.commit('change code')
        release = self.run_git('rev-parse', 'HEAD')
        self.assertFalse(self.release_check(self.base, release, release, release))
        self.assertFalse(self.release_check(release, self.base, release, self.base))
