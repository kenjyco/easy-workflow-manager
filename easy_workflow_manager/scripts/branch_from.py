import click
import input_helper as ih
import easy_workflow_manager as ewm
from pprint import pprint


@click.command()
@click.option(
    '--name', '-n', 'name', default='',
    help='Name of new branch to create'
)
@click.argument('branch', nargs=1, default='')
def main(branch, name):
    """Create a new branch from specified branch on origin"""
    ewm.branch_from(branch, name)


if __name__ == '__main__':
    main()
