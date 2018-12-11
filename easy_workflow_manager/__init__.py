import re
import settings_helper as sh
import input_helper as ih
import bg_helper as bh
import dt_helper as dh
from pprint import pprint


get_setting = sh.settings_getter(__name__)
QA_BRANCHES = get_setting('QA_BRANCHES')
IGNORE_BRANCHES = get_setting('IGNORE_BRANCHES')
LOCAL_BRANCH = get_setting('LOCAL_BRANCH')
SOURCE_BRANCH = get_setting('SOURCE_BRANCH')

QA_BRANCHES = [QA_BRANCHES] if type(QA_BRANCHES) == str else QA_BRANCHES
IGNORE_BRANCHES = [IGNORE_BRANCHES] if type(IGNORE_BRANCHES) == str else IGNORE_BRANCHES
RX_QA_PREFIX = re.compile('^(' + '|'.join(QA_BRANCHES) + ').*')
NON_SELECTABLE_BRANCHES = set(QA_BRANCHES + IGNORE_BRANCHES)


def get_remote_branches(grep='', all_branches=False):
    """Return list of remote branch names (via git ls-remote --heads)

    - grep: grep pattern to filter branches by (case-insensitive)
    - all_branches: if True, don't filter out non-selectable branches or branches
      prefixed by a qa branch

    Results are alphabetized
    """
    cmd = 'git ls-remote --heads 2>/dev/null | cut -f 2- | cut -c 12- | grep -iE {}'.format(
        repr(grep)
    )
    output = bh.run_output(cmd)
    branches = []
    for branch in re.split('\r?\n', output):
        if all_branches:
            branches.append(branch)
        elif not RX_QA_PREFIX.match(branch) and branch not in NON_SELECTABLE_BRANCHES:
            branches.append(branch)
    return branches


def get_remote_branches_with_times(grep='', all_branches=False):
    """Return list of dicts with remote branch names and last update time

    - grep: grep pattern to filter branches by (case-insensitive)
    - all_branches: if True, don't filter out non-selectable branches or branches
      prefixed by a qa branch

    Results are ordered by most recent commit
    """
    results = []
    bh.run('git fetch --all --prune &>/dev/null')
    for branch in get_remote_branches(grep, all_branches=all_branches):
        if not branch:
            continue
        cmd = 'git show --format="%ci %cr" origin/{} | head -n 1'.format(branch)
        time_data = bh.run_output(cmd)
        results.append({
            'branch': branch,
            'time': time_data
        })
    ih.sort_by_keys(results, 'time', reverse=True)
    return results


def get_qa_env_branches(qa='', display=False):
    """Return a list of dicts with info relating to what is on specified qa env

    - qa: name of qa branch that has things pushed to it
    - display: if True, print the info to the screen
    """
    if qa not in QA_BRANCHES:
        qa = select_qa()
    if not qa:
        return

    results = []
    for branch in get_remote_branches_with_times(grep='^{}--'.format(qa), all_branches=True):
        _qa, _, *env_branches = branch['branch'].split('--')
        branch['contains'] = env_branches
        results.append(branch)

    if results and display:
        print('\nEnvironment: {} ({})'.format(qa, results[0]['time']))
        for branch in results[0]['contains']:
            print('  - {}'.format(branch))

        if len(results) > 1:
            print('  ----------   older   ----------')
            for br in results[1:]:
                print('  - {} ({})'.format(br['branch'], br['time']))
    return results


def get_all_qa_env_branches():
    """Return a dict with all qa environments and their env branches"""
    data = {
        branch: get_qa_env_branches(branch)
        for branch in QA_BRANCHES
    }
    return data


def get_local_branches():
    """Return list of local branch names (via git branch)"""
    output = bh.run_output('git branch | cut -c 3-')
    branches = re.split('\r?\n', output)
    return branches


def get_merged_remote_branches():
    """Return a list of branches on origing that have been merged into SOURCE_BRANCH"""
    bh.run('git fetch --all --prune &>/dev/null')
    cmd = 'git branch -r --merged origin/{} | grep -v origin/{} | cut -c 10-'.format(
        SOURCE_BRANCH, SOURCE_BRANCH
    )
    output = bh.run_output(cmd)
    branches = re.split('\r?\n', output)
    return branches


def get_branch_name():
    """Return current branch name"""
    return bh.run_output('git rev-parse --abbrev-ref HEAD')


def select_qa():
    """Select QA branch"""
    if len(QA_BRANCHES) == 1:
        return QA_BRANCHES[0]
    selected = ih.make_selections(sorted(QA_BRANCHES), prompt='Select QA branch')
    if selected:
        return selected[0]


def select_branches(grep='', all_branches=False):
    """Select remote branch(es); return a list of strings

    - grep: grep pattern to filter branches by (case-insensitive)
    - all_branches: if True, don't filter out non-selectable branches or branches
      prefixed by a qa branch
    """
    return ih.make_selections(
        sorted(get_remote_branches(grep, all_branches=all_branches)),
        prompt='Select remote branch(es)'
    )


def select_branches_with_times(grep='', all_branches=False):
    """Select remote branch(es); return a list of dicts

    - grep: grep pattern to filter branches by (case-insensitive)
    - all_branches: if True, don't filter out non-selectable branches or branches
      prefixed by a qa branch
    """
    return ih.make_selections(
        get_remote_branches_with_times(grep, all_branches=all_branches),
        item_format='{branch} ({time})',
        wrap=False,
        prompt='Select remote branch(es)'
    )


def prompt_for_new_branch_name(name=''):
    """Prompt user for the name of a new allowed branch name

    - name: if provided, verify that it is an acceptable new branch name and
      prompt if it is invalid

    Branch name is not allowed to have the name of any QA_BRANCHES as a prefix
    """
    remote_branches = get_remote_branches()
    local_branches = get_local_branches()
    while True:
        if not name:
            name = ih.user_input('Enter name of new branch to create')
        if not name:
            break
        if name in remote_branches:
            print('{} already exists on remote server'.format(repr(name)))
            name = ''
        elif name in local_branches:
            print('{} already exists locally'.format(repr(name)))
            name = ''
        elif name in NON_SELECTABLE_BRANCHES:
            print('{} is not allowed'.format(repr(name)))
            name = ''
        elif RX_QA_PREFIX.match(name):
            print('{} not allowed to use any of these as prefix: {}'.format(
                repr(name), repr(QA_BRANCHES)
            ))
            name = ''
        else:
            break
    return name.replace(' ', '_')


def new_branch(name, source=SOURCE_BRANCH):
    """Create a new branch from remote source branch"""
    print('\n$ git fetch --all --prune')
    bh.run_or_die('git fetch --all --prune')
    print('\n$ git stash')
    bh.run_or_die('git stash')
    cmd = 'git checkout -b {} origin/{} --no-track'.format(name, source)
    print('\n$ {}'.format(cmd))
    bh.run(cmd)
    cmd = 'git push -u origin {}'.format(name)
    print('\n$ {}'.format(cmd))
    bh.run(cmd)


def get_clean_local_branch(source=SOURCE_BRANCH):
    """Create a clean LOCAL_BRANCH from remote source"""
    print('\n$ git fetch --all --prune')
    bh.run_or_die('git fetch --all --prune')
    print('\n$ git stash')
    bh.run_or_die('git stash')
    cmd = 'git checkout {}'.format(source)
    print('\n$ {}'.format(cmd))
    bh.run_or_die(cmd)
    cmd = 'git branch -D {}'.format(LOCAL_BRANCH)
    print('\n$ {}'.format(cmd))
    bh.run(cmd)
    cmd = 'git checkout -b {} origin/{} --no-track'.format(LOCAL_BRANCH, source)
    print('\n$ {}'.format(cmd))
    bh.run_or_die(cmd)


def merge_branches_locally(*branches, source=SOURCE_BRANCH):
    """Create a clean LOCAL_BRANCH from remote SOURCE_BRANCH and merge in remote branches

    If there are any merge conflicts, you will be dropped into a sub-shell where
    you can resolve them

    Return True if merge was successful
    """
    get_clean_local_branch(source=source)
    bad_merges = []
    for branch in branches:
        cmd = 'git merge origin/{}'.format(branch)
        print('\n$ {}'.format(cmd))
        ret_code = bh.run(cmd)
        if ret_code != 0:
            bad_merges.append(branch)
            cmd = 'git merge --abort'
            print('\n$ {}'.format(cmd))
            bh.run(cmd)

    if bad_merges:
        print('\n!!!!! The following branch(es) had merge conflicts: {}'.format(repr(bad_merges)))
        for branch in bad_merges:
            cmd = 'git merge origin/{}; git status'.format(branch)
            print('\n$ {}'.format(cmd))
            bh.run(cmd)
            print('\nManually resolve the conflict(s), then "git add ____", then "git commit", then "exit"\n')
            bh.run('sh')

            output = bh.run_output("git status -s | grep '^UU'")
            if output != '':
                print('\nConflicts still not resolved, aborting')
                cmd = 'git merge --abort'
                print('\n$ {}'.format(cmd))
                bh.run(cmd)
                return

    return True


def force_push_local(qa, *branches):
    """Da a git push -f of LOCAL_BRANCH to specified qa branch, if available

    - qa: name of qa branch to push to
    - branches: list of remote branch names that were merged into LOCAL_BRANCH

    Return True if push was successful
    """
    current_branch = get_branch_name()
    if current_branch != LOCAL_BRANCH:
        print('Will not do a force push with branch {}, only {}'.format(
            repr(current_branch), repr(LOCAL_BRANCH)
        ))
        return
    if qa not in QA_BRANCHES:
        print('Branch {} is not one of {}'.format(repr(qa), repr(QA_BRANCHES)))
        return

    env_branches = get_qa_env_branches(qa, display=True)
    if env_branches:
        print()
        resp = ih.user_input('Something is already there, are you sure? (y/n)')
        if not resp.lower().startswith('y'):
            return

    ret_codes = []
    combined_name = qa + '--with--' + '--'.join(branches)
    cmd_part = 'git push -uf origin {}:'.format(LOCAL_BRANCH)
    print('\n$ {}'.format(cmd_part + qa))
    ret_codes.append(bh.run(cmd_part + qa))
    print('\n$ {}'.format(cmd_part + combined_name))
    ret_codes.append(bh.run(cmd_part + combined_name))
    if all([x == 0 for x in ret_codes]):
        return True


def deploy_to_qa(qa='', grep=''):
    """Select remote branch(es) to deploy to specified QA branch

    - qa: name of qa branch that will receive this deploy
    - grep: grep pattern to filter branches by (case-insensitive)

    Return True if deploy was successful
    """
    if qa not in QA_BRANCHES:
        qa = select_qa()
    if not qa:
        return

    branches = select_branches_with_times(grep=grep)
    if not branches:
        return

    branch_names = [b['branch'] for b in branches]
    success = merge_branches_locally(*branch_names)
    if success:
        return force_push_local(qa, *branch_names)


def merge_qa_to_source(qa=''):
    """Merge the QA-verified code to SOURCE_BRANCH and delete merged branch(es)

    - qa: name of qa branch to merge to source

    Return True if merge and delete was successful
    """
    if qa not in QA_BRANCHES:
        qa = select_qa()
    if not qa:
        return
    env_branches = get_qa_env_branches(qa, display=True)
    if not env_branches:
        print('Nothing on {} to merge...'.format(qa))
        return

    print()
    resp = ih.user_input('Does this look correct? (y/n)')
    if not resp.lower().startswith('y'):
        print('\nNot going to do anything')
        return

    most_recent = env_branches[0]
    delete_after_merge = most_recent['contains'][:]
    delete_after_merge.extend([b['branch'] for b in env_branches])

    success = merge_branches_locally(SOURCE_BRANCH, source=qa)
    if not success:
        print('\nThere was a failure, not going to delete these: {}'.format(repr(delete_after_merge)))
        return

    cmd = 'git push -uf origin {}:{}'.format(LOCAL_BRANCH, SOURCE_BRANCH)
    print('\n$ {}'.format(cmd))
    ret_code = bh.run(cmd)
    if ret_code != 0:
        print('\nThere was a failure, not going to delete these: {}'.format(repr(delete_after_merge)))
        return

    delete_after_merge.extend(get_merged_remote_branches())
    ret_codes = []
    for branch in delete_after_merge:
        cmd = 'git push origin -d {}'.format(branch)
        print('\n$ {}'.format(cmd))
        ret_codes.append(bh.run(cmd))

    if all([x == 0 for x in ret_codes]):
        return True


def tag_release():
    """Select a recent remote commit on SOURCE_BRANCH to tag

    Return True if tag was successful
    """
    return False
