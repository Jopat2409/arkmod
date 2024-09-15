import os
import stat
import click
import shutil

from . import gitcommands
from .gitinfo import GitInfo
from .arkconfig import ArkModConfig, pass_arkmod_data
from ..console import log_error, log_info
from .gittransaction import GitTransaction


def __cleanup_git():
    """Remove git repository from the current working directory
    """

    # Change file permissions from readonly so the delete can happen (Thanks stackoverflow)
    if os.path.isdir('.git'):
        for root, dirs, files in os.walk(".git"):
            for dir in dirs:
                os.chmod(os.path.join(root, dir), stat.S_IRWXU)
            for file in files:
                os.chmod(os.path.join(root, file), stat.S_IRWXU)
        shutil.rmtree('.git')

def __init_existing(mod_db: str):
    """Initialise arkmod into an already existing git repository.

    Creates an orphan branch to base the arkmod vcs off of and creates necessary config files
    """

    # Fail if git is not initialised
    if not GitInfo.is_git_init():
        log_error("Git must already be initialised when using the --use-existing flag. See arkmod init --help for more info.")
        return

    # Ensure all changes stick, or none
    with GitTransaction() as transaction:
        # Create empty branch to base mod off (arkmod-master)
        if not transaction.execute(gitcommands.CreateBranch("arkmod_master", from_=None)):
            return log_error("Cannot create orphan branch to initialise arkmod in.")
        # Update config to refled renamed master branch

        if not transaction.execute(gitcommands.CreateFile('.arkmod')):
            return log_error("Could not create arkmod config file.")

        ArkModConfig.init_configfile(db=mod_db, base_branch="arkmod_master", from_existing_git=True)

        if not transaction.execute(gitcommands.Add(('.arkmod',))):
            return log_error("Could not add .arkmod config to version control. Reverting all changes.")
        if not transaction.execute(gitcommands.Commit(('.arkmod',), "Initial Commit")):
            return log_error("Could not commit .arkmod to version control. Reverting all changes.")

        transaction.set_success()

@click.command()
@click.option("--mod-db", '-db',
                default="..\\..\\Saved\\Mods.db",
                help="The path to the Mods.db file within your ark mod/devkit")
@click.option("--use-existing", '-ue',
                is_flag = True,
                help="Set to initialise arkmod into an existing git repository.")
def init(use_existing: bool,
            mod_db: str):
    """Initialise the arkmod version control in the current working directory. Bear in mind that this command should
    almost always be called in your ShooterGame/Content/Mods directory.
    """

    # Fail if git is not installed
    if not GitInfo.is_git_installed():
        return log_error("Git must be installed on your local machine in order to use arkmod version control.")

    if not os.path.isfile(mod_db):
        return log_error("Mods.db file could not be automatically found. Please specify the path using --mod-db. See arkmod init --help for more info")

    if use_existing:
        return __init_existing(mod_db)

    # Fail if git is already initialised and --use-existing is not set
    if GitInfo.is_git_init():
        return log_error("Git is already initialised in this repository. See arkmod init --help for more info.")

    # Fail if git cannot be initialised
    if not gitcommands.InitGit().execute():
        return log_error("Git could not be initialised on your machine.")


    with GitTransaction(onfail=__cleanup_git) as transaction:
        # Update config to refled renamed master branch
        ArkModConfig.init_configfile(db=mod_db)

        if not transaction.execute(gitcommands.Add(('.arkmod',))):
            return log_error("Could not add .arkmod config to version control. Reverting all changes.")
        if not transaction.execute(gitcommands.Commit(('.arkmod',), "Initial Commit")):
            return log_error("Could not commit .arkmod to version control. Reverting all changes.")

        transaction.set_success()

@click.command()
def list_mods():
    """List the mods that have been created / registered to arkmod version control
    """
    current_arkmod_data = ArkModConfig.load_configfile()
    if not current_arkmod_data:
        return log_error("You must initialise arkmod using 'arkmod init' before using the arkmod vcs interface. See arkmod --help for more info.")
    click.echo('\n'.join(current_arkmod_data["mods"].keys()))

@click.command()
def current_mod():
    """List the current mod that is being worked on
    """
    click.echo('Editing : ' + GitInfo.get_current_branch())

@click.command("create-mod")
@click.argument("name")
@click.option("--mod-directory", '-d',
                default="",
                help="Directory the mod should be created in. If not specified, the mod name will be used.")
@click.option("--remote", '-r',
                default="",
                help="Remote origin to assign to the mod being created")
@click.option("--remote-branch", '-rb',
                default="main",
                help="The branch on the remote repository that this mod should be pushed to")
@click.option("--no-copy", '-xc',
                is_flag = True,
                help="Do not copy over the default mod files.")
@click.option("--no-readme", '-xr',
                is_flag = True,
                help="Do not include the default README.md that is created with every mod.")
@pass_arkmod_data()
def create_mod(name: str,
                mod_directory: str,
                remote: str,
                remote_branch: str,
                no_copy: bool,
                no_readme: bool,
                arkmod_data: dict):

    mod_dir = mod_directory or name.replace(' ', '_')

    # Ensure the mod does not already exist:
    if name in arkmod_data["mods"]:
        return log_error(f"{name} is already a mod. See 'arkmod register-mod --help' to use vcs for a mod not created with this tool.")

    # Ensure the mod directory does not already exist
    rel_path = os.path.join("Mods", mod_dir)
    if os.path.isdir(rel_path):
        return log_error(f"{rel_path} is already a directory. See 'arkmod register-mod --help' to use vcs for a mod not created with this tool.")

    def cleanup():
        if os.path.isdir(rel_path):
            shutil.rmtree(rel_path)

    with GitTransaction(auto_rollback = True, onfail=cleanup) as transaction:

        # Create new git local branch
        if not transaction.execute(gitcommands.CreateBranch(mod_dir, from_=arkmod_data["config"]["git-base"])):
            return log_error(f"Error creating branch for mod {name}. Please see 'arkmod create-mod --help' for more information")

        # Add remote if specified
        if remote:
            if not transaction.execute(gitcommands.CreateRemote(f"origin_{mod_dir}", remote)):
                return log_error(f"Error creating remote origin for mod {name}. Ensure that your git URL is valid and try again.")
            if not transaction.execute(gitcommands.SetBranchRemote(mod_dir, f"origin_{mod_dir}", remote_branch)):
                return log_error(f"Could not set remote branch for mod {name}. Ensure that the local and remote branch names are accurate then try again.")

        os.mkdir(rel_path)

        # Copy default mod files over to new mod
        to_add = []
        if not no_copy:
            for file in arkmod_data["config"]["copyfiles"]:
                new_name = arkmod_data["config"]["copyfiles"][file].replace('<ArkMod:ModName>', mod_dir)
                shutil.copyfile(file, new_name)
                to_add.append(new_name)

            if not transaction.execute(gitcommands.Add(to_add)):
                return log_error(f"Could not track file {new_name} for mod {name}")

            if not transaction.execute(gitcommands.Commit(to_add, "Initial Commit")):
                return log_error(f"Could not commit file {new_name} for mod {name}")

        log_info("Created necessary files")

        arkmod_data["mods"].update({name: {
            "directory": mod_dir,
            "local-branch": mod_dir,
            "remote-origin": f"origin_{name}" if remote else "",
            "stable-release": None,
            "next-release": {}
        }})
        arkmod_data["config"]["current-mod"] = name
        ArkModConfig.save_configfile(arkmod_data)
        #ModDatabase(current_arkmod_data["config"]["mod-db"]).create_mod(name, mod_dir, default_maps=[file.split('.')[0] for file in to_add if file.endswith('umap')] if not no_copy else [])

        transaction.set_success()

    log_info("Created new mod")


@click.command("edit-mod")
@click.argument("mod")
@pass_arkmod_data()
def edit_mod(mod: str,
                arkmod_data: dict):

    # Checkout mod git branch
    if not gitcommands.CheckoutBranch(arkmod_data["mods"][mod]["local-branch"]).execute():
        return log_error(f"{mod} is not a valid mod. See arkmod create-mod --help for more info.")
    arkmod_data["config"]["current-mod"] = mod
    ArkModConfig.save_configfile(arkmod_data)

@click.command("create-release")
@click.argument("name")
@click.option('--manual-version', '-v',
                default="",
                help="Manually specifies the version in the form x.x.x")
def create_release(name: str,
                    manual_version: str,
                    arkmod_data: dict):
    """Create a new release for the mod you are working on.

    NAME is the name of the release. This should be a brief description of what will be included in the release and can be
    changed later.
    """

    if not arkmod_data:
        return log_error("You must initialise arkmod using 'arkmod init' before creating any releases. See arkmod --help for more info.")

    current_mod = arkmod_data["config"]["current-mod"]
    mod_branch = arkmod_data["mods"][current_mod]["local-branch"]
    mod_version = manual_version or arkmod_data["mods"][current_mod]["next-release"]

    if mod_version in arkmod_data["mods"][current_mod]["releases"]:
        return log_error(f"There is already an active release version with the tag {mod_version}")

    # Create new branch for the release
    if not gitcommands.CreateBranch(f"{mod_branch}-release-{mod_version}", from_=mod_branch).execute():
        return log_error(f"Could not create new branch for release {mod_version}")

    log_info("Created branch")


@click.command("set-remote")
@click.argument("mod")
@click.argument("remote-url")
@click.option("--remote-branch", '-rb',
                default="main")
@pass_arkmod_data()
def set_remote(mod: str,
                remote_url: str,
                remote_branch: str,
                arkmod_data: dict) -> None:

    # Create remote and set it on local branch
    with GitTransaction(auto_rollback=True) as transaction:
        if not transaction.execute(gitcommands.CreateRemote(f"origin_{mod}", remote_url)):
            return log_error(f"Could not create remote origin_{mod} at {remote_url}")
        if not transaction.execute(gitcommands.SetBranchRemote(mod, f"origin_{mod}", remote_branch)):
            return log_error(f"Could not set remote as origin_{mod}/{remote_branch}")

        transaction.set_success()

    # Update mod data in config file
    arkmod_data["mods"][mod]["remote-origin"] = f"origin_{mod}"
    ArkModConfig.save_configfile(arkmod_data)


def __detach_discard():
    gitcommands.CheckoutBranch(ArkModConfig.load_configfile()["config"]["git-base"])

@click.command("detach")
@click.option("--flatten-to",
                default="",
                help="Optional name of branch to flatten all mods created using arkmod to.")
@click.option("--discard-all",
                is_flag = True,
                help="Discard all mods created using arkmod")
@click.option("--no-confirm",
                is_flag = True,
                help="Disable the confirmation warning when using arkmod detach. ONLY use when testing. Detaching arkmod WILL remove all your created mods unless the command is used properly")
def detach(flatten_to: str,
            discard_all: bool,
            no_confirm: bool):
    if not no_confirm and click.prompt("Are you sure you want to detach arkmod from your version control? Type DETACH_ARKMOD if you are sure.") != "DETACH_ARKMOD":
        return

    if discard_all:
        return __detach_discard()


