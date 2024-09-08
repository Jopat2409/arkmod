import subprocess

def run_command_fetch_output(cmd):
    return subprocess.Popen( cmd, stdout=subprocess.PIPE ).communicate()[0].decode('utf-8').strip()

class GitCommand:

    def __init__(self) -> None:
        pass

    def execute(self) -> None:
        raise NotImplementedError("Must implement execute")

    def rollback(self) -> None:
        raise NotImplementedError("Must implement rollback")


class SwitchBranch(GitCommand):

    def __init__(self, branch: str):
        self.branch = branch

    def execute(self) -> bool:
        self.current_branch = run_command_fetch_output("git rev-parse --abbrev-ref HEAD")
        success = run_command_fetch_output(f"git checkout {self.branch}") != f"error: pathspec '{self.branch}' did not match any file(s) known to git"
        return success

    def rollback(self) -> None:
        run_command_fetch_output(f"git checkout {self.current_branch}")

class CreateBranch(GitCommand):

    def __init__(self, branch_name: str, from_ = "master"):
        self.branch_name = branch_name
        self.from_ = from_

    def execute(self) -> bool:
        output = run_command_fetch_output(f'git checkout -b {self.branch_name} {self.from_}')
        return not output.startswith("fatal")

    def rollback(self) -> None:
        run_command_fetch_output(f'git branch -d {self.branch_name}')

class Add(GitCommand):

    def __init__(self, path: str) -> None:
        self.path = path

    def execute(self) -> bool:
        success = run_command_fetch_output(f"git add {self.path}") != f"fatal: pathspec '{self.path}' did not match any files"
        return success

    def rollback(self) -> None:
        run_command_fetch_output(f"git rm {self.path}")

class Commit(GitCommand):

    def __init__(self, path: str, msg: str) -> None:
        self.path = path
        self.msg = msg

    def execute(self) -> bool:
        output = run_command_fetch_output(f"git commit {self.path} -m {self.msg}")
        self.commit_hash = run_command_fetch_output("git rev-parse --short HEAD")

        return not output.startswith("error") and not output.startswith("fatal")

    def rollback(self) -> None:
        run_command_fetch_output(f"git revert --strategy resolve {self.commit_hash}")

class CreateRemote(GitCommand):

    def __init__(self, name: str, url: str) -> bool:
        self.remote_name = name
        self.remote_url = url

    def execute(self) -> bool:
        run_command_fetch_output(f"""git remote add "{self.remote_name}" {self.remote_url}""")
        return True

    def rollback(self) -> None:
        run_command_fetch_output(f"git remote remove {self.remote_name}")

class SetBranchRemote(GitCommand):

    def __init__(self, local_branch: str, remote_name: str, remote_branch: str):
        self.local_branch = local_branch
        self.remote_name = remote_name
        self.remote_branch = remote_branch

    def execute(self) -> bool:
        output = run_command_fetch_output(f"git branch --set-upstream-to {self.remote_name}/{self.remote_branch} {self.local_branch}")

        return not output.startswith("error") and not output.startswith("fatal")

    def rollback(self) -> None:
        run_command_fetch_output(f"git branch --unset-upstream {self.local_branch}")
