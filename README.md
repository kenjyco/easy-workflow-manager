## Install

Install with `pip`

```
% pip3 install easy-workflow-manager
```

After running for the first time, the default settings file is copied to
`~/.config/easy-workflow-manager/settings.ini`

```
[default]
QA_BRANCHES = qa, qa2, qa3, qa4
IGNORE_BRANCHES = master, develop, release, uat
LOCAL_BRANCH = mylocalprep
SOURCE_BRANCH = master
```

## Understanding

To understand how you might make use of this project, check out some of the test
helper functions and test code, then the scripts

- `tests/__init__.py` overrwites some settings for `QA_BRANCHES` and
  `SOURCE_BRANCH` and defines several functions that execute `git` commands,
  with the help of `bg_helper.run`
    - `make_file` to create a file using `echo` and output redirection
    - `append_to_file` to append to a file using `echo` and output redirection
    - `change_file_line` to change a line of a file using `sed`
    - `init_clone_cd_repo` to create a git repo at `remote_path`, clone it to
      `local_path`, and cd to `local_path`
        - also creates a file, commits it, and pushes to origin
    - `checkout_branch` to checkout an existing branch
    - `add_commit_push` to add modified files, commit, and push
    - `deploy_merge_tag` to deploy a branch to an open qa environment, merge back
      to source, then tag
        - this makes heavy use of some high-level `easy_workflow_manager` functions
            - `get_empty_qa`
            - `get_remote_branches`
            - `deploy_to_qa`
            - `get_qa_env_branches`
            - `merge_qa_to_source`
            - `tag_release`
            - `get_tag_message`
- `tests/conftest.py` defines a single "fixture" that creates a new folder in
  `/tmp` to contain a new "remote git repository" and its "local clone" per
  defined test class
    - the fixture yields to let the methods of the test class run before
      deleting the temporary data
        - this would be a good place to drop a `pytest.set_trace()` if you want
          to inspect temporary repos and their commits
- `tests/test_stuff.py` defines two test classes with some test methods
    - `TestNewRepo.test_remote_branches` to make sure the only remote branch is
      `master`, create 3 new branches, confirm that various invocations of
      `ewm.get_remote_branches()` return what you'd expect
    - `TestNewRepo.test_local_branches` to confirm that various invocations of
      `ewm.get_local_branches()` return what you'd expect
    - `TestNewRepo.test_qa` to confirm that no qa branches are in use and that
      `ewm.get_empty_qa()` returns the set of the overwritten `QA_BRANCHES`,
      then use the helper functions to append to a file, commit the changes,
      push to the remote
        - then check that `ewm.deploy_to_qa()` gets the specified branch(es)
          onto the specified qa branch
        - then check that `ewm.clear_qa()` clears the specified qa branch
    - `TestNewRepo.test_change_commit_push()` to update a file
        - then check that `ewm.get_merged_remote_branches()` does not include
          the branch that was just updated
    - `TestNewRepo.test_tagging()` to check that merging a branch to source and
      tagging it works

## Commands / scripts

```
$ venv/bin/ewm-new-branch-from-source --help
Usage: ewm-new-branch-from-source [OPTIONS] [NAME]

  Create a new branch from SOURCE_BRANCH on origin

Options:
  --help  Show this message and exit.


$ venv/bin/ewm-deploy-to-qa --help
Usage: ewm-deploy-to-qa [OPTIONS] [QA]

  Select remote branch(es) to deploy to specified QA branch

Options:
  -g, --grep TEXT  case-insensitive grep pattern to filter branch names by
  --help           Show this message and exit.


$ venv/bin/ewm-qa-to-source --help
Usage: ewm-qa-to-source [OPTIONS] [QA]

  Merge the QA-verified code to SOURCE_BRANCH and delete merged branch(es)

Options:
  --help  Show this message and exit.


$ venv/bin/ewm-show-qa --help
Usage: ewm-show-qa [OPTIONS] [QA]

  Show what is in a specific (or all) qa branch(es)

Options:
  -a, --all  Select all qa environments
  --help     Show this message and exit.


$ venv/bin/ewm-clear-qa --help
Usage: ewm-clear-qa [OPTIONS] [QA]

  Clear whatever is in a specific (or all) qa branch(es)

Options:
  -a, --all  Select all qa environments
  --help     Show this message and exit.


$ venv/bin/ewm-tag-release --help
Usage: ewm-tag-release [OPTIONS]

  Select a recent remote commit on SOURCE_BRANCH to tag

Options:
  --help  Show this message and exit.
```

## Running Tests

Clone this repo then run the `./dev-setup.bash` script to create a virtual
environment that includes `pytest`

```
% ./dev-setup.bash
```

Run pytest with the `-v` an `-s` options to tests invoked as well as all the
generated `git` commands and their output

```
% venv/bin/pytest -vs
```

## Resources

- <https://git-scm.com/book/en/v2>
