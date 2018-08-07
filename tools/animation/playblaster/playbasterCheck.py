import maya.cmds as cmds
import playblasterUI as playblasterUI
import os


def checkWindowAtStartMaya():
    if cmds.panel('blasterCam', exists=True) or cmds.workspaceControl('playblaster', exists=True):
        global playblasterValues
        playblasterValues = playblasterUI.playblasterUI()
        return playblasterValues



