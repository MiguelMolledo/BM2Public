import os
import sys
import shutil 
import maya.cmds as cmds
import BM2Public.tools.animation.playblaster.playblasterFunctions as playblasterFunctions
import abcExporterUI as abcExporterUI 


def abcWriter(startFrame,endFrame,description,flags=('uvWrite', 'worldSpace', 'writeVisibility', 'writeUVSets')):
    '''esta funcion 
    '''
    outName=playblasterFunctions.confirm(path=playblasterFunctions.getPaths(description=description, fileType='abc', prodState='out'), message= 'Ooops, seems there is previous cache for ' + description.capitalize() + '.\nDo you want to overwrite it?')
    
    if outName:
        if os.path.exists(os.path.dirname(outName)) != True:
            os.makedirs(os.path.dirname(outName)) 

        stringFlags=' -' + ' -'.join(flags)

        command = "-frameRange "+ str(startFrame) + " " + str(endFrame) + stringFlags + ' -root ' + description + ':geo' + " -file " + outName

        cacheFile = cmds.AbcExport(j=command)
        cacheDescription=playblasterFunctions.pipeInfo(outName)

        return outName, cacheDescription['description']
    
    else:
        return None

def keysAtStart(char):
    ctl = cmds.ls(char + ':*ctl*', char + ':poses_1', typ='transform')
    firstFrame = cmds.findKeyframe(ctl, time=(25,25), which="next")
    for o in ctl:
        cmds.setKeyframe(o, t=firstFrame, rk=True, i=True)


def zeroAtZero(char):
    controls = cmds.ls(char + ':*ctl*', char + ':poses_1', typ='transform')
    for ctl in controls:
        atributes=cmds.listAttr(ctl, k=True)
        for attr in atributes: 
            defaultValue = cmds.attributeQuery(attr, ld=True, n=ctl)[0]
            cmds.setKeyframe(ctl, t=1, at=attr, v=defaultValue)


def rootElems(filterBy,selected=False):
    elems={'chars':[],'props':[]}
    for o in cmds.ls(filterBy, sl=selected):
        if 'mortando' not in o:
            if 'gato' not in o:
                elems['props'].append(o.split(':')[0])
            else:
                elems['chars'].append(o.split(':')[0])
        else:
            elems['chars'].append(o.split(':')[0])
    return elems


def setInList(objType):

    elemList = rootElems('*:rig')[objType]
    cmds.textScrollList(objType + 'List', ra=True, e=True)
    for each in elemList:
        cmds.textScrollList(objType + 'List',append=each, e=True)


def addSelectedElem(objType):
    elemList=clasifySelected()[objType]
    if elemList:
        for each in elemList:
            listItems=cmds.textScrollList(objType + 'List', ai=True, q=True)
            if listItems: 
                if each not in listItems:
                    cmds.textScrollList(objType + 'List', append=each, e=True)
            else:
                cmds.textScrollList(objType + 'List',append=each, e=True)


def removeFromList(listType):
    selection=cmds.textScrollList(listType, si=True, q=True)
    if selection:
        for each in selection:
            cmds.textScrollList(listType, ri=each, e=True)

def elemsLister(*args):
    objects = rootElems('*:rig')    
    return objects

def clasifySelected(*args):
    objects = rootElems('*:*', selected=True)
    return objects

def setPropsInList(*args):
    setInList('props')
    
def setCharsInList(*args):
    setInList('chars')

def addSelectedProps(*args):
    addSelectedElem('props')

def addSelectedChars(*args):
    addSelectedElem('chars')

def removeChar(*args):
    removeFromList('charsList')

def removeProp(*args):
    removeFromList('propsList')

def refreshUI(*args):
    sceneInfo=playblasterFunctions.pipeInfo()
    refreshCachesInDiskWindow()
    if not sceneInfo:
        cmds.textField('projectField',tx='', e=True, en=False)
        cmds.textField('seqField',tx='', e=True, en=False)
        cmds.textField('shotField',tx='', e=True, en=False)
        cmds.textScrollList('charsList',ra=True, e=True, en=False)
        cmds.textScrollList('propsList',ra=True, e=True, en=False)
        cmds.button('doAbcs', en=False, e=True)
    else:
        cmds.textField('projectField',tx=sceneInfo['project'], e=True)
        cmds.textField('seqField',tx=sceneInfo['seq'], e=True)
        cmds.textField('shotField',tx=sceneInfo['shot'], e=True)
        cmds.textScrollList('charsList', e=True, en=True)
        cmds.textScrollList('propsList', e=True, en=True)
        setCharsInList()
        setPropsInList()
        cmds.button('doAbcs', en=True, e=True)


def doTheCaches(*args):
    cmds.refresh(suspend=True)
    shotgunRange = playblasterFunctions.getShotgunRange()
    if shotgunRange:
        endFrame = shotgunRange['end'] + 15
    else:
        endFrame = cmds.playbackOptions(q=True,max=True)

    propList=cmds.textScrollList('propsList', ai=True, q=True)
    charList=cmds.textScrollList('charsList', ai=True, q=True)

    exportedList=[]

    if propList:
        for elem in propList:
            startFrame = 85
            cacheExported=abcWriter(startFrame, endFrame, elem)
            if cacheExported:
                exportedList.append(cacheExported[1])
    if charList: 
        for char in charList:
            startFrame = 1
            keysAtStart(char)
            zeroAtZero(char)
            cmds.setAttr(char + ':fatmesh.visibility', 0)
            cacheExported = abcWriter(startFrame, endFrame, char)
            if cacheExported:
                exportedList.append(cacheExported[1])
                cmds.setAttr(char + ':fatmesh.visibility', 1)

    refreshCachesInDiskWindow()
    
    if exportedList:    
        cmds.tabLayout('tabsLayout', e=True, sti=2)

    cmds.refresh(suspend=False)
  

def importCacheToScene(*args):
    cachesFiles=readCachesInDisk()
    selection = cmds.textScrollList('cachesExportedList', q=True, si=True)
    if selection:
        for o in selection:
            cmds.file(cachesFiles[o], i=True, type="Alembic", ignoreVersion=True, mergeNamespacesOnClash= False, namespace= o+'Exported', pr= True)


def removeCachesInScene():
    cachesToClean=[x for x in cmds.namespaceInfo(lon=True) if 'Exported' in x]
    for cache in cachesToClean:
        cmds.namespace( dnc=True,rm=cache)

def publishSelectedCaches(*args):
    cachesdict=readCachesInDisk()
    filestoQueu=[]
    selection = cmds.textScrollList('cachesExportedList', q=True, si=True)
    if selection:
        for o in selection:
            filestoQueu.append(cachesdict[o])

    userChoice = cmds.confirmDialog(db='ok', b= ['ok', 'cancel'], cb='cancel', t="Warning:", m=" it's about to publish this caches: " + ', '.join(selection) + ", \nare you sure??")
    if userChoice == 'ok':
        removeCachesInScene()
        cmds.file(save=True)
        fileInfo = playblasterFunctions.pipeInfo() 
        sceneFullName = fileInfo['folder'] + fileInfo['fileName'] + fileInfo['extension']    
        outFullName = playblasterFunctions.getPaths(description=fileInfo['description'], fileType='scene', prodState='out')  
        shutil.copy(sceneFullName, outFullName) 
        filestoQueu.append(outFullName)
        playblasterFunctions.sendToDropbox(filestoQueu,4)
        

def refreshCachesInDiskWindow():
    if cmds.textScrollList('cachesExportedList', ex=True):
        cmds.textScrollList('cachesExportedList', e=True, ra=True)
        if playblasterFunctions.pipeInfo():
            cachesDescription=[]
            for o in readCachesInDisk():
                cachesDescription.append(o)
            
            cmds.textScrollList('cachesExportedList', e=True, ra=True)
            cmds.textScrollList('cachesExportedList', e=True, a=cachesDescription)
            cmds.button('publishCachesButton', e=True, en=True)
            cmds.button('importCachesButton', e=True, en=True)

        else:
            cmds.button('publishCachesButton', e=True, en=False)
            cmds.button('importCachesButton', e=True, en=False)    

def readCachesInDisk():
    path=playblasterFunctions.pipeInfo()['folder'].replace('wip','out')
    cacheFiles={}

    for o in os.listdir(path):
        info=playblasterFunctions.pipeInfo(o)
        if info:
            if info['extension']=='.abc':
                cacheFiles[info['description']]=path + info['fileName'] + info['extension']

    return cacheFiles