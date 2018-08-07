import json
import os
import sys
import shutil
import maya.cmds as cmds
import maya.mel as mel
import playblasterUI as playblasterUI
import shotgun_api3 as sapi
from Framework.plugins.dependency_uploader.uploader_window import UploaderBackgroundWidget

def blast(*args):    
    
    review=False
    cam= cmds.modelPanel('blasterCam', q=True, cam=True)
    camShape= cmds.listRelatives(cam,s=True)[0]
    sceneSound = cmds.ls(typ='audio')
    startTime = cmds.intField('startFrame', v=True, q=True) 
    endTime = cmds.intField('endFrame', v=True, q=True)
    scale = playblasterUI.playblasterValues['scale']

    gPlayBackSlider = mel.eval('$temp=$gPlayBackSlider')
    if cmds.timeControl(gPlayBackSlider, query=True, rv=True):
        rangeSelected=cmds.timeControl(gPlayBackSlider, query=True, ra=True)
        startTime = int(rangeSelected[0])
        endTime = int(rangeSelected[1])

    if sceneSound and playblasterUI.playblasterValues['activateSound']:
        playblasterUI.playblasterValues['sound']= sceneSound[0]
    else:
        playblasterUI.playblasterValues['sound']= None
        
    wh= (cmds.getAttr('defaultResolution.width'),cmds.getAttr('defaultResolution.height'))
    displayValues = {'overscan':[1], 
                     'displayResolution':[0],
                     'displayGateMask':[0]}
                     
    #save the camDisplayValues into dictionary
    for value in displayValues:
        displayValues[value].append(cmds.getAttr(camShape + '.' + value))
        cmds.setAttr(camShape + '.' + value, displayValues[value][0])

    # comprobamos la opcion de guardado del playblast, si es version2 review forzamos que se sobreescriba el archivo
    if playblasterUI.playblasterValues['saveOption'] == 'version2Review':
        fileInfo = pipeInfo()
        review=True        
        #name = userConfirmDescriptionField(description=fileInfo['description'], fileType='version', prodState='chk')
        name = confirm(path=getPaths(description=fileInfo['description'], fileType='version', prodState='chk'))
        scale = 100
    
    else:
        name = confirm(playblasterUI.playblasterValues[playblasterUI.playblasterValues['saveOption']], incrementalOption=True)
    
    # obtenemos la ruta para comprobar si existe alguna version previa del playblast para dar la opcion de incrementalSave
    if not name and playblasterUI.playblasterValues['saveOption'] != 'temporaryPlayblast':
        cmds.warning('no video created')                
        return
    
    else:
        playblasterUI.playblasterValues['lastUserPlayblastPath'] = cmds.playblast(viewer=True, 
                                                                    format= 'qt', 
                                                                    clearCache= 1, 
                                                                    showOrnaments= playblasterUI.playblasterValues['showOrnaments'], 
                                                                    offScreen= playblasterUI.playblasterValues['offscreen'],  
                                                                    fp= 4, 
                                                                    percent= scale, 
                                                                    compression= "H.264", 
                                                                    quality= 100, 
                                                                    widthHeight = wh, 
                                                                    epn= 'blasterCam', 
                                                                    filename= name, 
                                                                    sound= playblasterUI.playblasterValues['sound'], 
                                                                    forceOverwrite= True,
                                                                    startTime = startTime,
                                                                    endTime= endTime)
        
    
    #restore the camDisplayValues
    for value in displayValues:
        cmds.setAttr(camShape + '.' + value, displayValues[value][1])

    staticValues = jsonPlayblaster()
    for staticValue in ('showOrnaments','scale','offscreen','lastUserPlayblastPath'):
        staticValues.modify(staticValue, playblasterUI.playblasterValues[staticValue])

    if review:
        sendToCheck(name)

def sendToCheck(filePath):

    userCheck = cmds.confirmDialog(db='ok', b= ['ok', 'cancel'], cb='cancel', t="Warning: ", m="it's about to send playblast and scene to review, \nThe scene will be saved, are you sure??")
    if userCheck == 'ok':
        fileInfo = pipeInfo()
        sceneFullName = fileInfo['folder'] + fileInfo['fileName'] + fileInfo['extension']   
        chkFullName = getPaths(description=fileInfo['description'], fileType='scene', prodState='chk')
 
        cmds.file(save=True)
        shutil.copy(sceneFullName, chkFullName)
        sendToDropbox([filePath, chkFullName],4)

    else:
        print 'no se ha enviado nada a review si quieres enviar algo relanza el playblast'
    
def playLast(*args):
    if playblasterUI.playblasterValues['lastUserPlayblastPath']:
        cmds.launch(movie=playblasterUI.playblasterValues['lastUserPlayblastPath'])        
    else:
        cmds.warning('there is no previous playblast')


def incrementalName(path,*args):
    '''esta funcion agrega la extension .000n al nombre del archivo
    '''
    fileName, file_extension = os.path.splitext(path)

    if os.path.splitext(fileName)[-1]:
        fileName, previousVersion = os.path.splitext(fileName)
        
        incremental = str(int(previousVersion[1:]) + 1).rjust(len(previousVersion[1:]), '0')
        
        return fileName + '.' + incremental + file_extension
        
    else:
        incremental= '0001'
        return fileName.split('.')[0] + '.' + incremental + file_extension


def hidePanelsMenu(panel):
    '''esa funcion oculta los menus de los model panels y deja solo la vista de camara
    '''
    panelBar = cmds.modelPanel(panel, q=True, barLayout=True)
    if panelBar:
        cmds.frameLayout(panelBar, edit=True, collapse=True)
        
def changeCameraView(*args):
    cmds.modelPanel('blasterCam',e=True, cam= cmds.optionMenu('camsMenu',q=True,v=True))
    

def customPathSelector(*args):
    '''refresca el valor de custom path del diccionario para guardar el video en disco en funcion de la eleccion de path por el usuario 
    '''
    try:
        playblasterUI.playblasterValues['custom'] = cmds.fileDialog2(fileFilter='*.mov', dialogStyle=1, caption='choose a directory to save the playblast', fileMode=0)[0]
    except:
        pass

    
def userCams():
    '''esta funcion filtra las camaras que no sean por defecto de maya
    devuelve una lista con los nombre de los transforms de las camaras creadas por el usuario
    esta pendiente que se muestren todas las camaras que hay en la escena, las camaras por defecto debajo de un separador
    '''
    allCameras = cmds.ls(typ='camera')
    userCameras = []
    defaultCameras = ('perspShape','topShape','sideShape','frontShape')
    
    for o in allCameras:
        if o not in defaultCameras:
            cameraTransform= cmds.listRelatives(o, p=True)[0]
            userCameras.append(cameraTransform)
    return userCameras       

def createMenuCams(*args):
    '''esta funcion recrea el los items del menu de camaras y marca como seleccionada la camara que este en el panel cada vez que se despliega el menu de seleccion de camaras
    '''
    defaultCameras = ('persp','top','side','front')
    playblasterUI.playblasterValues['cameras'] = []
    sceneCameras = userCams()
    cmds.menu('camerasMenu', e=True, dai=True) #se borra todo el menu desplegable de seleccion de camara 
    cmds.radioMenuItemCollection(p='camerasMenu') 
    #se recorre la lista de las camaras creadas por el usuario y se crea un item para el menu con cada una de ellas 
    if sceneCameras:
        cmds.menuItem(divider=True, dl='User Cameras',p='camerasMenu')
        for o in sceneCameras:
            if o.replace('Shape','') == cmds.modelPanel('blasterCam',q=True, cam=True):
                state = True
            else:
                state = False
                
            camara= cmds.menuItem(o, label=o.replace('Shape',''), p='camerasMenu', c= setCameraOnPanel, rb=state)
            if camara not in playblasterUI.playblasterValues['cameras']:
                playblasterUI.playblasterValues['cameras'].append(camara)
        
    cmds.menuItem(divider=True, dl='Default Cameras',p='camerasMenu')

    for i in defaultCameras:
        if i.replace('Shape','') == cmds.modelPanel('blasterCam',q=True, cam=True):
            state = True
        else:
            state = False
            
        camara= cmds.menuItem(i, label=i.replace('Shape',''), p='camerasMenu', c= setCameraOnPanel, rb=state)
        if camara not in playblasterUI.playblasterValues['cameras']:
            playblasterUI.playblasterValues['cameras'].append(camara)

    cmds.menuItem(divider=True,p='camerasMenu')
    cmds.menuItem('selectCamera', label='Select Camera', p='camerasMenu', c= "cmds.select(playblasterUI.playblasterValues['currentCamera'])")    
    cmds.menuItem('newCamera', label='New Camera', i='Camera.png', p='camerasMenu', c=newCamera)


def newCamera(*args):
    cameraName= cmds.camera(n="playblasterCam")
    cmds.rename(cameraName[-1],cameraName[0] + 'Shape')

def setCameraOnPanel(*args):
    for o in playblasterUI.playblasterValues['cameras']:
        if cmds.menuItem(o, q=True, rb=True):
            cameraItem= o.split('|')[-1]
            cmds.modelPanel('blasterCam',e=True, cam = cameraItem)
            playblasterUI.playblasterValues['currentCamera'] = cameraItem
            cmds.floatSlider('opacitySlider', e= True, v=1.0)

            cameraInitState()
        
def sceneRange(*args):
    '''esta funcion establece en el playblaster los valores de startFrame y endFrame en funcion del rangeSlider,
    estaria guay que si es un archivo de pipe hiciera una llamada a shotgun y preguntara por los rangos oficiales del plano
    '''
    min=cmds.playbackOptions(q=True,min=True)
    max=cmds.playbackOptions(q=True,max=True)
    shotgunRange = getShotgunRange()
    
    if shotgunRange:
       min=shotgunRange['start']
       max=shotgunRange['end']

    cmds.intField('startFrame', v=min, e=True) 
    cmds.intField('endFrame', v=max, e=True)
    
def getShotgunRange():

    sceneInfo = pipeInfo()
    shotRange = {}
    if sceneInfo:
        sg = sapi.Shotgun("https://esdip.shotgunstudio.com",
                                 login="tdevelopment",
                                 password="BM@Developement")
                                          
        shot=sceneInfo['seq'] + '.' + sceneInfo['shot']
        
        try:
            shotgunInfo = sg.find("Shot", filters=[["code", "is", shot],['project','is', {'type': 'Project','id': 86}]],
                                          fields=["sg_cut_in", "sg_cut_out"])[0]
            if shotgunInfo['sg_cut_in']:
                shotRange['start'] = int(shotgunInfo['sg_cut_in'])	
            if shotgunInfo['sg_cut_out']:
                shotRange['end'] = int(shotgunInfo['sg_cut_out'])
                
        except:
            return None
        
        return shotRange

def blasterPencil(*args):
    '''esta funcion activa el context de grease pencil
    '''
    cmds.setToolTo('greasePencilContext')
            
def greaseOff(*args):
    '''esta funcion desactiva el context de grease pencil y cierra su ventana
    '''
    if cmds.window('greasePencilFloatingWindow', exists=True):
        cmds.deleteUI('greasePencilFloatingWindow')    
    cmds.setToolTo('moveSuperContext')

def startFrameChange(*args):
    value = cmds.intField('startFrame', q=True, v=True)
    playblasterUI.playblasterValues['startFrame'] = value
    cmds.intField('endFrame', e=True, min= value)
    
def endFrameChange(*args):
    value = cmds.intField('endFrame', q=True, v=True)
    playblasterUI.playblasterValues['endFrame'] = value
    cmds.intField('startFrame', e=True, max= value)

def toogleRenderer(*args):
    if cmds.modelEditor('blasterCam', q=True, rendererName= True) == 'vp2Renderer':
        cmds.modelEditor('blasterCam',e=True, rendererName= 'base_OpenGL_Renderer')
        cmds.symbolButton('rendererCtr', image='hyper_s_OFF.png', e= True)
        
    else: 
        cmds.modelEditor('blasterCam',e=True, rendererName= 'vp2Renderer')
        cmds.symbolButton('rendererCtr', image='hyper_s_ON.png', e= True)
    
def cameraInitState():
    '''esta funcion actualiza el estado de los simbolCheckoxs del playblaster cuando cambia la camara en el panel,
    tambien refresca el valor de los sliders de opacidad y de offset en funcion de los valores del image plane
    '''
    playblasterUI.playblasterValues['camInitState'] = {'mask': cmds.getAttr(playblasterUI.playblasterValues['currentCamera'] + '.displayGateMask'),
                                         'antialiasing': cmds.getAttr("hardwareRenderingGlobals.multiSampleEnable"),
                                         'aOcclusion': cmds.getAttr("hardwareRenderingGlobals.ssaoEnable"),
                                         'locked': cmds.camera(playblasterUI.playblasterValues['currentCamera'], q=True, lockTransform=True),
                                         'zoomer': cmds.getAttr(playblasterUI.playblasterValues['currentCamera'] + '.panZoomEnabled')}
    
    cmds.symbolCheckBox('cameraMaskCtr', e=True, v= playblasterUI.playblasterValues['camInitState']['mask'])
    cmds.symbolCheckBox('sampleCtr', e=True, v= playblasterUI.playblasterValues['camInitState']['antialiasing'])
    cmds.symbolCheckBox('aOcclusionCtr', e=True, v= playblasterUI.playblasterValues['camInitState']['aOcclusion'])
    cmds.symbolCheckBox('lockCameraCtr', e=True, v= playblasterUI.playblasterValues['camInitState']['locked'])
    cmds.symbolCheckBox('panZoomCtr', e=True, v=playblasterUI.playblasterValues['camInitState']['zoomer'])    

    getIplaneInfo(playblasterUI.playblasterValues['currentCamera'])
            
    if playblasterUI.playblasterValues['currentIPlane']:
        #setear el valor en el slider de transparencia
        cmds.floatSlider('opacitySlider', e= True, en=True)
        cmds.optionMenu('sliderMode', e=True, en=True)
        changeSliderMode()
        
        if cmds.getAttr(playblasterUI.playblasterValues['currentIPlane'] + '.type') != 2 or 'playblaster' not in playblasterUI.playblasterValues['currentIPlane']:
            cmds.optionMenu('sliderMode', e=True, v='iPlane alpha')
            cmds.menuItem('playblasterOffsetOption', e=True, en=False)
            cmds.intField('IplaneStart', e= True, en=False)
        
        else:
            cmds.menuItem('playblasterOffsetOption',e=True, en=True)    
            cmds.intField('IplaneStart', e= True, en=True)
     
    else:  
        cmds.intField('IplaneStart', e= True, en=False)
        cmds.floatSlider('opacitySlider', e= True, en=False)
        cmds.optionMenu('sliderMode', e=True, en=False)


def resetZoomer(*args):
    '''esta funcion reestablece los valores por defecto de pan/zoom 2d de la camara
    '''
    cameraShape= cmds.listRelatives(playblasterUI.playblasterValues['currentCamera'], s=True)[0]

    cmds.setAttr(cameraShape + ".horizontalPan", 0)
    cmds.setAttr(cameraShape + ".verticalPan", 0)
    cmds.setAttr(cameraShape + ".zoom", 1)

def activeZoomPan(*args):
    cmds.setAttr(playblasterUI.playblasterValues['currentCamera'] + '.panZoomEnabled', 1)
    cmds.setToolTo('playblasterPanTool')
    cmds.symbolCheckBox('panZoomCtr', e=True, v=True)

def deactiveZoomPan(*args):
    cmds.setAttr(playblasterUI.playblasterValues['currentCamera'] + '.panZoomEnabled', 0)
    cmds.setToolTo('moveSuperContext')

def changeMovieStartFrame(*args):
    '''esta funcion modifica el frame en el que se muestra el fotograma 1 del video del imagePlane
    '''
    value= cmds.intField('IplaneStart', v= True, q=True)
    cmds.setAttr(playblasterUI.playblasterValues['frameChooser'] + '.input1D[1]', value -1)

def changeSliderValue(*args):
    '''esta funcion cambia la opacidad cuando se modifica el slider de opacidad, desactivando los undos sin borrar la cola para aislar la basura de acciones que genera
    '''
    option=cmds.optionMenu('sliderMode', q=True, v=True)
    attr={'iPlane alpha':'.alphaGain',
          'iPlane depth':'.depth',
          'iPlane offset':'.frameOffset'}

    value= cmds.floatSlider('opacitySlider', v= True, q=True)
    cmds.undoInfo(swf=False)
    cmds.setAttr(playblasterUI.playblasterValues['currentIPlane'] + attr[option], value)
    cmds.undoInfo(swf=True)

def changeSliderMode(*args):
    option = cmds.optionMenu('sliderMode', q=True, v=True)
    filePath = cmds.getAttr(playblasterUI.playblasterValues['currentIPlane']+ '.imageName')
    fileName, file_extension = os.path.splitext(filePath)
    movieType = ('.mov','.mp4')
    maxFrameOffset = 1

    if file_extension in movieType:
        maxFrameOffset=int(cmds.movieInfo(filePath, frameCount=True)[0])

    attr={'iPlane alpha':['.alphaGain',[0, 1]],
          'iPlane depth':['.depth',[0.15, 100]],
          'iPlane offset':['.frameOffset', [0, maxFrameOffset]]}

    valueAtChange= cmds.getAttr(playblasterUI.playblasterValues['currentIPlane'] + attr[option][0])      
    cmds.floatSlider('opacitySlider', min= attr[option][1][0], max= attr[option][1][1], v= valueAtChange, e=True)
    

def getIplaneInfo(currentCamera):
    '''actualiza el diccionario de los image planes que hay en la escena asiciandolos al transform de la camara que los contiene, y refresca el valor del iplane actual y el nodo frameChooser
    '''
    # empezamos obteniendo el nombre de la shape de la camara y los hijos que pueda tener, porque los image planes y los grease pencil quedan dentro de la shape
    camShape = cmds.listRelatives(currentCamera,s=True)[0]
    descents = cmds.listRelatives(camShape,ad=True)
    #generamos como valores vacios del diccionario el nombre del nodo framaChooser y el current Image Plane
    playblasterUI.playblasterValues['frameChooser']=None
    playblasterUI.playblasterValues['currentIPlane']=None
    
    if descents:
        for o in descents:
            if cmds.nodeType(o) == 'imagePlane':
                playblasterUI.playblasterValues['currentIPlane'] = cmds.listRelatives(o,p=True)[0]
                if cmds.getAttr(playblasterUI.playblasterValues['currentIPlane'] + '.type') == 2:
                    playblasterUI.playblasterValues['frameChooser'] = cmds.listConnections(o + '.frameExtension')[0]
            
            elif cmds.nodeType(o) == 'greasePlane':
                playblasterUI.playblasterValues['currentGreasePencil'] = cmds.listRelatives(o,p=True)[0]
                
    allImagePlanes = cmds.ls(typ='imagePlane')
    for o in allImagePlanes:
        cameraShape, iplaneShape = o.split('->')
        cameraTransform = cmds.listRelatives(cameraShape,p=True)[0]
        iplaneTransform = cmds.listRelatives(iplaneShape,p=True)[0] 
        if 'playblaster' in iplaneShape:
    
            playblasterUI.playblasterValues['imagesPlanes'][cameraTransform] = iplaneTransform


def iplane(file):
    getIplaneInfo(playblasterUI.playblasterValues['currentCamera'])
    fileName, file_extension = os.path.splitext(file)
    movieType= ('.mov','.mp4')
    iplane = cmds.imagePlane(n='playblasterImagePlane', camera = playblasterUI.playblasterValues['currentCamera'], lookThrough=playblasterUI.playblasterValues['currentCamera'], showInAllViews=False,nt=True)
    iplane[1]= cmds.rename(iplane[1],iplane[0] + 'Shape')        
    cmds.setAttr(iplane[1] + '.imageName', file, typ='string')
    cmds.setAttr(iplane[1] + '.depth', 0.15)
    cmds.setAttr(iplane[1] + '.fit', 1)        
    cmds.setAttr(iplane[1] + '.overrideEnabled', 1)
    cmds.setAttr(iplane[1] + '.overrideDisplayType', 2)                

    mel.eval('source AEimagePlaneTemplate.mel')
    mel.eval("AEinvokeFitRezGate" + (' {0} {1}').format(iplane[1]+'.sizeX', iplane[1]+'.sizeY'))        
    
    cmds.floatSlider('opacitySlider', e= True, en=True, v=1)
    cmds.optionMenu('sliderMode', e=True, en=True)

    playblasterUI.playblasterValues['imagesPlanes'][playblasterUI.playblasterValues['currentCamera']]=iplane[0]
    playblasterUI.playblasterValues['currentIPlane']= iplane[0]        

    if file_extension in movieType:
        firstFrameMinus = cmds.createNode('plusMinusAverage',n='playblasterChooserStartFrame_minus')
        cmds.setAttr(firstFrameMinus + '.operation', 2)
        cmds.connectAttr('time1.outTime',firstFrameMinus + '.input1D[0]')
        cmds.setAttr(firstFrameMinus + '.input1D[1]', cmds.intField('IplaneStart', v= True, q=True) - 1)
        cmds.connectAttr(firstFrameMinus + '.output1D', iplane[1] + '.frameExtension')
        cmds.setAttr(iplane[1] + '.type', 2)            
        cmds.setAttr(iplane[1] + '.useFrameExtension',lock=False)
        cmds.setAttr(iplane[1] + '.useFrameExtension', True)

        cmds.intField('IplaneStart', e= True, en=True, v= cmds.playbackOptions(q=True,min=True))
        
        playblasterUI.playblasterValues['frameChooser'] = firstFrameMinus
        changeMovieStartFrame()
        cmds.menuItem('playblasterOffsetOption', e=True, en=True)
    else:
        cmds.menuItem('playblasterOffsetOption', e=True, en=False)

    changeSliderMode()    


def setIPlane(*args):
    '''esta opcion inicia un fileDialog para explorar un archivo
    devuelve la ruta seleccionada por el usuario
    '''
    try:
        file= cmds.fileDialog2(fileFilter='*.mov *.mp4 *.jpg *.png', dialogStyle=1, caption='choose file to load', fileMode=1)[0]
        if file:
            if not playblasterUI.playblasterValues['currentIPlane']:
                iplane(file)
            else:
                deleteIplane()
                iplane(file)
    except:
        pass 


def defaultIplane(*args):
    '''esta funcion setea como iplane el ultimo playblast generado
    '''    
    if playblasterUI.playblasterValues['lastUserPlayblastPath']:
        if not playblasterUI.playblasterValues['currentIPlane']:
            iplane(playblasterUI.playblasterValues['lastUserPlayblastPath'])
        else:
            deleteIplane()
            iplane(playblasterUI.playblasterValues['lastUserPlayblastPath'])        
    else:
        cmds.warning('there is no recent playblast, please choose a videoFile to load')

def deleteIplane(*args):
    '''esta funcion elimina el iplane de la camara y desactiva los sliders de control de offset y transparencia
    tambien elimina de la variable global playblasterValues el item correspondiente a la camara que esta en ese momento en el playblaster
    '''
    if playblasterUI.playblasterValues['currentIPlane']:
        if 'playblaster' not in playblasterUI.playblasterValues['currentIPlane']:
            userCheck = cmds.confirmDialog(db='ok', b= ('ok','cancel'), cb='cancel', m='this iPlane was not created with the tool, \n do you want to delete it?')
            
            if userCheck != 'ok':
                return
        else:
            del playblasterUI.playblasterValues['imagesPlanes'][playblasterUI.playblasterValues['currentCamera']]
                       
        cmds.delete(playblasterUI.playblasterValues['currentIPlane'])
        cmds.intField('IplaneStart', e= True, en=False)
        cmds.floatSlider('opacitySlider', e= True, en=False, v=0)
        cmds.optionMenu('sliderMode', e=True, en=False)        
        playblasterUI.playblasterValues['currentIPlane']=None


def deleteGreasePencil(*args):
    '''esta funcion elimina el greasePencil de la camara y desactiva los sliders de control de offset y transparencia
    '''    
    greasePencilTransform = None
    camShape = cmds.listRelatives(playblasterUI.playblasterValues['currentCamera'],s=True)[0]
    descents = cmds.listRelatives(camShape,ad=True)
    
    if descents:
        for o in descents:
            if cmds.nodeType(o)== 'greasePlane':
                greasePencilTransform = cmds.listRelatives(o,p=True)[0]
        if greasePencilTransform:
            cmds.delete(greasePencilTransform)
                
def playOnly(*args):
    #start playback only on playblaster panel
    cmds.setFocus('blasterCam')
    
    cmds.playbackOptions(v="active")
    cmds.play( forward=True ) #start

def stop(*args):
    #stop playback and return to update all views
    cmds.play( state=False ) 
    cmds.playbackOptions(v="all")

def pipeInfo(path=None):
    '''chekea que el archivo este en pipe y pertenezca a alguno de los projectos.
    si no se pasa un path se basa en el nombre de la escena actual, en caso contrario analiza el path pasado
    si esta en pipe devuelve un dic con los datos de la escena(seq, numero de plano, departamento, descripcion, version y estado)
    si no devuelve None
    '''
    pipePathExample=('bm2_shoani_seq_tst_sho_620_animation_charsWalking_scene_wip.ma')
    if not path:
        longName=cmds.file(sn=True, q=True)
        fileName, file_extension = os.path.splitext(cmds.file(sn=True, shn=True, q=True))
    else:
        longName=path
        fileName, file_extension = os.path.splitext(path.split('/')[-1])

    splitedName=fileName.split("_")
    prodFields={'version':None}
    
    if longName and len(splitedName) == len(pipePathExample.split('_')):

        if len(splitedName[-1].split('.')) > 1:
            prodFields['version']=splitedName[-1].split('.')[-1]
            prodFields['state']=splitedName[-1].split('.')[0]
            prodFields['fileName']=fileName.replace(prodFields['version']+'.','')
        else:
            prodFields['state']=splitedName[-1]
            prodFields['fileName']=fileName
                    
        prodFields['project']=splitedName[0]
        prodFields['seq']=splitedName[3]
        prodFields['shot']=splitedName[5]
        prodFields['department']=splitedName[-4]
        prodFields['description']=splitedName[-3]
        prodFields['extension']=file_extension
        prodFields['folder']=longName.replace(fileName + file_extension,'')
        
        return prodFields

    else:
        return None 

def getPaths(fileType, description=None, prodState='out'):
    '''esta funcion devuelve la ruta completa de salida de archivos en funcion del parametro prodution State, deberia ser 'out' o 'chk',
    completa la ruta con el campo description por si se quisiera modificar para cada cache por ejemplo
    y el argumento fileType va a definir la extension del archivo
    '''

    fileInformation = pipeInfo()
    extensions={'version':'.mov','scene':'.ma','abc':'.abc'}
        
    if not description:
        description=fileInformation['description']

    longName = cmds.file(sn=True, q=True)
    sceneUbication = longName[:-len(longName.split('/')[-1])]

    cacheName = fileInformation['project'] + '_shoani_seq_' + fileInformation['seq'] + '_sho_' + fileInformation['shot'] + '_' + fileInformation['department'] + '_' + description + '_' + fileType + '_' + prodState + extensions[fileType]    
    outFolder = sceneUbication.replace(sceneUbication.split('/')[-2], prodState)
    outName = outFolder + cacheName

    return outName

def sendToDropbox(file_path_list,max_threads):
    '''por revisar, esta funcion en teoria deberia subir los archivos a dropbox
    '''
    uploader_background_widget = UploaderBackgroundWidget(file_path_list=file_path_list,
                                                          max_threads=max_threads)

    uploader_background_widget.show()
    uploader_background_widget.execute_upload_process()


def confirm(path=None, incrementalOption=False, message=None):
    ''' esta funcion comprueba si existe el archivo en disco y si es asi muestra un dilogo para que escoja si se quiere sobreescribir,
    en ese caso devuelve el mismo path que se le paso, en caso de que decida incrementar una version, devuelve el nombre del archivo + la extension .000n en funcion de que existan o no versiones del mismo
    si el usuario cancela la operacion devuelve None
    '''
    if not incrementalOption:
        options=['ok', 'cancel']
    else:
        options=['no, incremental save', 'ok', 'cancel']

    if not message:
        message= 'Oops, seems the file already exist, do you want to overwrite it?'
    
    if path: 
        if not os.path.isfile(path):
            return path
        else:
            userCheck = cmds.confirmDialog(db='ok', b= options, cb='cancel',t='Warning: file exist', m=message)
            if userCheck == 'cancel':
                return None
            elif userCheck == 'ok':
                return path
            else:
                #hacer un bucle while aqui para que le sume 1 hasta que no haya ningun archivo que se llame asi y separarlo en otra funcion
                while os.path.isfile(path): 
                    path=incrementalName(path)
                return path
    else:
        return None


def preOpenShowMenu(*args):
    staticValues=jsonPlayblaster().read()
    cmds.menuItem('curvesVis', cb= staticValues['nurbsCurves'], e=True)
    cmds.menuItem('locatorsVis', cb= staticValues['locators'], e=True)
    cmds.menuItem('manipulatorsVis', cb= staticValues['manipulators'], e=True)
    cmds.menuItem('lightsOnVis', cb= staticValues['lightsOn'], e=True)
    cmds.menuItem('shadowsVis', cb= staticValues['shadows'], e=True)
    cmds.menuItem('iPlaneVis', cb= staticValues['imagePlane'], e=True)
    cmds.menuItem('greaseVis', cb= staticValues['greasePencils'], e=True)
    cmds.menuItem('motionTrailsVis', cb= staticValues['motionTrails'], e=True)

def toogleMask(*args):
    if cmds.getAttr(playblasterUI.playblasterValues['currentCamera'] + '.displayGateMask'):
        cmds.setAttr(playblasterUI.playblasterValues['currentCamera'] + '.displayGateMask', 0)
        cmds.setAttr(playblasterUI.playblasterValues['currentCamera'] + '.displayResolution', 0)
    else:
        cmds.setAttr(playblasterUI.playblasterValues['currentCamera'] + '.displayResolution', 1) 
        cmds.setAttr(playblasterUI.playblasterValues['currentCamera'] + '.displayGateMask', 1)

def toogleShaded(*args):
    if cmds.modelEditor('blasterCam', q=True, displayAppearance= True) == 'smoothShaded':
        cmds.modelEditor('blasterCam',e=True, displayAppearance= 'wireframe')
        cmds.symbolButton('shadedCtr', image='WireFrame.png', e= True)
        cmds.modelEditor('blasterCam',e=True, wos= 0)
        cmds.symbolCheckBox('wireframeShadedCtr', v= 0, e=True)

    else: 
        cmds.modelEditor('blasterCam',e=True, displayAppearance= 'smoothShaded')
        cmds.symbolButton('shadedCtr', image='Shaded.png', e= True)
        cmds.modelEditor('blasterCam',e=True, wos= 0)
        cmds.symbolCheckBox('wireframeShadedCtr', v= 0, e=True)

def toogleLightsOn(*args):
    staticValues = jsonPlayblaster()
    if cmds.modelEditor('blasterCam', q=True, displayLights = True) == 'default':
        cmds.modelEditor('blasterCam', e=True, displayLights = 'all')
        staticValues.modify('lightsOn', True)
        staticValues.modify('displayLights','all')

    else:
        cmds.modelEditor('blasterCam', e=True, displayLights = 'default')
        staticValues.modify('lightsOn', False)
        staticValues.modify('displayLights','default')

def toogleShadows(*args):
    staticValues = jsonPlayblaster()
    if cmds.modelEditor('blasterCam', q=True, shadows = True):
        cmds.modelEditor('blasterCam', e=True, shadows = False)
        staticValues.modify('shadows', False)
    else:
        cmds.modelEditor('blasterCam', e=True, shadows = True)
        staticValues.modify('shadows', True)

def toogleNurbsCurves(*args):
    staticValues = jsonPlayblaster()
    if cmds.modelEditor('blasterCam', q=True, nurbsCurves = True):
        cmds.modelEditor('blasterCam', e=True, nurbsCurves = False)
        staticValues.modify('nurbsCurves', False)
    else:
        cmds.modelEditor('blasterCam', e=True, nurbsCurves = True)
        staticValues.modify('nurbsCurves', True) 

def toogleLocators(*args):
    staticValues = jsonPlayblaster()
    if cmds.modelEditor('blasterCam', q=True, locators = True):
        cmds.modelEditor('blasterCam', e=True, locators = False)
        staticValues.modify('locators', False)
    else:
        cmds.modelEditor('blasterCam', e=True, locators = True)
        staticValues.modify('locators', True)                 

def toogleManipulators(*args):
    staticValues = jsonPlayblaster()
    if cmds.modelEditor('blasterCam', q=True, manipulators = True):
        cmds.modelEditor('blasterCam', e=True, manipulators = False)
        staticValues.modify('manipulators', False)
    else:
        cmds.modelEditor('blasterCam', e=True, manipulators = True)
        staticValues.modify('manipulators', True) 

def toogleImagePlanes(*args):
    staticValues = jsonPlayblaster()
    if cmds.modelEditor('blasterCam', q=True, imagePlane = True):
        cmds.modelEditor('blasterCam', e=True, imagePlane = False)
        staticValues.modify('imagePlane', False)
    else:
        cmds.modelEditor('blasterCam', e=True, imagePlane = True)
        staticValues.modify('imagePlane', True) 

def toogleGreasePencils(*args):
    staticValues = jsonPlayblaster()
    if cmds.modelEditor('blasterCam', q=True, greasePencils = True):
        cmds.modelEditor('blasterCam', e=True, greasePencils = False)
        staticValues.modify('greasePencils', False)
    else:
        cmds.modelEditor('blasterCam', e=True, greasePencils = True)
        staticValues.modify('greasePencils', True) 

def toogleMotionTrails(*args):
    staticValues = jsonPlayblaster()
    if cmds.modelEditor('blasterCam', q=True, motionTrails = True):
        cmds.modelEditor('blasterCam', e=True, motionTrails = False)
        staticValues.modify('motionTrails', False)
    else:
        cmds.modelEditor('blasterCam', e=True, motionTrails = True)
        staticValues.modify('motionTrails', True)                 

def wireFrameOnShaded(*args):
        cmds.modelEditor('blasterCam',e=True, wos= 1)
        cmds.modelEditor('blasterCam',e=True, displayAppearance= 'smoothShaded')
        cmds.symbolButton('shadedCtr', image='Shaded.png', e= True)

def toogleAppereance(*args):
    if cmds.modelEditor('blasterCam', q=True, udm= True):
        cmds.modelEditor('blasterCam',e=True, udm= False)
        cmds.symbolButton('texturedCtr', image='Textured.png', e= True)
    else: 
        cmds.modelEditor('blasterCam',e=True, udm= True)
        cmds.symbolButton('texturedCtr', image='UseDefaultMaterial.png', e= True)



class jsonEditor(object):
    def __init__(self,file_path):
        self.file_path = file_path

    def read(self):
        if not os.path.isfile(self.file_path):
            raise Exception("Not file Found on the system: %s"%self.file_path)
        with open(self.file_path) as f:
            d = json.load(f)
            return d

    def save(self,content):
        if os.path.exists(os.path.dirname(self.file_path)) != True:
            os.makedirs(os.path.dirname(self.file_path))           
        with open(self.file_path, 'w') as outFile:
            json.dump(content, outFile, indent=4, sort_keys=True)

    def modify(self,index,newValue):
        json=self.read()
        json[index]=newValue
        self.save(json)



class jsonPlayblaster(jsonEditor):
    def __init__(self):
        self.file_path= os.path.dirname(playblasterUI.__file__)+'/playblasterValues.json'


'''
esta funcion y la clase que genera un prompt de eleccion no se va a usar finalmente para que siempre se fuerze el pisado de versiones
y no va a tener el usuario posibilidad de cambiar el campo partition

def userConfirmDescriptionField(description=None, fileType='version', prodState='chk'):
    
    path=getPaths(fileType=fileType, description=description, prodState= prodState)
    
    if not os.path.isfile(path):
        return path
    
    else:
        userDescriptionCheck = modifyDescriptionPrompt(description,fileType).showPrompt().replace(' ','')
        
        if userDescriptionCheck == 'ok':
            return path
        elif userDescriptionCheck == 'dismiss':
            return None
        else:
            newPath = getPaths(description=userDescriptionCheck, fileType=fileType, prodState= prodState)
            newDescription = userDescriptionCheck

            while os.path.isfile(newPath):
                newDescription=modifyDescriptionPrompt(newDescription,fileType).showPrompt().replace(' ','')
                    
                if newDescription == 'dismiss':
                    return None
                elif newDescription == 'ok':
                    return newPath
                else:    
                    newPath=getPaths(description=newDescription, fileType=fileType, prodState= prodState)    
        
            return newPath


class modifyDescriptionPrompt(object):
    def __init__(self,existedDescription,fileType):

        self.existedDescription=existedDescription
        self.fileType=fileType
        
    def uiPrompt(self):
        # Get the dialog's formLayout.
        #
        form = cmds.setParent(q=True)
    
        # layoutDialog's are not resizable, so hard code a size here,
        # to make sure all UI elements are visible.
        #
        cmds.formLayout(form, e=True, width=300)
    
        t = cmds.text(l='This file already exist please modify desription field')
        t1=cmds.textFieldGrp( label=self.fileType + ' description:', text= self.existedDescription, editable=False,adj=2,cw=(2,50))
        t2=cmds.textFieldGrp('newDescription', label='rename description to:', text=self.existedDescription,adj=2,cw=(2,50))
        lay=cmds.rowLayout(numberOfColumns=3,adj=2)
        #separatore=cmds.separator(p=lay,st='none')
        b1=cmds.button(l='modify', c="cmds.layoutDialog( dismiss=cmds.textFieldGrp('newDescription',q=True,tx=True))",p=lay)
        #separatore=cmds.separator(p=lay,st='none')
        b2=cmds.button(l='overwrite', c="cmds.layoutDialog( dismiss='ok' )",p=lay)
        #separatore=cmds.separator(p=lay,st='none')
        b3=cmds.button(l='cancel', c="cmds.layoutDialog( dismiss='dismiss' )",p=lay)
        #separatore=cmds.separator(p=lay,st='none')
        
        spacer = 5
        top = 5
        edge = 5
    
        cmds.formLayout(form, edit=True,
                        attachForm=[(t, 'top', top), (t, 'left', edge), (t, 'right', edge), (t1, 'left', edge), (t2, 'left', edge), (t1, 'right', edge), (t2, 'right', edge), (lay, 'left', edge), (lay, 'right', edge),(lay, 'bottom', edge)],
                        attachControl=[(t1, 'top', spacer, t), (t2, 'top', spacer, t1), (lay, 'top', spacer, t2)],
                        attachPosition=[(lay, 'left', spacer, 33), (lay, 'right', spacer, 33)])

    def showPrompt(self):
        answer = cmds.layoutDialog(ui=self.uiPrompt)
        return answer 



'''