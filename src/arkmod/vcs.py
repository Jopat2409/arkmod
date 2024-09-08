import os
import click
import shutil

from .console import log_error
from .gitinstance import GitInstance
import gitcommands



@click.command()
def init():

    if not GitInstance.is_git_installed():
        raise ImportError("You must have git configured on your local system to run arkmod version control.")

    GitInstance.init()
    with open(".arkmod", "x"):
        pass

    GitInstance.add_and_commit('.arkmod', "Initial Commit")

@click.command()
@click.argument("name")
@click.argument("origin", default="")
@click.argument("--remote-branch", default="main")
@click.option("--no-copy", default=False)
def create_mod(name: str, origin: str, __remote_branch: str, no_copy: bool):

    # Ensure the mod does not already exist
    rel_path = os.path.join("Mods", name)
    if os.path.isdir(rel_path):
        log_error(f"{name} is already a mod. See 'arkmod register-mod --help' to use vcs for a mod not created with this tool.")
        return

    with GitInstance.Transaction(auto_rollback = True) as transaction:

        # Create new git local branch
        if not transaction.execute(gitcommands.CreateBranch(name, from_="master")):
            log_error(f"Error creating branch for mod {name}. Please see 'arkmod create-mod --help' for more information")
            return

        # Add remote if specified
        if origin:
            if not transaction.execute(gitcommands.CreateRemote(f"origin_{name}", origin)):
                log_error(f"Error creating remote origin for mod {name}. Ensure that your git URL is valid and try again.")
                return
            if not transaction.execute(gitcommands.SetBranchRemote(name, f"origin_{name}", __remote_branch))

        os.mkdir(rel_path)

        # Copy
        if not no_copy:
            shutil.copyfile(".\\Mods\\GenericMod\\GenericMod.umap", f"Mods\\{name}\\{name}.umap")
            shutil.copyfile(".\\Mods\\GenericMod\\PrimalGameData_BP_GenericMod.uasset", f"Mods\\{name}\\PrimalGameData_BP_{name}.uasset")
            shutil.copyfile(".\\Mods\\GenericMod\\TestGameMode_GenericMod.uasset", f"Mods\\{name}\\TestGameMode_{name}.uasset")

        transaction.set_success()

@click.command()
@click.argument("mod")
@click.argument("remote-url")
@click.argument("remote-master", default="main")
def add_remote(mod: str, remote_url: str, remote_master: str = "main") -> None:
    with GitInstance.Transaction() as transaction:
        transaction.execute(gitcommands.CreateRemote(f"origin_{mod}", remote_url))
        transaction.execute(gitcommands.SetBranchRemote(mod, f"origin_{mod}", remote_master))
