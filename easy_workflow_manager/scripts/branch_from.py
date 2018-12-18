import click
import input_helper as ih
import easy_workflow_manager as ewm
from pprint import pprint


@click.command()
@click.option(
    '--from-branch', '-f', 'from_branch', default='',
    help='Remote branch name to make the new branch from'
)
@click.argument('name', nargs=1, default='')
def main(name, from_branch):
    """Create a new branch from specified branch on origin"""
    ewm.branch_from(name, from_branch)


if __name__ == '__main__':
    main()
