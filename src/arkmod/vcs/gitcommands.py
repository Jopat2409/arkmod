import os
import shutil

from .gitinfo import GitInfo
from ..console import run_command_fetch_output, git_cmd_was_successful, log_info

class Command:
    """A command is a piece of code which changes the active repository in some way, that contains code for executing
    and rolling back the effects of its execution.
    """

    def execute(self) -> None:
        raise NotImplementedError("Must implement execute")

    def rollback(self) -> None:
        raise NotImplementedError("Must implement rollback")


class CheckoutBranch(Command):

    def __init__(self, branch: str):
        self.branch = branch

    def execute(self) -> bool:
        """Switches the current git instance to the given branch

        Returns
        -------
        bool
            `True` if the command was successful else `False`
        """

        if (current_branch := GitInfo.get_current_branch()) is None:
            return False

        self.current_branch = current_branch
        output = run_command_fetch_output(f"git checkout {self.branch}")

        return git_cmd_was_successful(output)

    def rollback(self) -> None:
        run_command_fetch_output(f"git checkout {self.current_branch}")

class InitGit(Command):

    def execute(self) -> bool:
        return git_cmd_was_successful(run_command_fetch_output('git init'))

    def rollback(self) -> None:
        shutil.rmtree(".git")

class CreateBranch(Command):

    def __init__(self, branch_name: str, from_: str | None = "master"):
        self.branch_name = branch_name
        self.from_ = from_

    def execute(self) -> bool:
        if self.from_ is None:
            output = run_command_fetch_output(f"git switch --orphan {self.branch_name}")
        else:
            output = run_command_fetch_output(f'git checkout -b {self.branch_name} {self.from_}')
        return git_cmd_was_successful(output)

    def rollback(self) -> None:
        run_command_fetch_output(f'git branch -d {self.branch_name}')

class Add(Command):

    def __init__(self, files: tuple[str]) -> None:
        self.files = ' '.join(files)

    def execute(self) -> bool:
        output = run_command_fetch_output(f"git add {self.files}")
        return git_cmd_was_successful(output)

    def rollback(self) -> None:
        run_command_fetch_output(f"git rm {self.files}")

class Commit(Command):

    def __init__(self, files: str, msg: str) -> None:
        self.files = ' '.join(files)
        self.msg = msg

    def execute(self) -> bool:
        cmd = f'git commit {self.files} -m "{self.msg}"'
        output = run_command_fetch_output(cmd)

        if (commit_hash := GitInfo.get_current_commit_hash()) is None:
            return False

        self.commit_hash = commit_hash
        return git_cmd_was_successful(output)

    def rollback(self) -> None:
        run_command_fetch_output(f"git revert --strategy resolve {self.commit_hash}")

class CreateRemote(Command):

    def __init__(self, name: str, url: str) -> bool:
        self.remote_name = name
        self.remote_url = url

    def execute(self) -> bool:
        output = run_command_fetch_output(f"""git remote add "{self.remote_name}" {self.remote_url}""")
        return git_cmd_was_successful(output)

    def rollback(self) -> None:
        run_command_fetch_output(f"git remote remove {self.remote_name}")

class SetBranchRemote(Command):

    def __init__(self, local_branch: str, remote_name: str, remote_branch: str):
        self.local_branch = local_branch
        self.remote_name = remote_name
        self.remote_branch = remote_branch

    def execute(self) -> bool:
        output = run_command_fetch_output(f"git branch --set-upstream-to {self.remote_name}/{self.remote_branch} {self.local_branch}")

        return git_cmd_was_successful(output)

    def rollback(self) -> None:
        run_command_fetch_output(f"git branch --unset-upstream {self.local_branch}")

class CreateFile(Command):

    def __init__(self, filepath: str) -> None:
        self.filepath = filepath

    def execute(self) -> bool:

        try:
            with open(self.filepath, 'x'):
                return True
        except:
            return False

    def rollback(self) -> None:
        os.remote(self.filepath)

class CopyFile(Command):

    def __init__(self, from_: str, to: str) -> None:
        self.from_ = from_
        self.to = to

    def execute(self) -> bool:
        try:
            shutil.copyfile(self.from_, self.to)
            return True
        except:
            return False

    def rollback(self) -> None:
        os.remove(self.to)
