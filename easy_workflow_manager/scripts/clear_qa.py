import click
import input_helper as ih
import easy_workflow_manager as ewm
from pprint import pprint


@click.command()
@click.option(
    '--all', '-a', 'all_qa', is_flag=True, default=False,
    help='Select all qa environments'
)
@click.argument('qa', nargs=1, default='')
def main(qa, all_qa):
    """Clear whatever is in a specific (or all) qa branch(es)"""
    success = ewm.clear_qa(qa, all_qa=all_qa)
    if success:
        print('\nSuccessfully cleared qa branch(es)')
        ewm.show_qa(all_qa=True)


if __name__ == '__main__':
    main()
