import click
import input_helper as ih
import easy_workflow_manager as ewm
from pprint import pprint


@click.command()
def main():
    """Select a recent remote commit on SOURCE_BRANCH to tag"""
    success = ewm.tag_release()
    if success:
        print('\nSuccessfully tagged')


if __name__ == '__main__':
    main()
