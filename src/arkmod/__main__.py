import click

from . import vcs


@click.group()
def cli():
    pass

cli.add_command(vcs.init)
cli.add_command(vcs.create_mod)
cli.add_command(vcs.add_remote)
