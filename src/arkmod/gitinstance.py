import subprocess

from .console import log_error
import gitcommands

def run_command_fetch_output(cmd):
    return subprocess.Popen( cmd, stdout=subprocess.PIPE ).communicate()[0].decode('utf-8').strip()

class GitInstance:

    current_branch = "master"

    class Transaction:

        def __enter__(self, auto_rollback: bool = False):
            self.transaction_success = False
            self.auto_rollback = auto_rollback
            self.rollback_methods: list[gitcommands.GitCommand] = []
            return self

        def __exit__(self):
            if not GitInstance.success:
                GitInstance.void_transaction()

        def execute(self, cmd: gitcommands.GitCommand) -> None:
            if (x := cmd.execute()):
                self.rollback_methods.append(cmd)
            elif self.auto_rollback:
                self.void_transaction()
            return x

        def void_transaction(self) -> None:
            count = len(self.rollback_methods)
            for i in range(count):
                self.rollback_methods.pop(-i).rollback()
            log_error(f"Rolled back {count} git transactions due to critical failure.")

        def set_success(self) -> None:
            self.transaction_success = True

    @staticmethod
    def init() -> bool:
        run_command_fetch_output('git init')

    def is_file_tracked(file: str) -> bool:
        return not run_command_fetch_output(f"git ls-files --error-unmatch {file}").startswith("error")

    @staticmethod
    def is_git_installed() -> bool:
        return run_command_fetch_output('git --version') != "'git' is not recognized as an internal or external command, operable program or batch file."
