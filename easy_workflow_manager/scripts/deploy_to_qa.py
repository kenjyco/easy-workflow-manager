import click
import input_helper as ih
import easy_workflow_manager as ewm
from pprint import pprint


@click.command()
@click.option(
    '--grep', '-g', 'grep', default='',
    help='case-insensitive grep pattern to filter branch names by'
)
@click.argument('qa', nargs=1, default='')
def main(qa, grep):
    """Select remote branch(es) to deploy to specified QA branch"""
    deployed_to = ewm.deploy_to_qa(qa=qa, grep=grep)
    if deployed_to:
        print('\nDeploy to {} was successful'.format(repr(deployed_to)))


if __name__ == '__main__':
    main()
