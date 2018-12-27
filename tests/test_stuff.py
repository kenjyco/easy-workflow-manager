import pytest
import bg_helper as bh
import easy_workflow_manager as ewm
from . import *


class TestNewRepo(object):
    def test_remote_branches(self):
        assert ewm.get_remote_branches(all_branches=True) == ['master']
        ewm.new_branch('otherbranch')
        ewm.new_branch('mybranch')
        ewm.new_branch('mybranch2')
        assert ewm.get_remote_branches() == ['mybranch', 'mybranch2', 'otherbranch']
        assert ewm.get_remote_branches(all_branches=True) == ['master', 'mybranch', 'mybranch2', 'otherbranch']
        assert ewm.get_merged_remote_branches() == ['mybranch', 'mybranch2', 'otherbranch']
        assert ewm.get_branch_name() == 'mybranch2'

    def test_local_branches(self):
        assert ewm.get_local_branches() == ['master', 'mybranch', 'mybranch2', 'otherbranch']
        assert ewm.get_local_branches(grep='other') == ['otherbranch']
        assert ewm.get_local_branches(grep='branch') == ['mybranch', 'mybranch2', 'otherbranch']
        assert ewm.get_local_branches(grep='my') == ['mybranch', 'mybranch2']
        assert ewm.get_merged_local_branches() == ['mybranch', 'mybranch2', 'otherbranch']

    def test_qa(self):
        assert ewm.get_qa_env_branches() == []
        assert ewm.get_non_empty_qa() == set()
        assert ewm.get_empty_qa() == set(ewm._get_repo_settings('QA_BRANCHES'))

    def test_change_commit_push(self):
        print()
        change_file_line()
        ewm.show_repo_info()
        bh.run('git add .; git commit -m "Changed file"; git push', show=True)
        assert ewm.get_merged_remote_branches() == ['mybranch', 'otherbranch']


class TestMoreStuff(object):
    def test_remote_branches(self):
        assert ewm.get_remote_branches(all_branches=True) == ['master']
