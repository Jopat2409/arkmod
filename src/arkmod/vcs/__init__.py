
from . import vcs


def attach_endpoints(cli: callable):
    cli.add_command(vcs.init)
    cli.add_command(vcs.detach)

    cli.add_command(vcs.list_mods)
    cli.add_command(vcs.current_mod)

    cli.add_command(vcs.create_mod)
    cli.add_command(vcs.set_remote)
    cli.add_command(vcs.edit_mod)
    cli.add_command(vcs.create_release)
