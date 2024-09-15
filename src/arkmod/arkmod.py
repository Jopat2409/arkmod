import click

from arkmod.vcs import attach_endpoints as vcs_attach_endpoints

def arkmod_command(name: str, required_args, options, flags):
    
    def arkmod_command(func):
        cmd = click.Command(
            name=name,
            callback=func
        )

        map(lambda arg: cmd.params.append(click.Argument(arg[0])))
        map(lambda f: cmd.params.append(click.Option(f[0], is_flag=True, help=f[1])), flags)

@click.group()
def cli():
    pass

vcs_attach_endpoints(cli)

if __name__ == "__main__":
    cli()
