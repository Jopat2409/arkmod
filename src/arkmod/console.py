import click
import subprocess

def log_error(err_msg: str) -> None:
    """Logs an error to the console, coloured in red

    Parameters
    ----------
    err_msg : str
        The message to log to the console
    """
    click.echo(f"\033[91m[Error]: {err_msg}\033[0;37;40m\033[0m")

def log_info(info_msg) -> str:
    click.echo(f"[Info]: {info_msg}")

def run_command(cmd):
    subprocess.Popen( cmd, shell=True )

def run_command_fetch_output(cmd) -> tuple[str, str]:
    output, err = tuple(map(lambda x: x.decode('utf-8').strip(), subprocess.Popen( cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True ).communicate()))
    output_split = output.split('\n')
    log_info(f"Running command '{cmd}', Output: {output_split}" + f", Err: '{err}'"*bool(err))
    return output, err

def git_cmd_was_successful(cmd_output: str) -> bool:
    success = not cmd_output[1].startswith("error") and not cmd_output[1].startswith("fatal")
    if not success:
        log_error(cmd_output[1])
    return success
