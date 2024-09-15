import os

from ..console import run_command_fetch_output, git_cmd_was_successful

class GitInfo:
    """Contains helper functions that return information about the current git instance. \n
    Note that no functions exposed by this interface will edit or change the current git repository in any way.
    """

    @staticmethod
    def get_current_branch() -> str | None:
        """Gets the name of the current git branch that is active

        Returns
        -------
        str | None
            The git branch that is active, or `None` if the command fails
        """
        output = run_command_fetch_output("git rev-parse --abbrev-ref HEAD")
        return output[0] if git_cmd_was_successful(output) else None

    @staticmethod
    def get_current_commit_hash() -> str | None:
        """Gets the shortened commit hash of the current HEAD

        Returns
        -------
        str | None
            Hash of the HEAD of the current active branch, or `None` if the command fails
        """
        output = run_command_fetch_output("git rev-parse --short HEAD")
        return output[0] if git_cmd_was_successful(output) else None

    @staticmethod
    def is_git_installed() -> bool:
        """Checks if git is installed on the local system

        Returns
        -------
        bool
            `True` if git is installed, else `False`
        """
        return run_command_fetch_output("git --version")[0].startswith("git version")

    @staticmethod
    def is_git_init() -> bool:
        """Checks if the current working directory has already been initialised as a git repository

        Determines this through the presence of a `.git` directory

        Returns
        -------
        bool
            `True` if git is initialised in this directory else `False`
        """
        return os.path.isdir(".git")

    @staticmethod
    def is_file_tracked(file: str) -> bool:
        return not run_command_fetch_output(f"git ls-files --error-unmatch {file}").startswith("error")
