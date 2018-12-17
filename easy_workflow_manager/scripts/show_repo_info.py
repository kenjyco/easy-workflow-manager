import click
import easy_workflow_manager as ewm


@click.command()
def main():
    """Show info about the repo"""
    ewm.show_repo_info()


if __name__ == '__main__':
    main()
