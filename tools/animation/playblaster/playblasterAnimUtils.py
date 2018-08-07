import maya.cmds as cmds
import maya.mel as mel
import playblasterUI
import os


def changeRotateOrder(newRotateOrder, *args):
    keyInRange(atributes='rotate')
    cmds.refresh(suspend=True)
    selection = cmds.ls(sl=True)
    if selection:
        scriptPath = (os.path.dirname(playblasterUI.__file__)+ '/zooChangeRoo.mel').replace('\\','/')
        scriptUtilsPath = (os.path.dirname(playblasterUI.__file__)+ '/zooUtils.mel').replace('\\','/')
        mel.eval('source "%s"' % scriptPath)
        mel.eval('source "%s"' % scriptUtilsPath)
        mel.eval("zooChangeRoo " + newRotateOrder)
        mel.eval('performEulerFilter graphEditor1FromOutliner')
    else:
        cmds.warning('there is no object selected')
    cmds.refresh(suspend=False)         


def keyInRange(atributes='all',*args):
    cmds.refresh(suspend=True)
    start=cmds.playbackOptions(q=True, min=True)
    end=cmds.playbackOptions(q=True, max=True)

    selection = cmds.ls(sl=True)
    if selection:

        keysInFrames=cmds.keyframe(selection, time=(start,end), query=True)
        simplifiedList=[]

        for o in keysInFrames:
            if o not in simplifiedList:
                simplifiedList.append(o)

        simplifiedList.sort()

        for o in range(len(simplifiedList)):
            cmds.currentTime(cmds.findKeyframe(timeSlider=True, which="next"), edit=True)
            if atributes == 'all':
                cmds.setKeyframe()
            else:
                cmds.setKeyframe(at=atributes)

    else:
        cmds.warning('there is no object selected')

    cmds.refresh(suspend=False)        


def stepTangents(*args):
    selection=cmds.ls(sl=True)
    if selection:
        cmds.selectKey() 
    else:
        cmds.warning('there is no object selected but new keys will be in stepped')
    cmds.keyTangent(itt='linear', ott='step')
    cmds.keyTangent(g=True, itt='linear', ott= 'step')


def autoTangents(*args):
    selection=cmds.ls(sl=True)
    if selection:
        cmds.selectKey()
    else:
        cmds.warning('there is no object selected but new keys will be in auto')
    cmds.keyTangent(itt='auto', ott= 'auto')
    cmds.keyTangent(g=True, itt='auto', ott= 'auto')


def intermediateAndConstraint(*args):
    selection= cmds.ls(sl=True)
    if len(selection) == 2:
        slave= selection[-1]
        master= selection[0]
        #first create a locator and offset it:
        locator= cmds.spaceLocator(n='intermediate_' + slave)[0]
        offset= cmds.group(locator,n=locator+'_offset')
        #align the offset with the slave
        cmds.delete(cmds.parentConstraint(slave,offset, mo=False))
        #constraint the slave with the intermediate object
        cmds.parentConstraint(locator,slave, mo=False)
        cmds.parentConstraint(master,offset, mo=True)

    else:
        cmds.warning('please select first master and then slave to create and intermediate object and constraint with it')
