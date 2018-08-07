'''to do:
-posibilidad de hacer mas de un image plane y seleccionar cual quieres que te muestre
-que publique lo videos en su carpeta de dropbox
-que haga una copia de la escena en su sitio chk
'''

import maya.cmds as cmds
import playblasterFunctions as functions
import playblasterAnimUtils as playblasterAnimUtils
import BM2Public.tools.abcExporter.abcExporterUI as abcExporter
import BM2Public.tools.abcExporter.abcExporterFunctions as abcExporterFunctions


def checkWorkspace():
    if cmds.panel('blasterCam', exists=True) and cmds.workspaceControl('playblaster', exists=True):
        cmds.workspaceControl('playblaster', restore=True, e=True)

        return True 

def checkJob():
    sesionJobs=cmds.scriptJob(lj=True)
    jobExist=False
    for job in sesionJobs:
        if 'refreshPlayblasterWindow()' in job:
            jobExist=True
            break
    if not jobExist:
        cmds.scriptJob(e=('PreFileNewOrOpened','playblasterUI.refreshPlayblasterWindow()'),permanent=True)

def refreshPlayblasterWindow():
    fileInformation = functions.pipeInfo()

    if cmds.modelPanel('blasterCam', q=True, ex=True):
        cmds.modelPanel('blasterCam', e=True, mbv=False)
        playblasterValues['currentCamera'] = cmds.modelPanel('blasterCam', q=True, cam=True)
        functions.cameraInitState()        
        functions.sceneRange()
        
        if fileInformation and fileInformation['department'] == 'animation':
            cmds.radioButton('version2Review', e=True, en=True, vis=True) 
            cmds.menu('caches', e=True, en=True, vis=True)
            cmds.button('setToSceneRange', l='Set Shotgun Range', e=True)

        else :
            cmds.radioButton('version2Review', e=True, en=False, vis=False)
            cmds.radioButton('temporaryPlayblast', e=True, sl=True)
            playblasterValues['saveOption']='temporaryPlayblast'
            cmds.menu('caches', e=True, en=False, vis=False)
            cmds.button('setToSceneRange', l='Set Scene Range', e=True)

    if cmds.window('abcExporter', exists=True):
        abcExporterFunctions.refreshUI()

        


def playblasterUI(*args):
    '''esta funcion genera la ui
    empezamos definiendo las variables globales que tendra la ventana y que modificara, 
    tengo que pensar en guardar en un json externo mejor que como variable global al menos settings como lastUserPlayblastPath, temporaryPlayblast,proyectPath, format, scale, showOrnaments, activateSound, y offscreen
    ''' 
    staticValues=functions.jsonPlayblaster().read()

    if not 'playblasterValues' in globals():
        global playblasterValues
        playblasterValues={'custom':'',
                           'version2Review':'',
                           'lastUserPlayblastPath':staticValues['lastUserPlayblastPath'],
                           'temporaryPlayblast':None,
                           'sound':None,
                           'activateSound':True,
                           'format':'qt',
                           'showOrnaments':staticValues['showOrnaments'],
                           'offscreen':staticValues['offscreen'],
                           'scale':staticValues['scale'],
                           'cameras':None,
                           'currentCamera':'persp',
                           'pencil':None,
                           'imagesPlanes':{},
                           'currentIPlane':None,
                           'currentGreasePencil':None,
                           'frameChooser':None,
                           'saveOption':'temporaryPlayblast',
                           }


    playblasterValues['startFrame'] = cmds.playbackOptions(q=True,min=True)
    playblasterValues['endFrame'] = cmds.playbackOptions(q=True,max=True)
    
    #listamos las camaras en escena filtrando las camaras por defecto de maya y cogemos la primera para setearla como camara inicial, 
    if functions.userCams():
        playblasterValues['currentCamera'] = functions.userCams()[0]  

    #si existe la ventana el panelview o el workspaceControl lo eliminamos
    if checkWorkspace():
        return playblasterValues

    if not cmds.workspaceControl('playblaster', exists=True):
        blastWindow = cmds.workspaceControl('playblaster', label="playblaster", 
                                         uiScript='playblasterUI', 
                                         initialWidth=355, 
                                         initialHeight=720,
                                         wp='free',
                                         loadImmediately=False,
                                         hp='free',
                                         rt=False,
                                         )
    else:
        blastWindow='playblaster'
    
    #menu de opciones de la ventana, en funcion son 4 menus que van a permitir cambiar las opciones de formato 
    menuLayout = cmds.menuBarLayout('playblasterMenuLayout',p=blastWindow)
    camsMenu = cmds.menu('camerasMenu',label='Cameras',p= menuLayout, pmc= functions.createMenuCams)
    windowMenu = cmds.menu('playblasterMenu',label='Playblast Options',p= menuLayout)

    cmds.menuItem('playblasterScaleOptions', label='Scale', sm=True)
    cmds.radioMenuItemCollection()
    cmds.menuItem('playblasterScale_50', label='50', rb=False,c="playblasterValues['scale']=50")
    cmds.menuItem('playblasterScale_70', label='70', rb=False,c="playblasterValues['scale']=70")
    cmds.menuItem('playblasterScale_100', label='100', rb=False,c="playblasterValues['scale']=100")
    cmds.setParent( '..', menu=True)

    cmds.menuItem( divider=True )
    cmds.menuItem('playblasterShowornamentsOption', label='Show ornaments', cb=playblasterValues['showOrnaments'], c="playblasterValues['showOrnaments']=cmds.menuItem('playblasterShowornamentsOption',q=True,cb=True)" )
    cmds.menuItem('playblasterSoundOption', label='Sound activate', cb= True, c="playblasterValues['activateSound']=cmds.menuItem('playblasterSoundOption',q=True,cb=True)" )
    cmds.menuItem('playblasterOffscreenOption', label='offscreen', cb=playblasterValues['offscreen'],c="playblasterValues['offscreen']=cmds.menuItem('playblasterOffscreenOption',q=True,cb=True)" )
    
    showMenu = cmds.menu('showMenu',label='Show',p= menuLayout, pmc= functions.preOpenShowMenu)
    cmds.menuItem('curvesVis',label='nurbs curves', cb= staticValues['nurbsCurves'], c= functions.toogleNurbsCurves)
    cmds.menuItem('locatorsVis',label='locators', cb= staticValues['locators'], c= functions.toogleLocators)
    cmds.menuItem('motionTrailsVis',label='motion trails', cb=staticValues['motionTrails'], c= functions.toogleMotionTrails)
    cmds.menuItem(divider=True, dl='lights')    

    cmds.menuItem('lightsOnVis',label='lights on', cb=staticValues['lightsOn'], c= functions.toogleLightsOn)
    cmds.menuItem('shadowsVis',label='shadows', cb=staticValues['shadows'], c= functions.toogleShadows)
    cmds.menuItem(divider=True, dl='2D planes')    

    cmds.menuItem('iPlaneVis',label='images planes', cb=staticValues['imagePlane'], c= functions.toogleImagePlanes)
    cmds.menuItem('greaseVis',label='grease pencil', cb=staticValues['greasePencils'], c= functions.toogleGreasePencils)
    cmds.menuItem(divider=True)    

    cmds.menuItem('manipulatorsVis',label='manipulators', cb=staticValues['manipulators'], c= functions.toogleManipulators)

    utilsMenu = cmds.menu('utilsMenu',label='Utils',p= menuLayout, to=True)
    cmds.menuItem(divider=True, dl='Anim Utils')        
    cmds.menuItem(label='step curves', image='stepTangent.png', c=playblasterAnimUtils.stepTangents)
    cmds.menuItem(label='auto tangents', image='autoTangent.png', c=playblasterAnimUtils.autoTangents)
    cmds.menuItem(label='keys selected in range', image='setKeyframe.png', c=playblasterAnimUtils.keyInRange)
    cmds.menuItem(label='change rotate order', image='out_holder.png', sm=True)
    cmds.radioMenuItemCollection()
    
    cmds.menuItem(label='XYZ', c="playblasterAnimUtils.changeRotateOrder('xyz')")
    cmds.menuItem(label='YZX', c="playblasterAnimUtils.changeRotateOrder('yzx')")
    cmds.menuItem(label='ZXY', c="playblasterAnimUtils.changeRotateOrder('zxy')")
    cmds.menuItem(label='XZY', c="playblasterAnimUtils.changeRotateOrder('xzy')")
    cmds.menuItem(label='YXZ', c="playblasterAnimUtils.changeRotateOrder('yzx')")
    cmds.menuItem(label='ZYX', c="playblasterAnimUtils.changeRotateOrder('zyx')")
    cmds.setParent( '..', menu=True)    

    cmds.menuItem(divider=True, dl='Constraints')    
    cmds.menuItem(label='intermediate and constraint', image='interactiveBindTool.png', c=playblasterAnimUtils.intermediateAndConstraint)
    cmds.menuItem(label='parent constraint', image='parentConstraint.png', c='cmds.parentConstraint(mo=True)')    
    cmds.menuItem(ob=True, c=cmds.ParentConstraintOptions)

    cachesMenu = cmds.menu('caches',label='Caches',p= menuLayout)  
    cmds.menuItem('exportUi', label='export window',c=abcExporter.abcExporterUI)
    
    mainLayout = cmds.formLayout('formLayout')
    panelViewLayout = cmds.frameLayout(h=300, lv=0, p=mainLayout,bv=True)
    
    if cmds.panel('blasterCam', exists=True):
        cmds.deleteUI('blasterCam', pnl=True)

    camPanel = cmds.modelPanel('blasterCam', l='blasterCam', mbv=False, init=False, needsInit=False, p=panelViewLayout)

    cmds.modelPanel('blasterCam',e=True, cam=playblasterValues['currentCamera'])
    cmds.modelEditor('blasterCam',e=True,
                     cameras=False,
                     manipulators=staticValues['manipulators'],
                     grid=False,
                     headsUpDisplay=False,
                     joints=False,
                     ikHandles=False,
                     lights=False,                     
                     locators= staticValues['locators'],
                     nurbsCurves= staticValues['nurbsCurves'],
                     motionTrails= staticValues['motionTrails'],
                     textures=False,
                     displayAppearance='smoothShaded',
                     rendererName='vp2Renderer',
                     displayTextures=True,
                     hud=False,
                     sel=False,
                     shadows= staticValues['shadows'],
                     imagePlane= staticValues['imagePlane'],
                     greasePencils= staticValues['greasePencils'],
                     displayLights = staticValues['displayLights'])

    #escondemos los menus tipicos del panel view por defecto y setamos la camara inicial 
    functions.hidePanelsMenu(camPanel)

    #empezamos con los botones de la ventana
    topLayout = cmds.columnLayout(adj=True,p=mainLayout)
    cmds.separator(w= 50, hr=True, p=topLayout,style='single')

    buttonLayout = cmds.rowLayout(h=35, numberOfColumns=21, p= topLayout, adj=8)
    
    cmds.symbolCheckBox(h=35,image='paintFXtoNurbs.png',p=buttonLayout, en= True, onc=functions.blasterPencil, ofc=functions.greaseOff)
    cmds.symbolButton(h=35,image='deleteActive.png',p=buttonLayout, en= True, c=functions.deleteGreasePencil)

    cmds.symbolButton(h=20,image='closeBar.png',p=buttonLayout, en= False)                             
    cmds.symbolButton('loadVideo',h=35,image='fluidCacheCreate.png',p=buttonLayout, en= True, c=functions.setIPlane)
    cmds.symbolButton(h=35,image='fluidCacheDelete.png',p=buttonLayout, en= True, c=functions.deleteIplane)
    cmds.popupMenu('videoRefPath', parent='loadVideo', numberOfItems=1)
    cmds.radioCollection(p='videoRefPath')
    cmds.menuItem('videoSelector', label='load last playblast as reference', p='videoRefPath',c=functions.defaultIplane)
    cmds.text( label='1st Frame')
    cmds.intField('IplaneStart', w=50, p=buttonLayout, v= cmds.playbackOptions(q=True,min=True),en=False, cc=functions.changeMovieStartFrame)
    
    cmds.separator(w= 10,hr=True, p=buttonLayout,style='none')
    cmds.symbolButton('shadedCtr',w=20,h=20,image='Shaded.png', p=buttonLayout, en= True, c= functions.toogleShaded)
    cmds.symbolCheckBox('wireframeShadedCtr',w=20,h=20,image='WireFrameOnShaded.png', p=buttonLayout, en= True, onc=functions.wireFrameOnShaded, ofc='cmds.modelEditor("blasterCam",e=True, wos= 0)')
    cmds.symbolCheckBox('cameraMaskCtr',w=20,h=20,image='ResolutionGate.png', p=buttonLayout, cc=functions.toogleMask, en= True)  

    cmds.symbolButton(h=20,image='closeBar.png',p=buttonLayout, en= False)    
    cmds.symbolButton('rendererCtr',w=25,h=25,image='hyper_s_ON.png', p=buttonLayout, en= True, c= functions.toogleRenderer)
    cmds.symbolButton('texturedCtr',w=20,h=20,image='Textured.png', p=buttonLayout, en= True, ebg=False, c= functions.toogleAppereance)    
    cmds.symbolCheckBox('sampleCtr',w=20,h=20,image='MultisampleAA.png', p=buttonLayout, en= True, onc='cmds.setAttr("hardwareRenderingGlobals.multiSampleEnable", 1)',ofc='cmds.setAttr("hardwareRenderingGlobals.multiSampleEnable", 0)')
    cmds.symbolCheckBox('aOcclusionCtr',w=20,h=20,image='SSAO.png', p=buttonLayout, en= True, onc='cmds.setAttr("hardwareRenderingGlobals.ssaoEnable", 1)',ofc='cmds.setAttr("hardwareRenderingGlobals.ssaoEnable", 0)')

    #botones con las opciones de camara(bloquear la camara y manipular el zoom y paneo 2D)
    cmds.symbolButton(h=20,image='closeBar.png',p=buttonLayout, en= False)    
    cmds.symbolCheckBox('lockCameraCtr', w=20, h=20, image='CameraLock.png', p=buttonLayout, en= True, onc="cmds.camera(playblasterValues['currentCamera'], e=True, lockTransform=True)",ofc="cmds.camera(playblasterUI.playblasterValues['currentCamera'], e=True, lockTransform=False)")
    cmds.symbolCheckBox('panZoomCtr', w=20, h=20, image='PanZoom.png', p=buttonLayout, en= True, onc="cmds.setAttr(playblasterValues['currentCamera'] + '.panZoomEnabled', 1)", ofc=functions.deactiveZoomPan)
    cmds.popupMenu('panZoomPopUp', parent='panZoomCtr', numberOfItems=4)
    cmds.radioCollection(p='panZoomPopUp')
    cmds.menuItem('2DPan/ZoomTool', label='Pan/Zoom Tool', p='panZoomPopUp', c= functions.activeZoomPan)
    cmds.menuItem(d=True, p='panZoomPopUp')
    cmds.menuItem('2DReset', label='Reset', p='panZoomPopUp', c= functions.resetZoomer)
    if not cmds.panZoomCtx('playblasterPanTool', exists=True):
        cmds.panZoomCtx(n='playblasterPanTool', pm=True)

    cmds.symbolButton(h=20,image='openBar.png',p=buttonLayout, en= False)                         
    cmds.symbolButton(image='playblast.png', p=buttonLayout, en= True, c=functions.playLast)
    
    # hacemos los slider que van a controlar el offset del image plane y su opacidad
    cmds.separator(h=10, hr=True, p=topLayout,style='single')
    
    downSliderLayout = cmds.rowLayout(p=topLayout, numberOfColumns=2, adj=2)
    cmds.optionMenu('sliderMode', p=downSliderLayout, cc=functions.changeSliderMode, en=False)
    cmds.menuItem( label='iPlane alpha')
    cmds.menuItem( label='iPlane depth')
    cmds.menuItem('playblasterOffsetOption', label='iPlane offset')

    opacitySlider = cmds.floatSlider('opacitySlider', p=downSliderLayout, min=0, max=1, v=1, en=False, dc=functions.changeSliderValue)    
    
    bottomLayout = cmds.columnLayout(adj=True,p=mainLayout)
    cmds.separator(h=10, p=bottomLayout,style='single',hr=True)    

    # boton para setear el rango de playblast al rango del timeSlider y campos para setear el rango del playblast
    framesLayout = cmds.rowLayout(h=26, numberOfColumns=7, p=bottomLayout, adj=4)
    cmds.text( label='Start Frame  ')
    cmds.intField('startFrame', w=50, p=framesLayout, v= cmds.playbackOptions(q=True,min=True), cc= functions.startFrameChange)
    cmds.separator(w=20, p=framesLayout,style='none')
    rangeButton = cmds.button('setToSceneRange', p=framesLayout, l='Set Scene Range',w=100, c= functions.sceneRange)
    cmds.separator(w=20, p=framesLayout,style='none')
    cmds.intField('endFrame', w=50, p=framesLayout, v= cmds.playbackOptions(q=True,max=True), cc= functions.endFrameChange)    
    cmds.text( label='  End Frame')

    # boton de playblast
    cmds.separator(h=5, w=200, p=bottomLayout,style='none')
    cmds.button(label = '- P L A Y B L A S T -', p=bottomLayout, en= True, c=functions.blast)
    cmds.separator(h=10, w=200, hr=True, p=bottomLayout,style='shelf')
    
    # botones inferiores con selector de guardado, y opciones de play solamente en la vista del playblaster, add un rewind y forward xq es comodo tenerlo ahi tambien
    checkLayout = cmds.rowLayout(h=26, numberOfColumns=6, p=bottomLayout, adj=3)
    cmds.radioCollection(p=blastWindow)
    cmds.radioButton('temporaryPlayblast', label='Temporary Playblast', sl=True, p=checkLayout, cc="playblasterValues['saveOption']='temporaryPlayblast'")
    cmds.radioButton('custom', label='Save Playblast', sl=False, p=checkLayout, cc="playblasterValues['saveOption']='custom'")
    cmds.popupMenu('customPopUp', parent='custom', numberOfItems=1)
    cmds.menuItem(label = 'set custom path', c=functions.customPathSelector, p='customPopUp')    
    cmds.radioButton('version2Review', label='Version To Review', sl=False, p=checkLayout, en=True, cc="playblasterValues['saveOption']='version2Review'")
    cmds.symbolButton('rewindCtr', image= 'timerew.png', p=checkLayout, en= True, c='cmds.currentTime(cmds.playbackOptions(q=True,min=True),e=True)')       
    cmds.symbolCheckBox('playCtr', ofi='play_S.png', oni= 'pause_S.png', p=checkLayout, en= True, v=False, onc= functions.playOnly, ofc= functions.stop)    
    cmds.symbolButton('forwardCtr', image= 'timefwd.png', p=checkLayout, en= True, c='cmds.currentTime(cmds.playbackOptions(q=True,max=True),e=True)')       

    # ajustamos los layouts para se acomoden al tamagno de la ventana
    cmds.formLayout(mainLayout, e=True,
                    attachForm=[(topLayout,'top',-1),(topLayout,'right',5),(topLayout,'left',5), (panelViewLayout,'right',5),(panelViewLayout,'left',5), (bottomLayout,'bottom',5),(bottomLayout,'right',5),(bottomLayout,'left',5)],
                    attachControl=[(panelViewLayout,'top',5,topLayout),(panelViewLayout,'bottom',1,bottomLayout)]) 

    # forzamos que aparezca seleccionado la opcione de scala a 50 xq no se xq cojones no le da la gana de marcarla 
    cmds.menuItem('playblasterScale_' + str(playblasterValues['scale']), rb=True, e=True)
    
    #ejecutamos la funcion que va a setear los valores por defecto en los iconos checkeando el estado de la camara del panel 
    functions.cameraInitState()   

    # se muestra la ventana y se devuelve la variable que contiene los datos de usuario
    cmds.showWindow(blastWindow)
    
    checkJob()    
    refreshPlayblasterWindow()


    return playblasterValues


