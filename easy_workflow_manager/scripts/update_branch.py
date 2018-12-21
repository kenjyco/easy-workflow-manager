import click
import easy_workflow_manager as ewm


@click.command()
@click.option(
    '--pop-stash', '-p', 'pop_stash', is_flag=True, default=False,
    help='Do a `git stash pop` at the end if a stash was made'
)
@click.argument('branch', nargs=1, default='')
def main(branch, pop_stash):
    """Get latest changes from origin into branch"""
    success = ewm.update_branch(branch=branch, pop_stash=pop_stash)
    if success:
        print('\nSuccessfully updated {} branch locally'.format(branch))


if __name__ == '__main__':
    main()
