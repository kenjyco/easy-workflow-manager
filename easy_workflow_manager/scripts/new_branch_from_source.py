import click
import input_helper as ih
import easy_workflow_manager as ewm
from pprint import pprint


@click.command()
@click.argument('name', nargs=1, default='')
def main(name):
    """Create a new branch from SOURCE_BRANCH on origin"""
    name = ewm.prompt_for_new_branch_name(name)
    if name:
        ewm.new_branch(name)


if __name__ == '__main__':
    main()
