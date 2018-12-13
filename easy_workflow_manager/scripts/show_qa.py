import click
import input_helper as ih
import easy_workflow_manager as ewm
from functools import partial
from pprint import pprint


@click.command()
@click.option(
    '--all', '-a', 'do_all', is_flag=True, default=False,
    help='Select all qa environments'
)
@click.argument('qa', nargs=1, default='')
def main(qa, do_all):
    """Show what is in a specific (or all) qa branch(es)"""
    if qa not in ewm.QA_BRANCHES:
        do_all = True

    if do_all:
        func = ewm.show_all_qa
    else:
        func = partial(ewm.show_qa, qa)
    func()


if __name__ == '__main__':
    main()
