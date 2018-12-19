import re
import inspect
import settings_helper as sh
import input_helper as ih
import fs_helper as fh
import bg_helper as bh
import dt_helper as dh
from io import StringIO
from pprint import pprint


logger = fh.get_logger(__name__)
get_setting = sh.settings_getter(__name__)
QA_BRANCHES = get_setting('QA_BRANCHES')
IGNORE_BRANCHES = get_setting('IGNORE_BRANCHES')
LOCAL_BRANCH = get_setting('LOCAL_BRANCH')
SOURCE_BRANCH = get_setting('SOURCE_BRANCH')

QA_BRANCHES = [QA_BRANCHES] if type(QA_BRANCHES) == str else QA_BRANCHES
IGNORE_BRANCHES = [IGNORE_BRANCHES] if type(IGNORE_BRANCHES) == str else IGNORE_BRANCHES
RX_QA_PREFIX = re.compile('^(' + '|'.join(QA_BRANCHES) + ').*')
RX_NON_TAG = re.compile(r'.*-\d+-g[a-f0-9]+$')
RX_CONFIG_URL = re.compile('^url\s*=\s*(\S+)$')
NON_SELECTABLE_BRANCHES = set(QA_BRANCHES + IGNORE_BRANCHES)
FUNCS_ALLOWED_TO_FORCE_PUSH = ('deploy_to_qa', 'merge_qa_to_source')
FUNCS_ALLOWED_TO_FORCE_PUSH_TO_SOURCE = ('merge_qa_to_source', )


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
    if not output:
        return branches
    for branch in re.split('\r?\n', output):
        if all_branches:
            branches.append(branch)
        elif not RX_QA_PREFIX.match(branch) and branch not in NON_SELECTABLE_BRANCHES:
            branches.append(branch)
    return branches


def get_remote_branches_with_times(grep='', all_branches=False, fetch=True):
    """Return list of dicts with remote branch names and last update time

    - grep: grep pattern to filter branches by (case-insensitive)
    - all_branches: if True, don't filter out non-selectable branches or branches
      prefixed by a qa branch
    - fetch: if True, do a `git fetch` before calling get_remote_branches

    Results are ordered by most recent commit
    """
    results = []
    if fetch:
        bh.run('git fetch --all --prune >/dev/null 2>&1')
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


def get_qa_env_branches(qa='', display=False, all_qa=False):
    """Return a list of dicts with info relating to what is on specified qa env

    - qa: name of qa branch that has things pushed to it
        - if no name is passed in assume all_qa=True
    - display: if True, print the info to the screen
    - all_qa: if True and no qa passed in, return info for all qa envs
    """
    if qa:
        if qa not in QA_BRANCHES:
            return
        qa_branches = [qa]
    else:
        all_qa = True
    if all_qa:
        qa_branches = QA_BRANCHES

    full_results = []
    bh.run('git fetch --all --prune >/dev/null 2>&1')
    for qa_name in qa_branches:
        results = []
        for branch in get_remote_branches_with_times(grep='^{}--'.format(qa_name), all_branches=True, fetch=False):
            _qa, _, *env_branches = branch['branch'].split('--')
            branch['contains'] = env_branches
            results.append(branch)

        if results and display:
            print('\nEnvironment: {} ({})'.format(qa_name, results[0]['time']))
            for branch in results[0]['contains']:
                print('  - {}'.format(branch))

            if len(results) > 1:
                print('  ----------   older   ----------')
                for br in results[1:]:
                    print('  - {} ({})'.format(br['branch'], br['time']))
        full_results.extend(results)
    return full_results


def get_non_empty_qa():
    """Return a set of all QA branches with something deployed"""
    return set([
        eb['branch'].split('--', 1)[0]
        for eb in get_qa_env_branches()
    ])


def get_empty_qa():
    """Return a set of all QA branches with nothing deployed"""
    non_empty = get_non_empty_qa()
    return set(QA_BRANCHES) - non_empty


def get_local_branches(grep=''):
    """Return list of local branch names (via git branch)

    - grep: grep pattern to filter branches by (case-insensitive)
    """
    output = bh.run_output('git branch | cut -c 3- | grep -iE {}'.format(repr(grep)))
    if not output:
        return []
    branches = re.split('\r?\n', output)
    return branches


def get_merged_remote_branches():
    """Return a list of branches on origin that have been merged into SOURCE_BRANCH"""
    bh.run('git fetch --all --prune >/dev/null 2>&1')
    cmd = 'git branch -r --merged origin/{} | grep -v origin/{} | cut -c 10-'.format(
        SOURCE_BRANCH, SOURCE_BRANCH
    )
    output = bh.run_output(cmd)
    branches = []
    if not output:
        return branches
    branches = re.split('\r?\n', output)
    return branches


def get_merged_local_branches():
    """Return a list of local branches that have been merged into SOURCE_BRANCH"""
    cmd = 'git branch --merged {} | cut -c 3- | grep -v "^{}$"'.format(
        SOURCE_BRANCH, SOURCE_BRANCH
    )
    output = bh.run_output(cmd)
    branches = []
    if not output:
        return branches
    branches = re.split('\r?\n', output)
    return branches


def get_branch_name():
    """Return current branch name"""
    return bh.run_output('git rev-parse --abbrev-ref HEAD')


def get_tracking_branch():
    """Return remote tracking branch for current branch"""
    branch = get_branch_name()
    cmd = 'git branch -r | grep "/{}$" | grep -v HEAD'.format(branch)
    return bh.run_output(cmd)


def get_local_repo_path():
    """Return path to local repository"""
    return fh.repopath()


def get_origin_url():
    """Return url to remote origin (from .git/config file)"""
    local_path = get_local_repo_path()
    if not local_path:
        return
    cmd = 'grep "remote \\"origin\\"" -A 2 {}/.git/config | grep url'.format(
        local_path
    )
    output = bh.run_output(cmd)
    match = RX_CONFIG_URL.match(output)
    if match:
        return match.group(1)


def get_unpushed_commits():
    """Return a list of any local commits that have not been pushed"""
    cmd = 'git log --find-renames --no-merges --oneline @{u}.. 2>/dev/null'
    output = bh.run_output(cmd)
    commits = []
    if output:
        commits = re.split('\r?\n', output)
    return commits


def get_first_commit_id():
    """Get the first commit id for the repo"""
    return bh.run_output('git rev-list --max-parents=0 HEAD')


def get_last_commit_id():
    """Get the last commit id for the repo"""
    return bh.run_output('git log --no-merges  --format="%h" -1')


def get_commits_since_last_tag(until=''):
    """Return a list of commits made since last_tag

    - until: a recent commit id to stop at (instead of last commit)

    If no tag has been made, returns a list of commits since the first commit
    """
    tag = get_last_tag()
    commits = []
    if not tag:
        tag = get_first_commit_id()
    if not until:
        until = get_last_commit_id()
    cmd = 'git log --find-renames --no-merges --oneline {}..{}'.format(tag, until)
    output = bh.run_output(cmd)
    if output:
        commits = re.split('\r?\n', output)
    return commits


def get_stashlist():
    """Return a list of any local stashes"""
    cmd = 'git stash list'
    output = bh.run_output(cmd)
    stashes = []
    if output:
        stashes = re.split('\r?\n', output)
    return stashes


def get_status():
    """Return a list of any modified or untracked files"""
    cmd = 'git status -s'
    output = bh.run_output(cmd)
    results = []
    if output:
        results = re.split('\r?\n\s*', output)
    return results


def get_tags():
    """Return a list of all tags with most recent first"""
    cmd = 'git describe --tags $(git rev-list --tags) 2>/dev/null'
    output = bh.run_output(cmd)
    tags = []
    if not output:
        return tags
    for tag in re.split('\r?\n', output):
        if not RX_NON_TAG.match(tag):
            tags.append(tag)
    return tags


def get_last_tag():
    """Return the most recent tag made"""
    return bh.run_output('git describe --tags $(git rev-list --tags --max-count=1 2>/dev/null) 2>/dev/null')


def get_tag_message(tag=''):
    """Return the message for the most recent tag made

    - tag: name of a tag that was made
    """
    if not tag:
        tag = get_last_tag()
        if not tag:
            return
    output = bh.run_output('git tag -n99 {}'.format(tag))
    return output.replace(tag, '').strip()


def get_repo_info_dict():
    """Return a dict of info about the repo"""
    data = {}
    repo_path = get_local_repo_path()
    if not repo_path:
        return data
    data['branch'] = get_branch_name()
    data['branch_tracking'] = get_tracking_branch()
    data['path'] = repo_path
    data['url'] = get_origin_url()
    data['last_tag'] = get_last_tag()
    data['unpushed'] = get_unpushed_commits()
    data['commits_since_last_tag'] = get_commits_since_last_tag()
    data['stashes'] = get_stashlist()
    data['status'] = get_status()
    return data


def get_repo_info_string():
    """Build up a string of info from get_repo_info_dict and return it"""
    info = get_repo_info_dict()
    if not info:
        return ''
    s = StringIO()
    s.write('{} .::. {} .::. {}'.format(
        info['path'], info['url'], info['branch']
    ))
    if info['branch_tracking']:
        s.write('\n- tracking: {}'.format(info['branch_tracking']))
    if info['last_tag']:
        s.write('\n- last tag: {}'.format(info['last_tag']))
    if info['status']:
        s.write('\n- status:')
        for filestat in info['status']:
            s.write('\n    - {}'.format(filestat))
    if info['stashes']:
        s.write('\n\n- stashes:')
        for stash in info['stashes']:
            s.write('\n    - {}'.format(stash))
    if info['unpushed']:
        s.write('\n\n- unpushed commits:')
        for commit in info['unpushed']:
            s.write('\n    - {}'.format(commit))
    if info['commits_since_last_tag']:
        s.write('\n\n- commits since last tag:')
        for commit in info['commits_since_last_tag']:
            s.write('\n    - {}'.format(commit))
    return s.getvalue()


def show_repo_info():
    """Show info about the repo"""
    print(get_repo_info_string())


def select_qa(empty_only=False, full_only=False, multi=False):
    """Select QA branch(es)

    - empty_only: if True, only show empty qa environments in generated menu
    - full_only: if True, only show non-empty qa environments in generated menu
    - multi: if True, allow selecting multiple qa branches
    """
    assert not empty_only or not full_only, 'Cannot select both empty_only and full_only'
    if empty_only:
        items = sorted(list(get_empty_qa()))
    elif full_only:
        items = sorted(list(get_non_empty_qa()))
    else:
        items = sorted(QA_BRANCHES)
    if len(items) == 1:
        print('Selected: {}'.format(repr(items[0])))
        return items[0]
    elif len(items) == 0:
        print('No items to select')
        return
    prompt = 'Select QA branch'
    if multi:
        prompt = 'Select QA branches'
    selected = ih.make_selections(items, prompt=prompt)
    if selected:
        if not multi:
            return selected[0]
        return selected


def select_qa_with_times(multi=False):
    """Select QA branch(es)

    - multi: if True, allow selecting multiple qa branches
    """
    if len(QA_BRANCHES) == 1:
        return QA_BRANCHES[0]
    one = not multi
    grep = '(' + '|'.join(['^{}$'.format(qa) for qa in QA_BRANCHES]) + ')'
    return select_branches_with_times(grep=grep, all_branches=True, one=one)


def select_branches(grep='', all_branches=False, one=False):
    """Select remote branch(es); return a list of strings

    - grep: grep pattern to filter branches by (case-insensitive)
    - all_branches: if True, don't filter out non-selectable branches or branches
      prefixed by a qa branch
    - one: if True, only select one branch
    """
    prompt = 'Select remote branch(es)'
    if one:
        prompt = 'Select remote branch'
    selected =  ih.make_selections(
        sorted(get_remote_branches(grep, all_branches=all_branches)),
        prompt=prompt
    )
    if selected:
        if one:
            return selected[0]
        return selected


def select_branches_with_times(grep='', all_branches=False, one=False):
    """Select remote branch(es); return a list of dicts

    - grep: grep pattern to filter branches by (case-insensitive)
    - all_branches: if True, don't filter out non-selectable branches or branches
      prefixed by a qa branch
    - one: if True, only select one branch
    """
    prompt = 'Select remote branch(es)'
    if one:
        prompt = 'Select remote branch'
    selected = ih.make_selections(
        get_remote_branches_with_times(grep, all_branches=all_branches),
        item_format='{branch} ({time})',
        wrap=False,
        prompt=prompt
    )
    if selected:
        if one:
            return selected[0]
        return selected


def select_commit_to_tag(n=10):
    """Select a commit hash from recent commits

    - n: number of recent commits to choose from
    """
    branch = get_branch_name()
    assert branch == SOURCE_BRANCH, (
        'Must be on {} branch to select commit, not {}'.format(SOURCE_BRANCH, branch)
    )
    last_tag = get_last_tag()
    cmd_part = 'git log --find-renames --no-merges --oneline'
    if last_tag:
        cmd = cmd_part + ' {}..'.format(last_tag)
    else:
        cmd = cmd_part + ' -{}'.format(n)
    output = bh.run_output(cmd)
    if not output:
        return
    items = re.split('\r?\n', output)[:n]
    selected = ih.make_selections(
        items,
        wrap=False,
        prompt='Select commit to tag'
    )
    if selected:
        return selected[0].split(' ', 1)[0]


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
    """Create a new branch from remote source branch

    - name: name of new branch
    - source: name of source branch (default SOURCE_BRANCH)

    Return True if branch creation and push to origin were successful
    """
    print('\n$ git fetch --all --prune')
    bh.run_or_die('git fetch --all --prune')
    print('\n$ git stash')
    bh.run_or_die('git stash')
    cmd = 'git checkout -b {} origin/{} --no-track'.format(name, source)
    print('\n$ {}'.format(cmd))
    ret_code = bh.run(cmd)
    if ret_code == 0:
        cmd = 'git push -u origin {}'.format(name)
        print('\n$ {}'.format(cmd))
        return bh.run(cmd)


def branch_from(branch='', name=''):
    """Create a new branch from specified branch on origin

    - branch: remote branch name to make the new branch from
    - name: name of new branch to create

    Return True if branch creation and push to origin were successful
    """
    remote_branches = get_remote_branches(all_branches=True)
    if not branch or branch not in remote_branches:
        selected = select_branches_with_times(all_branches=True, one=True)
        if selected:
            branch = selected['branch']
        else:
            return

    name = prompt_for_new_branch_name(name)
    if name:
        return new_branch(name, branch)


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


def force_push_local(qa='', *branches, to_source=False):
    """Da a git push -f of LOCAL_BRANCH to specified qa branch or SOURCE_BRANCH

    - qa: name of qa branch to push to
    - branches: list of remote branch names that were merged into LOCAL_BRANCH
    - to_source: if True, force push to SOURCE_BRANCH (only allowed if func
      that called it is in FUNCS_ALLOWED_TO_FORCE_PUSH_TO_SOURCE)

    Return True if push was successful

    Only allowed to be called from funcs in FUNCS_ALLOWED_TO_FORCE_PUSH (because
    these are functions that just finished creating a clean LOCAL_BRANCH from the
    remote SOURCE_BRANCH, with other remote branches combined in (via rebase or
    merge)
    """
    caller = inspect.stack()[1][3]
    assert caller in FUNCS_ALLOWED_TO_FORCE_PUSH, (
        'Only allowed to invoke force_push_local func from {}... not {}'.format(
            repr(FUNCS_ALLOWED_TO_FORCE_PUSH), repr(caller)
        )
    )
    if to_source:
        assert caller in FUNCS_ALLOWED_TO_FORCE_PUSH_TO_SOURCE, (
            'Only allowed to force push to {} when invoked from {}... not {}'.format(
                SOURCE_BRANCH, repr(FUNCS_ALLOWED_TO_FORCE_PUSH_TO_SOURCE), repr(caller)
            )
        )
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

    Return qa name if deploy was successful
    """
    if qa not in QA_BRANCHES:
        qa = select_qa(empty_only=True)
    if not qa:
        return

    branches = select_branches_with_times(grep=grep)
    if not branches:
        return

    branch_names = [b['branch'] for b in branches]
    success = merge_branches_locally(*branch_names)
    if success:
        success2 = force_push_local(qa, *branch_names)
        if success2:
            return qa


def delete_remote_branches(*branches):
    """Delete the specified remote branches

    Return True if all deletes were successful
    """
    ret_codes = []
    for branch in sorted(set(branches)):
        cmd = 'git push origin -d {}'.format(branch)
        print('\n$ {}'.format(cmd))
        ret_codes.append(bh.run(cmd))

    if all([x == 0 for x in ret_codes]):
        return True


def delete_local_branches(*branches):
    """Delete the specified local branches

    Return True if all deletes were successful
    """
    ret_codes = []
    for branch in sorted(set(branches)):
        cmd = 'git branch -D {}'.format(branch)
        print('\n$ {}'.format(cmd))
        ret_codes.append(bh.run(cmd))

    if all([x == 0 for x in ret_codes]):
        return True


def merge_qa_to_source(qa=''):
    """Merge the QA-verified code to SOURCE_BRANCH and delete merged branch(es)

    - qa: name of qa branch to merge to source

    Return qa name if merge(s) and delete(s) were successful
    """
    if qa not in QA_BRANCHES:
        show_qa(all_qa=True)
        print()
        qa = select_qa(full_only=True)
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
    success = delete_remote_branches(*delete_after_merge)
    if success:
        return qa


def update_branch(branch='', pop_stash=False):
    """Get latest changes from origin into branch

    - branch: name of branch to update (if not current checked out)
    - pop_stash: if True, do `git stash pop` at the end if a stash was made

    Return True if update was successful
    """
    if branch:
        if branch not in get_local_branches():
            cmd = 'git checkout origin/{}'.format(branch)
        else:
            cmd = 'git checkout {}'.format(branch)
        print('\n$ {}'.format(cmd))
        bh.run_or_die(cmd)

    branch = get_branch_name()
    url = get_origin_url()
    tracking = get_tracking_branch()
    if not url:
        print('\nLocal-only repo, not updating')
        return
    elif tracking:
        print('\n$ git stash')
        stash_output = bh.run_output('git stash')
        print(stash_output)
        print('\n$ git pull --rebase')
        ret_code = bh.run('git pull --rebase')
        if ret_code != 0:
            return
        if branch != SOURCE_BRANCH:
            cmd = 'git rebase origin/{}'.format(SOURCE_BRANCH)
            print('\n$ {}'.format(cmd))
            ret_code = bh.run(cmd)
            if ret_code != 0:
                return
        if pop_stash and stash_output != 'No local changes to save':
            print('\n$ git stash pop')
            bh.run_output('git stash pop')
    else:
        print('\n$ git fetch')
        bh.run_output('git fetch')

    return True


def show_remote_branches(grep='', all_branches=False):
    """Show the remote branch names and last update times

    - grep: grep pattern to filter branches by (case-insensitive)
    - all_branches: if True, don't filter out non-selectable branches or branches
      prefixed by a qa branch

    Results are ordered by most recent commit
    """
    branches = get_remote_branches_with_times(grep=grep, all_branches=all_branches)
    if branches:
        make_string = ih.get_string_maker(item_format='- {branch} .::. {time}')
        print('\n'.join([make_string(branch) for branch in branches]))


def show_local_branches(grep=''):
    """Show the local branches; results are alphabetized

    - grep: grep pattern to filter branches by (case-insensitive)
    """
    branches = get_local_branches(grep=grep)
    for branch in branches:
        print('- {}'.format(branch))


def show_qa(qa='', all_qa=False):
    """Show what is on a specific QA branch

    - qa: name of qa branch that may have things pushed to it
    - all_qa: if True and no qa passed in, return info for all qa envs
    """
    get_qa_env_branches(qa, display=True, all_qa=all_qa)


def clear_qa(*qas, all_qa=False):
    """Clear whatever is on selected QA branches

    - qas: names of qa branches that may have things pushed to them
        - if no qas passed in, you will be prompted to select multiple
    - all_qa: if True and no qa passed in, clear all qa branches

    Return True if deleting branch(es) was successful
    """
    if not all_qa:
        valid = set(QA_BRANCHES).intersection(set(qas))
        if valid == set():
            qas = select_qa_with_times(multi=True)
            if not qas:
                return
            qas = [b['branch'] for b in qas]
        else:
            qas = list(valid)
    else:
        qas = QA_BRANCHES

    parts = []
    for qa in qas:
        parts.append('^{}$|^{}--'.format(qa, qa))
    branches = get_remote_branches(
        grep='|'.join(parts),
        all_branches=True
    )

    if not branches:
        return
    print('\n', branches, '\n')
    resp = ih.user_input('Does this look correct? (y/n)')
    if not resp.lower().startswith('y'):
        print('\nNot going to do anything')
        return

    return delete_remote_branches(*branches)


def tag_release():
    """Select a recent remote commit on SOURCE_BRANCH to tag

    Return True if tag was successful
    """
    success = update_branch(SOURCE_BRANCH)
    if not success:
        return
    print('\nRecent commits')
    commit_id = select_commit_to_tag()
    if not commit_id:
        return
    tag = dh.local_now_string('%Y-%m%d-%H%M%S')
    commits = get_commits_since_last_tag(until=commit_id)
    notes_file = '/tmp/{}.txt'.format(tag)
    summary = ih.user_input('One-line summary for tag')
    if not summary:
        summary = tag
    with open(notes_file, 'w') as fp:
        fp.write('{}\n\n'.format(summary))
        fp.write('\n'.join(commits) + '\n')
    bh.run('vim {}'.format(notes_file))
    cmd = 'git tag -a {} {} -F {}'.format(
        tag, commit_id, repr(notes_file)
    )
    print('Tag command would be -> {}'.format(cmd))
    resp = ih.user_input('Continue? (y/n)')
    if not resp.lower().startswith('y'):
        return

    print('\n$ {}'.format(cmd))
    ret_code = bh.run(cmd)
    if ret_code != 0:
        return

    print('\n$ git push --tags')
    return bh.run('git push --tags')
