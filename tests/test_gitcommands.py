import os
import pytest
import shutil

from arkmod.vcs import gitcommands

os.chdir(".\\test_environment")

@pytest.fixture()
def git_repo():
    if os.path.isdir(".git"):
        shutil.rmtree(".git")
    assert 1 == 0
    os.system("git init")
    print(os.listdir("."))
    assert 1 == 0

def test_git_add(git_reset):
    gitcommands.Add("test_gitcommands.py")
