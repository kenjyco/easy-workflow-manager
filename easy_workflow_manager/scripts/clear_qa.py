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
    """Clear whatever is in a specific (or all) qa branch(es)"""
    if do_all:
        func = ewm.clear_all_qa
    else:
        func = partial(ewm.clear_qa, qa)

    success = func()
    if success:
        print('\nSuccessfully cleared qa branch(es)')
        ewm.show_all_qa()


if __name__ == '__main__':
    main()
