__all__ = [
    'make_file', 'append_to_file', 'change_file_line', 'init_clone_cd_repo',
    'add_commit_push', 'checkout_branch', 'deploy_merge_tag'
]


import os
import random
import bg_helper as bh
import easy_workflow_manager as ewm


os.environ['QA_BRANCHES'] = 'qa1, qa2, qa3'
os.environ['IGNORE_BRANCHES'] = 'master'
os.environ['SOURCE_BRANCH'] = 'master'
os.environ['TAG_BRANCH'] = 'master'


def make_file(fname='some-file.txt', initial_text='some stuff'):
    """Create a file using 'echo' and output redirection"""
    cmd = 'echo {} > {}'.format(repr(initial_text), repr(fname))
    return bh.run(cmd)


def append_to_file(fname='some-file.txt', text='more stuff'):
    """Append to a file using 'echo' and output redirection"""
    cmd = 'echo {} >> {}'.format(repr(text), repr(fname))
    return bh.run(cmd)


def change_file_line(fname='some-file.txt', text='CHANGED', line=1):
    """Change a line of a file using 'sed'"""
    tmp_name = '__{}'.format(fname)
    cmd1 = "sed '{}s/.*/{}/' {} > {}".format(line, text, fname, tmp_name)
    cmd2 = 'mv {} {}'.format(repr(tmp_name), repr(fname))
    ret_code = bh.run(cmd1)
    if ret_code == 0:
        return bh.run(cmd2)


def init_clone_cd_repo(remote_path, local_path):
    """Create a git repo at remote_path, clone it to local_path, and cd to local_path

    Also create a file, commit it, and push to origin; Return True if successful
    """
    print()
    ret_code = bh.run('git init --bare {}'.format(remote_path))
    if ret_code == 0:
        ret_code = bh.run('git clone {} {}'.format(remote_path, local_path))
        if ret_code == 0:
            os.chdir(local_path)
            ret_code = make_file()
            if ret_code == 0:
                ret_code = bh.run(
                    'git config user.name "Someone"; '
                    'git config user.email "someone@email.com"'
                )
                ret_code += bh.run(
                    'git add .; '
                    'git commit -m "Initial commit"; '
                    'git push -u origin master'
                )
                if ret_code == 0:
                    return True
    raise Exception('Creating test remote/local repo failed')


def checkout_branch(branch):
    """Check out an existing branch"""
    return bh.run('git checkout {}'.format(branch))


def add_commit_push(show=True):
    """Add modified files, commit, and push"""
    branch = ewm.get_branch_name()
    files = [x.split(' ', 1)[-1] for x in ewm.get_status()]
    message = 'Changed ' + ', '.join(files) + ' in branch ' + branch
    return bh.run(
        'git add .; git commit -m "{}"; git push'.format(message),
        show=show
    )

def deploy_merge_tag(branch):
    """Deploy a branch to an open qa environment, merge back to source, then tag

    Return True if ewm_tag_release was successful
    """
    qa = random.choice(list(ewm.get_empty_qa()))
    orig_remote_branches = ewm.get_remote_branches()
    assert branch in orig_remote_branches
    deployed_branch = ewm.deploy_to_qa(qa=qa, branches=branch)
    assert qa == deployed_branch
    qa_env_branches = ewm.get_qa_env_branches(qa=qa, display=True)
    merged_branch = ewm.merge_qa_to_source(qa=qa, auto=True)
    remote_branches = ewm.get_remote_branches()
    assert branch not in remote_branches
    tag_success = ewm.tag_release(auto=True)
    tag_message = ewm.get_tag_message()
    assert branch in tag_message
    return tag_success
