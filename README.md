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

## Usage

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


$ venv/bin/ewm-tag-release --help
Usage: ewm-tag-release [OPTIONS]

  Select a recent remote commit on SOURCE_BRANCH to tag

Options:
  --help  Show this message and exit.
```
