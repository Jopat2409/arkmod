from . import gitcommands

from ..console import log_error


class GitTransaction:

    def __init__(self, auto_rollback: bool = False, onfail: callable = lambda : 0) -> None:
        """Provides a context manager for git commands, ensuring that each command that is completed successfully
        is rolled back upon exit of the context manager unless the success flag is set.

        Parameters
        ----------
        auto_rollback : bool, optional
            If auto_rollback is set, then the rollback will be done the moment a transaction fails instead of on exit of the context manager, by default False
        onfail : _type_, optional
            An additional cleanup function to call on rollback of all the executed commands, by default lambda:0
        """

        self.auto_rollback = auto_rollback
        self.run_on_fail = onfail
        self.success = False

    def __enter__(self):
        self.rollback_methods: list[gitcommands.Command] = []
        return self

    def __exit__(self, type, value, traceback):
        if not self.success:
            self.void_transaction()

    def execute(self, cmd: gitcommands.Command) -> None:
        # If command succeeds, add it to rollback queue, else roll the transaction back
        if (x := cmd.execute()):
            self.rollback_methods.append(cmd)
        elif self.auto_rollback:
            self.void_transaction()
        return x

    def void_transaction(self) -> None:
        count = len(self.rollback_methods)
        if count == 0:
            return
        for i in range(count):
            self.rollback_methods.pop(-i).rollback()
        self.run_on_fail()
        log_error(f"Rolled back {count} git transactions due to critical failure.")

    def set_success(self) -> None:
        self.success = True
