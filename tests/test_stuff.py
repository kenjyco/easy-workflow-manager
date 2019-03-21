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
        assert ewm.get_empty_qa() == {'qa1', 'qa2', 'qa3'}
        qa = 'qa1'
        append_to_file()
        add_commit_push()
        ewm.deploy_to_qa(qa=qa, branches='mybranch2')
        env_branches = ewm.get_qa_env_branches(qa=qa)
        assert len(env_branches) == 1
        assert env_branches[0]['contains'] == ['mybranch2']
        assert sorted(list(ewm.get_empty_qa())) == ['qa2', 'qa3']
        all_branches = ewm.get_remote_branches(all_branches=True)
        assert all_branches == ['master', 'mybranch', 'mybranch2', 'otherbranch', 'qa1', 'qa1--with--mybranch2']
        ewm.clear_qa(qa, force=True)
        assert ewm.get_qa_env_branches(qa=qa) == []

    def test_change_commit_push(self):
        print()
        checkout_branch('mybranch2')
        change_file_line()
        ewm.show_repo_info()
        add_commit_push()
        ewm.show_repo_info()
        merged_remote_branches = ewm.get_merged_remote_branches()
        assert 'mybranch' in merged_remote_branches
        assert 'otherbranch' in merged_remote_branches
        assert 'mybranch2' not in merged_remote_branches


class TestMoreStuff(object):
    def test_remote_branches(self):
        assert ewm.get_remote_branches(all_branches=True) == ['master']
