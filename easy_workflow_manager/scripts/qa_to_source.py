import click
import input_helper as ih
import easy_workflow_manager as ewm
from pprint import pprint


@click.command()
@click.argument('qa', nargs=1, default='')
def main(qa):
    """Merge the QA-verified code to SOURCE_BRANCH and delete merged branch(es)"""
    if qa not in ewm.QA_BRANCHES:
        qa = ewm.select_qa()
    if not qa:
        return

    success = ewm.merge_qa_to_source(qa)
    if success:
        print('Successfully merged {} to {} and deleted branches'.format(qa, ewm.SOURCE_BRANCH))


if __name__ == '__main__':
    main()
