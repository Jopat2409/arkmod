import os
import json

from . import gitcommands
from ..console import run_command_fetch_output, log_error

class ArkModConfig:

    current_mod: str = None
    DEFAULT_COPYFILES: dict[str, str] = {
        ".\\Mods\\GenericMod\\GenericMod.umap": "Mods\\<ArkMod:ModName>\\<ArkMod:ModName>.umap",
        ".\\Mods\\GenericMod\\PrimalGameData_BP_GenericMod.uasset": "Mods\\<ArkMod:ModName>\\PrimalGameData_BP_<ArkMod:ModName>.uasset",
        ".\\Mods\\GenericMod\\TestGameMode_GenericMod.uasset": "Mods\\<ArkMod:ModName>\\TestGameMode_<ArkMod:ModName>.uasset"
    }


    @staticmethod
    def init_configfile(db: str, base_branch: str = "master", from_existing_git: bool = False):
        with open('.arkmod', 'w+') as f:
            json.dump({
                "config": {
                    "copyfiles": ArkModConfig.DEFAULT_COPYFILES,
                    "from-existing": from_existing_git,
                    "current-mod": None,
                    "git-base": base_branch,
                    "mod-db": db
                },
                "mods": {}
            }, f, indent=2)

    @staticmethod
    def save_configfile(data: dict) -> None:
        cmd = gitcommands.CheckoutBranch(data["config"]["git-base"])
        cmd.execute()
        with open('.arkmod', 'w+') as f:
            json.dump(data, f, indent=2)
        gitcommands.Commit(('.arkmod',), "Added additional mods to .arkmod config.").execute()
        cmd.rollback()
        run_command_fetch_output(f'git merge {data["config"]["git-base"]}')

    @staticmethod
    def load_configfile() -> dict:
        if not os.path.isfile('.arkmod'):
            return {}
        with open('.arkmod', "r+") as f:
            return json.load(f)


def pass_arkmod_data(name: str = "arkmod_data"):
    def pass_arkmod_data(func):
        def inner(*args, **kwargs):
            data = ArkModConfig.load_configfile()
            if not data:
                return log_error("You must initialise arkmod using 'arkmod init' before creating any mods. See arkmod --help for more info.")
            kwargs.update({name: data})
            return func(*args, **kwargs)
        return inner
    return pass_arkmod_data
