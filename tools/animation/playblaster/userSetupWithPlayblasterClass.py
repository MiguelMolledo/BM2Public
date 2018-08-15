import sys
import os

sys.path.append(r"C:/Python27/Lib/site-packages")
sys.path.append(r"P:/TOOLS")

import git
import maya.cmds as cmds
import BM2Public.tools.animation.playblaster.playblasterClass as playblasterUI
#import BM2Public.tools.animation.playblaster.playbasterCheckClass as check
import BM2Public.tools.animation.playblaster.playblasterAnimUtils as playblasterAnimUtils

    
if not cmds.about(batch=True):
    # launch playblaster lastState
    cmds.evalDeferred('playblasterWindow=playblasterUI.playblaster(); playblasterWindow.checkWindowAtStartMaya()',lowestPriority=True)

    # launch aTools_Animation_Bar
    cmds.evalDeferred("from BM2Public.tools.animation.aTools.animTools.animBar import animBarUI; animBarUI.show('launch')")



os.environ["GIT_PYTHON_GIT_EXECUTABLE"] = "P:/Deployment/Git/bin/git.exe"
os.environ['GIT_SSL_NO_VERIFY'] = "1"

PRODUCTION_REPO = "https://github.com/MayaFramework/Framework.git"
REPO_DIR = "P:/TOOLS/Framework"



def is_git_repo(path):
    try:
        _ = git.Repo(path).git_dir
        return True
    except git.exc.InvalidGitRepositoryError:
        return False



def clone_repo(git_url, repo_dir, branch="master"):
    try:
        git.Repo.clone_from(git_url, repo_dir, branch=branch)
        return True
    except:
        return False


def pull_latest_changes(repo_dir):
    repo = git.Repo(repo_dir)
    o = repo.remotes.origin
    o.pull()


if not is_git_repo(REPO_DIR):
    clone_repo(PRODUCTION_REPO, REPO_DIR, branch="bm2_production")
    print ("Finished Clone process")
else:
    pull_latest_changes(REPO_DIR)
    print ("Finished Clone process")


