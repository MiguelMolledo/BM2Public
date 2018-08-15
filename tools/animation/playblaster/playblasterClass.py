'''to do: 
-posibilidad de hacer mas de un image plane y seleccionar cual quieres que te muestre 
-que publique lo videos en su carpeta de dropbox 
-que haga una copia de la escena en su sitio chk 
''' 
 
import maya.cmds as cmds 
import maya.mel as mel 
import os 
import playblasterFunctionsClass as functions 
import playblasterAnimUtils as playblasterAnimUtils 
import BM2Public.tools.abcExporter.abcExporterUI as abcExporter 
import BM2Public.tools.abcExporter.abcExporterFunctions as abcExporterFunctions 
 
class playblaster(object): 
     
    def __init__(self): 
        self.staticValues = functions.jsonPlayblaster().read() 
        self.playblasterValues = {'custom': '', 
                             'version2Review': '', 
                             'lastUserPlayblastPath': self.staticValues['lastUserPlayblastPath'], 
                             'temporaryPlayblast': None, 
                             'sound': None, 
                             'activateSound': True, 
                             'format': 'qt', 
                             'showOrnaments': self.staticValues['showOrnaments'], 
                             'offscreen': self.staticValues['offscreen'], 
                             'scale': self.staticValues['scale'], 
                             'cameras': None, 
                             'currentCamera': 'persp', 
                             'pencil': None, 
                             'imagesPlanes': {}, 
                             'currentIPlane': None, 
                             'currentGreasePencil': None, 
                             'frameChooser': None, 
                             'saveOption': 'temporaryPlayblast', 
                             } 
 
    def checkWindowAtStartMaya(self): 
        if cmds.panel('blasterCam', exists=True) or cmds.workspaceControl('playblaster', exists=True): 
            playblasterWindow = playblaster() 
            playblasterWindow.show() 
            return playblasterWindow.playblasterValues 
 
 
    def checkWorkspace(self): 
        if cmds.panel('blasterCam', exists=True) and cmds.workspaceControl('playblaster', exists=True): 
            cmds.workspaceControl('playblaster', restore=True, e=True) 
 
            return True 
 
    def checkJob(self): 
        sesionJobs = cmds.scriptJob(lj=True) 
        jobExist = False 
        for job in sesionJobs: 
            if 'refreshPlayblasterWindow()' in job: 
                jobExist = True 
                break 
        if not jobExist: 
            cmds.scriptJob(e=('PreFileNewOrOpened', 'playblasterWindow.refreshPlayblasterWindow()'), permanent=True) 
 
    def refreshPlayblasterWindow(self): 
        fileInformation = functions.pipeInfo() 
 
        if cmds.modelPanel('blasterCam', q=True, ex=True): 
            cmds.modelPanel('blasterCam', e=True, mbv=False) 
            self.playblasterValues['currentCamera'] = cmds.modelPanel('blasterCam', q=True, cam=True) 
            self.cameraInitState() 
            functions.sceneRange() 
 
 
            if fileInformation and fileInformation['department'] == 'animation': 
                cmds.radioButton('version2Review', e=True, en=True, vis=True) 
                cmds.menu('caches', e=True, en=True, vis=True) 
                cmds.button('setToSceneRange', l='Set Shotgun Range', e=True) 
 
            else: 
                cmds.radioButton('version2Review', e=True, en=False, vis=False) 
                cmds.radioButton('temporaryPlayblast', e=True, sl=True) 
                self.playblasterValues['saveOption'] = 'temporaryPlayblast' 
                cmds.menu('caches', e=True, en=False, vis=False) 
                cmds.button('setToSceneRange', l='Set Scene Range', e=True) 
 
        if cmds.window('abcExporter', exists=True): 
            abcExporterFunctions.refreshUI() 
 
    def show(self): 
        '''esta funcion genera la ui 
        empezamos definiendo las variables globales que tendra la ventana y que modificara,  
        tengo que pensar en guardar en un json externo mejor que como variable global al menos settings como lastUserPlayblastPath, temporaryPlayblast,proyectPath, format, scale, showOrnaments, activateSound, y offscreen 
        ''' 
        #self.staticValues = functions.jsonPlayblaster().read() 
 
        # listamos las camaras en escena filtrando las camaras por defecto de maya y cogemos la primera para setearla como camara inicial,  
        if functions.userCams(): 
            self.playblasterValues['currentCamera'] = functions.userCams()[0] 
 
            # si existe la ventana el panelview o el workspaceControl lo eliminamos 
        if self.checkWorkspace(): 
            return #self.playblasterValues 
 
        else: 
            self.playblasterValues['startFrame'] = cmds.playbackOptions(q=True, min=True) 
            self.playblasterValues['endFrame'] = cmds.playbackOptions(q=True, max=True) 
            self.createUi() 
 
 
    def createUi(self): 
 
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
            blastWindow = 'playblaster' 
 
        # menu de opciones de la ventana, en funcion son 4 menus que van a permitir cambiar las opciones de formato  
        menuLayout = cmds.menuBarLayout('playblasterMenuLayout', p=blastWindow) 
        camsMenu = cmds.menu('camerasMenu', label='Cameras', p=menuLayout, pmc=self.createMenuCams) 
        windowMenu = cmds.menu('playblasterMenu', label='Playblast Options', p=menuLayout) 
 
        cmds.menuItem('playblasterScaleOptions', label='Scale', sm=True) 
        cmds.radioMenuItemCollection() 
        cmds.menuItem('playblasterScale_50', label='50', rb=False, c="playblasterWindow.playblasterValues['scale']=50") 
        cmds.menuItem('playblasterScale_70', label='70', rb=False, c="playblasterWindow.playblasterValues['scale']=70") 
        cmds.menuItem('playblasterScale_100', label='100', rb=False, c="playblasterWindow.playblasterValues['scale']=100") 
        cmds.setParent('..', menu=True) 
 
        cmds.menuItem(divider=True) 
        cmds.menuItem('playblasterShowornamentsOption', label='Show ornaments', 
                      cb= self.playblasterValues['showOrnaments'], 
                      c="playblasterWindow.playblasterValues['showOrnaments'] = cmds.menuItem('playblasterShowornamentsOption',q=True,cb=True)") 
        cmds.menuItem('playblasterSoundOption', label='Sound activate', cb= self.playblasterValues['activateSound'], 
                      c="playblasterWindow.playblasterValues['activateSound'] = cmds.menuItem('playblasterSoundOption',q=True,cb=True)") 
        cmds.menuItem('playblasterOffscreenOption', label='offscreen', cb= self.playblasterValues['offscreen'], 
                      c="playblasterWindow.playblasterValues['offscreen'] = cmds.menuItem('playblasterOffscreenOption',q=True,cb=True)") 
 
        showMenu = cmds.menu('showMenu', label='Show', p=menuLayout, pmc=self.preOpenShowMenu) 
        cmds.menuItem('curvesVis', label='nurbs curves', cb=self.staticValues['nurbsCurves'], 
                      c=self.toogleNurbsCurves) 
        cmds.menuItem('locatorsVis', label='locators', cb=self.staticValues['locators'], c=self.toogleLocators) 
        cmds.menuItem('motionTrailsVis', label='motion trails', cb=self.staticValues['motionTrails'], 
                      c=self.toogleMotionTrails) 
        cmds.menuItem(divider=True, dl='lights') 
 
        cmds.menuItem('lightsOnVis', label='lights on', cb=self.staticValues['lightsOn'], c=self.toogleLightsOn) 
        cmds.menuItem('shadowsVis', label='shadows', cb=self.staticValues['shadows'], c=self.toogleShadows) 
        cmds.menuItem(divider=True, dl='2D planes') 
 
        cmds.menuItem('iPlaneVis', label='images planes', cb=self.staticValues['imagePlane'], 
                      c=self.toogleImagePlanes) 
        cmds.menuItem('greaseVis', label='grease pencil', cb=self.staticValues['greasePencils'], 
                      c=self.toogleGreasePencils) 
        cmds.menuItem(divider=True) 
 
        cmds.menuItem('manipulatorsVis', label='manipulators', cb=self.staticValues['manipulators'], 
                      c=self.toogleManipulators) 
 
        utilsMenu = cmds.menu('utilsMenu', label='Utils', p=menuLayout, to=True) 
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
        cmds.setParent('..', menu=True) 
 
        cmds.menuItem(divider=True, dl='Constraints') 
        cmds.menuItem(label='intermediate and constraint', image='interactiveBindTool.png', 
                      c=playblasterAnimUtils.intermediateAndConstraint) 
        cmds.menuItem(label='parent constraint', image='parentConstraint.png', c='cmds.parentConstraint(mo=True)') 
        cmds.menuItem(ob=True, c=cmds.ParentConstraintOptions) 
 
        cachesMenu = cmds.menu('caches', label='Caches', p=menuLayout) 
        cmds.menuItem('exportUi', label='export window', c=abcExporter.abcExporterUI) 
 
        mainLayout = cmds.formLayout('formLayout') 
        panelViewLayout = cmds.frameLayout(h=300, lv=0, p=mainLayout, bv=True) 
 
        if cmds.panel('blasterCam', exists=True): 
            cmds.deleteUI('blasterCam', pnl=True) 
 
        camPanel = cmds.modelPanel('blasterCam', l='blasterCam', mbv=False, init=False, needsInit=False, 
                                   p=panelViewLayout) 
 
        cmds.modelPanel('blasterCam', e=True, cam=self.playblasterValues['currentCamera']) 
        cmds.modelEditor('blasterCam', e=True, 
                         cameras=False, 
                         manipulators=self.staticValues['manipulators'], 
                         grid=False, 
                         headsUpDisplay=False, 
                         joints=False, 
                         ikHandles=False, 
                         lights=False, 
                         locators=self.staticValues['locators'], 
                         nurbsCurves=self.staticValues['nurbsCurves'], 
                         motionTrails=self.staticValues['motionTrails'], 
                         textures=False, 
                         displayAppearance='smoothShaded', 
                         rendererName='vp2Renderer', 
                         displayTextures=True, 
                         hud=False, 
                         sel=False, 
                         shadows=self.staticValues['shadows'], 
                         imagePlane=self.staticValues['imagePlane'], 
                         greasePencils=self.staticValues['greasePencils'], 
                         displayLights=self.staticValues['displayLights']) 
 
        # escondemos los menus tipicos del panel view por defecto y setamos la camara inicial  
        functions.hidePanelsMenu(camPanel) 
 
        # empezamos con los botones de la ventana 
        topLayout = cmds.columnLayout(adj=True, p=mainLayout) 
        cmds.separator(w=50, hr=True, p=topLayout, style='single') 
 
        buttonLayout = cmds.rowLayout(h=35, numberOfColumns=21, p=topLayout, adj=8) 
 
        cmds.symbolCheckBox(h=35, image='paintFXtoNurbs.png', p=buttonLayout, en=True, onc=self.blasterPencil, 
                            ofc=self.greaseOff) 
        cmds.symbolButton(h=35, image='deleteActive.png', p=buttonLayout, en=True, c=self.deleteGreasePencil) 
 
        cmds.symbolButton(h=20, image='closeBar.png', p=buttonLayout, en=False) 
        cmds.symbolButton('loadVideo', h=35, image='fluidCacheCreate.png', p=buttonLayout, en=True, 
                          c=self.setIPlane) 
        cmds.symbolButton(h=35, image='fluidCacheDelete.png', p=buttonLayout, en=True, c=self.deleteIplane) 
        cmds.popupMenu('videoRefPath', parent='loadVideo', numberOfItems=1) 
        cmds.radioCollection(p='videoRefPath') 
        cmds.menuItem('videoSelector', label='load last playblast as reference', p='videoRefPath', 
                      c=self.defaultIplane) 
        cmds.text(label='1st Frame') 
        cmds.intField('IplaneStart', w=50, p=buttonLayout, v=cmds.playbackOptions(q=True, min=True), en=False, 
                      cc=self.changeMovieStartFrame) 
 
        cmds.separator(w=10, hr=True, p=buttonLayout, style='none') 
        cmds.symbolButton('shadedCtr', w=20, h=20, image='Shaded.png', p=buttonLayout, en=True, 
                          c=self.toogleShaded) 
        cmds.symbolCheckBox('wireframeShadedCtr', w=20, h=20, image='WireFrameOnShaded.png', p=buttonLayout, 
                            en=True, onc=self.wireFrameOnShaded, 
                            ofc='cmds.modelEditor("blasterCam",e=True, wos= 0)') 
        cmds.symbolCheckBox('cameraMaskCtr', w=20, h=20, image='ResolutionGate.png', p=buttonLayout, 
                            cc=self.toogleMask, en=True) 
 
        cmds.symbolButton(h=20, image='closeBar.png', p=buttonLayout, en=False) 
        cmds.symbolButton('rendererCtr', w=25, h=25, image='hyper_s_ON.png', p=buttonLayout, en=True, 
                          c=self.toogleRenderer) 
        cmds.symbolButton('texturedCtr', w=20, h=20, image='Textured.png', p=buttonLayout, en=True, ebg=False, 
                          c=self.toogleAppereance) 
        cmds.symbolCheckBox('sampleCtr', w=20, h=20, image='MultisampleAA.png', p=buttonLayout, en=True, 
                            onc='cmds.setAttr("hardwareRenderingGlobals.multiSampleEnable", 1)', 
                            ofc='cmds.setAttr("hardwareRenderingGlobals.multiSampleEnable", 0)') 
        cmds.symbolCheckBox('aOcclusionCtr', w=20, h=20, image='SSAO.png', p=buttonLayout, en=True, 
                            onc='cmds.setAttr("hardwareRenderingGlobals.ssaoEnable", 1)', 
                            ofc='cmds.setAttr("hardwareRenderingGlobals.ssaoEnable", 0)') 
 
        # botones con las opciones de camara(bloquear la camara y manipular el zoom y paneo 2D) 
        cmds.symbolButton(h=20, image='closeBar.png', p=buttonLayout, en=False) 
        cmds.symbolCheckBox('lockCameraCtr', w=20, h=20, image='CameraLock.png', p=buttonLayout, en=True, 
                            onc="cmds.camera(cmds.modelPanel('blasterCam', q=True, cam=True), e=True, lockTransform=True)", 
                            ofc="cmds.camera(cmds.modelPanel('blasterCam', q=True, cam=True), e=True, lockTransform=False)") 
        cmds.symbolCheckBox('panZoomCtr', w=20, h=20, image='PanZoom.png', p=buttonLayout, en=True, 
                            onc=self.activeZoomPan, 
                            ofc=self.deactiveZoomPan) 
        cmds.popupMenu('panZoomPopUp', parent='panZoomCtr', numberOfItems=4) 
        cmds.radioCollection(p='panZoomPopUp') 
        cmds.menuItem('2DPan/ZoomTool', label='Pan/Zoom Tool', p='panZoomPopUp', c= self.activeZoomPan) 
        cmds.menuItem(d=True, p='panZoomPopUp') 
        cmds.menuItem('2DReset', label='Reset', p='panZoomPopUp', c=self.resetZoomer) 
        if not cmds.panZoomCtx('playblasterPanTool', exists=True): 
            cmds.panZoomCtx(n='playblasterPanTool', pm=True) 
 
        cmds.symbolButton(h=20, image='openBar.png', p=buttonLayout, en=False) 
        cmds.symbolButton(image='playblast.png', p=buttonLayout, en=True, c=self.playLast) 
 
        # hacemos los slider que van a controlar el offset del image plane y su opacidad 
        cmds.separator(h=10, hr=True, p=topLayout, style='single') 
 
        downSliderLayout = cmds.rowLayout(p=topLayout, numberOfColumns=2, adj=2) 
        cmds.optionMenu('sliderMode', p=downSliderLayout, cc=self.changeSliderMode, en=False) 
        cmds.menuItem(label='iPlane alpha') 
        cmds.menuItem(label='iPlane depth') 
        cmds.menuItem('playblasterOffsetOption', label='iPlane offset') 
 
        opacitySlider = cmds.floatSlider('opacitySlider', p=downSliderLayout, min=0, max=1, v=1, en=False, 
                                         dc=self.changeSliderValue) 
 
        bottomLayout = cmds.columnLayout(adj=True, p=mainLayout) 
        cmds.separator(h=10, p=bottomLayout, style='single', hr=True) 
 
        # boton para setear el rango de playblast al rango del timeSlider y campos para setear el rango del playblast 
        framesLayout = cmds.rowLayout(h=26, numberOfColumns=7, p=bottomLayout, adj=4) 
        cmds.text(label='Start Frame  ') 
        cmds.intField('startFrame', w=50, p=framesLayout, v=cmds.playbackOptions(q=True, min=True), 
                      cc=self.startFrameChange) 
        cmds.separator(w=20, p=framesLayout, style='none') 
        rangeButton = cmds.button('setToSceneRange', p=framesLayout, l='Set Scene Range', w=100, 
                                  c=functions.sceneRange) 
        cmds.separator(w=20, p=framesLayout, style='none') 
        cmds.intField('endFrame', w=50, p=framesLayout, v=cmds.playbackOptions(q=True, max=True), 
                      cc=self.endFrameChange) 
        cmds.text(label='  End Frame') 
 
        # boton de playblast 
        cmds.separator(h=5, w=200, p=bottomLayout, style='none') 
        cmds.button(label='- P L A Y B L A S T -', p=bottomLayout, en=True, c="playblasterWindow.blast()") 
        cmds.separator(h=10, w=200, hr=True, p=bottomLayout, style='shelf') 
 
        # botones inferiores con selector de guardado, y opciones de play solamente en la vista del playblaster, add un rewind y forward xq es comodo tenerlo ahi tambien 
        checkLayout = cmds.rowLayout(h=26, numberOfColumns=6, p=bottomLayout, adj=3) 
        cmds.radioCollection(p=blastWindow) 
        cmds.radioButton('temporaryPlayblast', label='Temporary Playblast', sl=True, p=checkLayout, 
                         cc="playblasterWindow.playblasterValues['saveOption'] = 'temporaryPlayblast'") 
        cmds.radioButton('custom', label='Save Playblast', sl=False, p=checkLayout, 
                         cc="playblasterWindow.playblasterValues['saveOption'] = 'custom'") 
 
        cmds.popupMenu('customPopUp', parent='custom', numberOfItems=1) 
        cmds.menuItem(label='set custom path', c=self.customPathSelector, p='customPopUp') 
        cmds.radioButton('version2Review', label='Version To Review', sl=False, p=checkLayout, en=True, 
                         cc="playblasterWindow.playblasterValues['saveOption'] = 'version2Review'") 
        cmds.symbolButton('rewindCtr', image='timerew.png', p=checkLayout, en=True, 
                          c='cmds.currentTime(cmds.playbackOptions(q=True,min=True),e=True)') 
        cmds.symbolCheckBox('playCtr', ofi='play_S.png', oni='pause_S.png', p=checkLayout, en=True, v=False, 
                            onc=self.playOnly, ofc=self.stop) 
        cmds.symbolButton('forwardCtr', image='timefwd.png', p=checkLayout, en=True, 
                          c='cmds.currentTime(cmds.playbackOptions(q=True,max=True),e=True)') 
 
        # ajustamos los layouts para se acomoden al tamagno de la ventana 
        cmds.formLayout(mainLayout, e=True, 
                        attachForm=[(topLayout, 'top', -1), (topLayout, 'right', 5), (topLayout, 'left', 5), 
                                    (panelViewLayout, 'right', 5), (panelViewLayout, 'left', 5), 
                                    (bottomLayout, 'bottom', 5), (bottomLayout, 'right', 5), 
                                    (bottomLayout, 'left', 5)], 
                        attachControl=[(panelViewLayout, 'top', 5, topLayout), 
                                       (panelViewLayout, 'bottom', 1, bottomLayout)]) 
 
        # forzamos que aparezca seleccionado la opcione de scala a 50 xq no se xq cojones no le da la gana de marcarla  
        cmds.menuItem('playblasterScale_' + str(self.getPlayblasterValue('scale')), rb=True, e=True) 
 
        # ejecutamos la funcion que va a setear los valores por defecto en los iconos checkeando el estado de la camara del panel  
        self.cameraInitState() 
 
        # se muestra la ventana y se devuelve la variable que contiene los datos de usuario 
        cmds.showWindow(blastWindow) 
 
        self.checkJob() 
        self.refreshPlayblasterWindow() 
 
        #return self.playblasterValues 
 
 
    def getPlayblasterValue(self, item): 
        return self.playblasterValues[item] 
 
    def setPlayblasterValue(self, item, value): 
        self.playblasterValues[item] = value 
 
 
    def playLast(self,*args): 
        if self.playblasterValues['lastUserPlayblastPath']: 
            cmds.launch(movie=self.playblasterValues['lastUserPlayblastPath']) 
        else: 
            cmds.warning('there is no previous playblast') 
 
 
    def customPathSelector(self,*args): 
        '''refresca el valor de custom path del diccionario para guardar el video en disco en funcion de la eleccion de path por el usuario 
        ''' 
        try: 
            self.setPlayblasterValue('custom', cmds.fileDialog2(fileFilter='*.mov', dialogStyle=1, caption='choose a directory to save the playblast', fileMode=0)[0]) 
        except: 
            pass 
 
 
    def createMenuCams(self,*args): 
        '''esta funcion recrea el los items del menu de camaras y marca como seleccionada la camara que este en el panel cada vez que se despliega el menu de seleccion de camaras 
        ''' 
        defaultCameras = ('persp', 'top', 'side', 'front') 
        self.playblasterValues['cameras'] = [] 
        sceneCameras = functions.userCams() 
        cmds.menu('camerasMenu', e=True, dai=True)  # se borra todo el menu desplegable de seleccion de camara 
        cmds.radioMenuItemCollection(p='camerasMenu') 
        # se recorre la lista de las camaras creadas por el usuario y se crea un item para el menu con cada una de ellas 
        if sceneCameras: 
            cmds.menuItem(divider=True, dl='User Cameras', p='camerasMenu') 
            for o in sceneCameras: 
                if o.replace('Shape', '') == cmds.modelPanel('blasterCam', q=True, cam=True): 
                    state = True 
                else: 
                    state = False 
 
                camara = cmds.menuItem(o, label=o.replace('Shape', ''), p='camerasMenu', c=self.setCameraOnPanel, rb=state) 
                if camara not in self.playblasterValues['cameras']: 
                    self.playblasterValues['cameras'].append(camara) 
 
        cmds.menuItem(divider=True, dl='Default Cameras', p='camerasMenu') 
 
        for i in defaultCameras: 
            if i.replace('Shape', '') == cmds.modelPanel('blasterCam', q=True, cam=True): 
                state = True 
            else: 
                state = False 
 
            camara = cmds.menuItem(i, label=i.replace('Shape', ''), p='camerasMenu', c=self.setCameraOnPanel, rb=state) 
            if camara not in self.playblasterValues['cameras']: 
                self.playblasterValues['cameras'].append(camara) 
 
        cmds.menuItem(divider=True, p='camerasMenu') 
        cmds.menuItem('selectCamera', label='Select Camera', p='camerasMenu', 
                      c="cmds.select(cmds.modelPanel('blasterCam', q=True, cam=True))") 
        cmds.menuItem('newCamera', label='New Camera', i='Camera.png', p='camerasMenu', c=self.newCamera) 
 
 
    def newCamera(self,*args): 
        cameraName = cmds.camera(n="playblasterCam") 
        cmds.rename(cameraName[-1], cameraName[0] + 'Shape') 
 
 
    def setCameraOnPanel(self,*args): 
        for o in self.playblasterValues['cameras']: 
            if cmds.menuItem(o, q=True, rb=True): 
                cameraItem = o.split('|')[-1] 
                cmds.modelPanel('blasterCam', e=True, cam=cameraItem) 
                cmds.floatSlider('opacitySlider', e=True, v=1.0) 
                self.cameraInitState() 
 
    def changeCameraView(self,*args): 
        cmds.modelPanel('blasterCam',e=True, cam= cmds.optionMenu('camsMenu',q=True,v=True)) 
 
 
    def blast(self,*args): 
        review = False 
        cam = cmds.modelPanel('blasterCam', q=True, cam=True) 
        camShape = cmds.listRelatives(cam, s=True)[0] 
        sceneSound = cmds.ls(typ='audio') 
        startTime = cmds.intField('startFrame', v=True, q=True) 
        endTime = cmds.intField('endFrame', v=True, q=True) 
        scale = self.getPlayblasterValue('scale') 
 
        gPlayBackSlider = mel.eval('$temp=$gPlayBackSlider') 
        if cmds.timeControl(gPlayBackSlider, query=True, rv=True): 
            rangeSelected = cmds.timeControl(gPlayBackSlider, query=True, ra=True) 
            startTime = int(rangeSelected[0]) 
            endTime = int(rangeSelected[1]) 
 
        if sceneSound and self.playblasterValues['activateSound']: 
            self.playblasterValues['sound'] = sceneSound[0] 
        else: 
            self.playblasterValues['sound'] = None 
 
        wh = (cmds.getAttr('defaultResolution.width'), cmds.getAttr('defaultResolution.height')) 
        displayValues = {'overscan': [1], 
                         'displayResolution': [0], 
                         'displayGateMask': [0]} 
 
        # save the camDisplayValues into dictionary 
        for value in displayValues: 
            displayValues[value].append(cmds.getAttr(camShape + '.' + value)) 
            cmds.setAttr(camShape + '.' + value, displayValues[value][0]) 
 
        # comprobamos la opcion de guardado del playblast, si es version2 review forzamos que se sobreescriba el archivo 
        if self.playblasterValues['saveOption'] == 'version2Review': 
            fileInfo = functions.pipeInfo() 
            review = True 
            # name = userConfirmDescriptionField(description=fileInfo['description'], fileType='version', prodState='chk') 
            name = functions.confirm(path=functions.getPaths(description=fileInfo['description'], fileType='version', prodState='chk')) 
            scale = 100 
 
        else: 
            name = functions.confirm(self.playblasterValues[self.playblasterValues['saveOption']], 
                           incrementalOption=True) 
 
        # obtenemos la ruta para comprobar si existe alguna version previa del playblast para dar la opcion de incrementalSave 
        if not name and self.playblasterValues['saveOption'] != 'temporaryPlayblast': 
            cmds.warning('no video created') 
            return 
 
        else: 
            self.playblasterValues['lastUserPlayblastPath'] = cmds.playblast(viewer=True, 
                                                                                      format='qt', 
                                                                                      clearCache=1, 
                                                                                      showOrnaments=self.playblasterValues[ 
                                                                                          'showOrnaments'], 
                                                                                      offScreen=self.playblasterValues[ 
                                                                                          'offscreen'], 
                                                                                      fp=4, 
                                                                                      percent=scale, 
                                                                                      compression="H.264", 
                                                                                      quality=100, 
                                                                                      widthHeight=wh, 
                                                                                      epn='blasterCam', 
                                                                                      filename=name, 
                                                                                      sound=self.playblasterValues[ 
                                                                                          'sound'], 
                                                                                      forceOverwrite=True, 
                                                                                      startTime=startTime, 
                                                                                      endTime=endTime) 
 
        # restore the camDisplayValues 
        for value in displayValues: 
            cmds.setAttr(camShape + '.' + value, displayValues[value][1]) 
 
        staticValues = functions.jsonPlayblaster() 
        for staticValue in ('showOrnaments', 'scale', 'offscreen', 'lastUserPlayblastPath'): 
            staticValues.modify(staticValue, self.playblasterValues[staticValue]) 
 
        if review: 
            functions.sendToCheck(name) 
 
 
    def preOpenShowMenu(self,*args): 
        staticValues=functions.jsonPlayblaster().read() 
        cmds.menuItem('curvesVis', cb= staticValues['nurbsCurves'], e=True) 
        cmds.menuItem('locatorsVis', cb= staticValues['locators'], e=True) 
        cmds.menuItem('manipulatorsVis', cb= staticValues['manipulators'], e=True) 
        cmds.menuItem('lightsOnVis', cb= staticValues['lightsOn'], e=True) 
        cmds.menuItem('shadowsVis', cb= staticValues['shadows'], e=True) 
        cmds.menuItem('iPlaneVis', cb= staticValues['imagePlane'], e=True) 
        cmds.menuItem('greaseVis', cb= staticValues['greasePencils'], e=True) 
        cmds.menuItem('motionTrailsVis', cb= staticValues['motionTrails'], e=True) 
 
    def blasterPencil(self,*args): 
        '''esta funcion activa el context de grease pencil 
        ''' 
        cmds.setToolTo('greasePencilContext') 
 
    def greaseOff(self,*args): 
        '''esta funcion desactiva el context de grease pencil y cierra su ventana 
        ''' 
        if cmds.window('greasePencilFloatingWindow', exists=True): 
            cmds.deleteUI('greasePencilFloatingWindow') 
        cmds.setToolTo('moveSuperContext') 
 
    def startFrameChange(self,*args): 
        value = cmds.intField('startFrame', q=True, v=True) 
        self.playblasterValues['startFrame'] = value 
        cmds.intField('endFrame', e=True, min=value) 
 
    def endFrameChange(self,*args): 
        value = cmds.intField('endFrame', q=True, v=True) 
        self.playblasterValues['endFrame'] = value 
        cmds.intField('startFrame', e=True, max=value) 
 
    def toogleRenderer(self,*args): 
        if cmds.modelEditor('blasterCam', q=True, rendererName=True) == 'vp2Renderer': 
            cmds.modelEditor('blasterCam', e=True, rendererName='base_OpenGL_Renderer') 
            cmds.symbolButton('rendererCtr', image='hyper_s_OFF.png', e=True) 
 
        else: 
            cmds.modelEditor('blasterCam', e=True, rendererName='vp2Renderer') 
            cmds.symbolButton('rendererCtr', image='hyper_s_ON.png', e=True) 
 
    def cameraInitState(self): 
        '''esta funcion actualiza el estado de los simbolCheckoxs del playblaster cuando cambia la camara en el panel, 
        tambien refresca el valor de los sliders de opacidad y de offset en funcion de los valores del image plane 
        ''' 
        self.playblasterValues['camInitState'] = { 
            'mask': cmds.getAttr(cmds.modelPanel('blasterCam', q=True, cam=True) + '.displayGateMask'), 
            'antialiasing': cmds.getAttr("hardwareRenderingGlobals.multiSampleEnable"), 
            'aOcclusion': cmds.getAttr("hardwareRenderingGlobals.ssaoEnable"), 
            'locked': cmds.camera(cmds.modelPanel('blasterCam', q=True, cam=True), q=True, lockTransform=True), 
            'zoomer': cmds.getAttr(cmds.modelPanel('blasterCam', q=True, cam=True) + '.panZoomEnabled')} 
 
        cmds.symbolCheckBox('cameraMaskCtr', e=True, v=self.playblasterValues['camInitState']['mask']) 
        cmds.symbolCheckBox('sampleCtr', e=True, v=self.playblasterValues['camInitState']['antialiasing']) 
        cmds.symbolCheckBox('aOcclusionCtr', e=True, v=self.playblasterValues['camInitState']['aOcclusion']) 
        cmds.symbolCheckBox('lockCameraCtr', e=True, v=self.playblasterValues['camInitState']['locked']) 
        cmds.symbolCheckBox('panZoomCtr', e=True, v=self.playblasterValues['camInitState']['zoomer']) 
 
        self.getIplaneInfo(cmds.modelPanel('blasterCam', q=True, cam=True)) 
 
        if self.playblasterValues['currentIPlane']: 
            # setear el valor en el slider de transparencia 
            cmds.floatSlider('opacitySlider', e=True, en=True) 
            cmds.optionMenu('sliderMode', e=True, en=True) 
            self.changeSliderMode() 
 
            if cmds.getAttr(self.playblasterValues['currentIPlane'] + '.type') != 2 or 'playblaster' not in \ 
                    self.playblasterValues['currentIPlane']: 
                cmds.optionMenu('sliderMode', e=True, v='iPlane alpha') 
                cmds.menuItem('playblasterOffsetOption', e=True, en=False) 
                cmds.intField('IplaneStart', e=True, en=False) 
 
            else: 
                cmds.menuItem('playblasterOffsetOption', e=True, en=True) 
                cmds.intField('IplaneStart', e=True, en=True) 
 
        else: 
            cmds.intField('IplaneStart', e=True, en=False) 
            cmds.floatSlider('opacitySlider', e=True, en=False) 
            cmds.optionMenu('sliderMode', e=True, en=False) 
 
    def resetZoomer(self,*args): 
        '''esta funcion reestablece los valores por defecto de pan/zoom 2d de la camara 
        ''' 
        cameraShape = cmds.listRelatives(cmds.modelPanel('blasterCam', q=True, cam=True), s=True)[0] 
 
        cmds.setAttr(cameraShape + ".horizontalPan", 0) 
        cmds.setAttr(cameraShape + ".verticalPan", 0) 
        cmds.setAttr(cameraShape + ".zoom", 1) 
 
    def activeZoomPan(self,*args): 
        cmds.setAttr(cmds.modelPanel('blasterCam', q=True, cam=True) + '.panZoomEnabled', 1) 
        cmds.setToolTo('playblasterPanTool') 
        cmds.symbolCheckBox('panZoomCtr', e=True, v=True) 
 
    def deactiveZoomPan(self,*args): 
        cmds.setAttr(cmds.modelPanel('blasterCam', q=True, cam=True) + '.panZoomEnabled', 0) 
        cmds.setToolTo('moveSuperContext') 
 
    def changeMovieStartFrame(self,*args): 
        '''esta funcion modifica el frame en el que se muestra el fotograma 1 del video del imagePlane 
        ''' 
        value = cmds.intField('IplaneStart', v=True, q=True) 
        cmds.setAttr(self.playblasterValues['frameChooser'] + '.input1D[1]', value - 1) 
 
    def changeSliderValue(self,*args): 
        '''esta funcion cambia la opacidad cuando se modifica el slider de opacidad, desactivando los undos sin borrar la cola para aislar la basura de acciones que genera 
        ''' 
        option = cmds.optionMenu('sliderMode', q=True, v=True) 
        attr = {'iPlane alpha': '.alphaGain', 
                'iPlane depth': '.depth', 
                'iPlane offset': '.frameOffset'} 
 
        value = cmds.floatSlider('opacitySlider', v=True, q=True) 
        cmds.undoInfo(swf=False) 
        cmds.setAttr(self.playblasterValues['currentIPlane'] + attr[option], value) 
        cmds.undoInfo(swf=True) 
 
    def changeSliderMode(self,*args): 
        option = cmds.optionMenu('sliderMode', q=True, v=True) 
        filePath = cmds.getAttr(self.playblasterValues['currentIPlane'] + '.imageName') 
        fileName, file_extension = os.path.splitext(filePath) 
        movieType = ('.mov', '.mp4') 
        maxFrameOffset = 1 
 
        if file_extension in movieType: 
            maxFrameOffset = int(cmds.movieInfo(filePath, frameCount=True)[0]) 
 
        attr = {'iPlane alpha': ['.alphaGain', [0, 1]], 
                'iPlane depth': ['.depth', [0.15, 100]], 
                'iPlane offset': ['.frameOffset', [0, maxFrameOffset]]} 
 
        valueAtChange = cmds.getAttr(self.playblasterValues['currentIPlane'] + attr[option][0]) 
        cmds.floatSlider('opacitySlider', min=attr[option][1][0], max=attr[option][1][1], v=valueAtChange, e=True) 
 
    def getIplaneInfo(self,currentCamera): 
        '''actualiza el diccionario de los image planes que hay en la escena asiciandolos al transform de la camara que los contiene, y refresca el valor del iplane actual y el nodo frameChooser 
        ''' 
        # empezamos obteniendo el nombre de la shape de la camara y los hijos que pueda tener, porque los image planes y los grease pencil quedan dentro de la shape 
        camShape = cmds.listRelatives(currentCamera, s=True)[0] 
        descents = cmds.listRelatives(camShape, ad=True) 
        # generamos como valores vacios del diccionario el nombre del nodo framaChooser y el current Image Plane 
        self.playblasterValues['frameChooser'] = None 
        self.playblasterValues['currentIPlane'] = None 
 
        if descents: 
            for o in descents: 
                if cmds.nodeType(o) == 'imagePlane': 
                    self.playblasterValues['currentIPlane'] = cmds.listRelatives(o, p=True)[0] 
                    if cmds.getAttr(self.playblasterValues['currentIPlane'] + '.type') == 2: 
                        self.playblasterValues['frameChooser'] = cmds.listConnections(o + '.frameExtension')[0] 
 
                elif cmds.nodeType(o) == 'greasePlane': 
                    self.playblasterValues['currentGreasePencil'] = cmds.listRelatives(o, p=True)[0] 
 
        allImagePlanes = cmds.ls(typ='imagePlane') 
        for o in allImagePlanes: 
            cameraShape, iplaneShape = o.split('->') 
            cameraTransform = cmds.listRelatives(cameraShape, p=True)[0] 
            iplaneTransform = cmds.listRelatives(iplaneShape, p=True)[0] 
            if 'playblaster' in iplaneShape: 
                self.playblasterValues['imagesPlanes'][cameraTransform] = iplaneTransform 
 
    def iplane(self,file): 
        self.getIplaneInfo(cmds.modelPanel('blasterCam', q=True, cam=True)) 
        fileName, file_extension = os.path.splitext(file) 
        movieType = ('.mov', '.mp4') 
        iplane = cmds.imagePlane(n='playblasterImagePlane', camera=cmds.modelPanel('blasterCam', q=True, cam=True), 
                                 lookThrough=cmds.modelPanel('blasterCam', q=True, cam=True), showInAllViews=False, 
                                 nt=True) 
        iplane[1] = cmds.rename(iplane[1], iplane[0] + 'Shape') 
        cmds.setAttr(iplane[1] + '.imageName', file, typ='string') 
        cmds.setAttr(iplane[1] + '.depth', 0.15) 
        cmds.setAttr(iplane[1] + '.fit', 1) 
        cmds.setAttr(iplane[1] + '.overrideEnabled', 1) 
        cmds.setAttr(iplane[1] + '.overrideDisplayType', 2) 
 
        mel.eval('source AEimagePlaneTemplate.mel') 
        mel.eval("AEinvokeFitRezGate" + (' {0} {1}').format(iplane[1] + '.sizeX', iplane[1] + '.sizeY')) 
 
        cmds.floatSlider('opacitySlider', e=True, en=True, v=1) 
        cmds.optionMenu('sliderMode', e=True, en=True) 
 
        self.playblasterValues['imagesPlanes'][cmds.modelPanel('blasterCam', q=True, cam=True)] = iplane[0] 
        self.playblasterValues['currentIPlane'] = iplane[0] 
 
        if file_extension in movieType: 
            firstFrameMinus = cmds.createNode('plusMinusAverage', n='playblasterChooserStartFrame_minus') 
            cmds.setAttr(firstFrameMinus + '.operation', 2) 
            cmds.connectAttr('time1.outTime', firstFrameMinus + '.input1D[0]') 
            cmds.setAttr(firstFrameMinus + '.input1D[1]', cmds.intField('IplaneStart', v=True, q=True) - 1) 
            cmds.connectAttr(firstFrameMinus + '.output1D', iplane[1] + '.frameExtension') 
            cmds.setAttr(iplane[1] + '.type', 2) 
            cmds.setAttr(iplane[1] + '.useFrameExtension', lock=False) 
            cmds.setAttr(iplane[1] + '.useFrameExtension', True) 
 
            cmds.intField('IplaneStart', e=True, en=True, v=cmds.playbackOptions(q=True, min=True)) 
 
            self.playblasterValues['frameChooser'] = firstFrameMinus 
            self.changeMovieStartFrame() 
            cmds.menuItem('playblasterOffsetOption', e=True, en=True) 
        else: 
            cmds.menuItem('playblasterOffsetOption', e=True, en=False) 
 
        self.changeSliderMode() 
 
    def setIPlane(self,*args): 
        '''esta opcion inicia un fileDialog para explorar un archivo 
        devuelve la ruta seleccionada por el usuario 
        ''' 
        try: 
            file = cmds.fileDialog2(fileFilter='*.mov *.mp4 *.jpg *.png', dialogStyle=1, caption='choose file to load', 
                                    fileMode=1)[0] 
            if file: 
                if not self.playblasterValues['currentIPlane']: 
                    self.iplane(file) 
                else: 
                    self.deleteIplane() 
                    self.iplane(file) 
        except: 
            pass 
 
    def defaultIplane(self,*args): 
        '''esta funcion setea como iplane el ultimo playblast generado 
        ''' 
        if self.playblasterValues['lastUserPlayblastPath']: 
            if not self.playblasterValues['currentIPlane']: 
                self.iplane(self.playblasterValues['lastUserPlayblastPath']) 
            else: 
                self.deleteIplane() 
                self.iplane(self.playblasterValues['lastUserPlayblastPath']) 
        else: 
            cmds.warning('there is no recent playblast, please choose a videoFile to load') 
 
    def deleteIplane(self,*args): 
        '''esta funcion elimina el iplane de la camara y desactiva los sliders de control de offset y transparencia 
        tambien elimina de la variable global playblasterValues el item correspondiente a la camara que esta en ese momento en el playblaster 
        ''' 
        if self.playblasterValues['currentIPlane']: 
            if 'playblaster' not in self.playblasterValues['currentIPlane']: 
                userCheck = cmds.confirmDialog(db='ok', b=('ok', 'cancel'), cb='cancel', 
                                               m='this iPlane was not created with the tool, \n do you want to delete it?') 
 
                if userCheck != 'ok': 
                    return 
            else: 
                del self.playblasterValues['imagesPlanes'][cmds.modelPanel('blasterCam', q=True, cam=True)] 
 
            cmds.delete(self.playblasterValues['currentIPlane']) 
            cmds.intField('IplaneStart', e=True, en=False) 
            cmds.floatSlider('opacitySlider', e=True, en=False, v=0) 
            cmds.optionMenu('sliderMode', e=True, en=False) 
            self.playblasterValues['currentIPlane'] = None 
 
    def deleteGreasePencil(self,*args): 
        '''esta funcion elimina el greasePencil de la camara y desactiva los sliders de control de offset y transparencia 
        ''' 
        greasePencilTransform = None 
        camShape = cmds.listRelatives(cmds.modelPanel('blasterCam', q=True, cam=True), s=True)[0] 
        descents = cmds.listRelatives(camShape, ad=True) 
 
        if descents: 
            for o in descents: 
                if cmds.nodeType(o) == 'greasePlane': 
                    greasePencilTransform = cmds.listRelatives(o, p=True)[0] 
            if greasePencilTransform: 
                cmds.delete(greasePencilTransform) 
 
    def playOnly(self,*args): 
        # start playback only on playblaster panel 
        cmds.setFocus('blasterCam') 
 
        cmds.playbackOptions(v="active") 
        cmds.play(forward=True)  # start 
 
    def stop(self,*args): 
        # stop playback and return to update all views 
        cmds.play(state=False) 
        cmds.playbackOptions(v="all") 
 
 
    def toogleMask(self,*args): 
        if cmds.getAttr(cmds.modelPanel('blasterCam', q=True, cam=True) + '.displayGateMask'): 
            cmds.setAttr(cmds.modelPanel('blasterCam', q=True, cam=True) + '.displayGateMask', 0) 
            cmds.setAttr(cmds.modelPanel('blasterCam', q=True, cam=True) + '.displayResolution', 0) 
        else: 
            cmds.setAttr(cmds.modelPanel('blasterCam', q=True, cam=True) + '.displayResolution', 1) 
            cmds.setAttr(cmds.modelPanel('blasterCam', q=True, cam=True) + '.displayGateMask', 1) 
 
    def toogleShaded(self,*args): 
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
 
    def toogleLightsOn(self,*args): 
        staticValues = functions.jsonPlayblaster() 
        if cmds.modelEditor('blasterCam', q=True, displayLights = True) == 'default': 
            cmds.modelEditor('blasterCam', e=True, displayLights = 'all') 
            staticValues.modify('lightsOn', True) 
            staticValues.modify('displayLights','all') 
 
        else: 
            cmds.modelEditor('blasterCam', e=True, displayLights = 'default') 
            staticValues.modify('lightsOn', False) 
            staticValues.modify('displayLights','default') 
 
    def toogleShadows(self,*args): 
        staticValues = functions.jsonPlayblaster() 
        if cmds.modelEditor('blasterCam', q=True, shadows = True): 
            cmds.modelEditor('blasterCam', e=True, shadows = False) 
            staticValues.modify('shadows', False) 
        else: 
            cmds.modelEditor('blasterCam', e=True, shadows = True) 
            staticValues.modify('shadows', True) 
 
    def toogleNurbsCurves(self,*args): 
        staticValues = functions.jsonPlayblaster() 
        if cmds.modelEditor('blasterCam', q=True, nurbsCurves = True): 
            cmds.modelEditor('blasterCam', e=True, nurbsCurves = False) 
            staticValues.modify('nurbsCurves', False) 
        else: 
            cmds.modelEditor('blasterCam', e=True, nurbsCurves = True) 
            staticValues.modify('nurbsCurves', True) 
 
    def toogleLocators(self,*args): 
        staticValues = functions.jsonPlayblaster() 
        if cmds.modelEditor('blasterCam', q=True, locators = True): 
            cmds.modelEditor('blasterCam', e=True, locators = False) 
            staticValues.modify('locators', False) 
        else: 
            cmds.modelEditor('blasterCam', e=True, locators = True) 
            staticValues.modify('locators', True) 
 
    def toogleManipulators(self,*args): 
        staticValues = functions.jsonPlayblaster() 
        if cmds.modelEditor('blasterCam', q=True, manipulators = True): 
            cmds.modelEditor('blasterCam', e=True, manipulators = False) 
            staticValues.modify('manipulators', False) 
        else: 
            cmds.modelEditor('blasterCam', e=True, manipulators = True) 
            staticValues.modify('manipulators', True) 
 
    def toogleImagePlanes(self,*args): 
        staticValues = functions.jsonPlayblaster() 
        if cmds.modelEditor('blasterCam', q=True, imagePlane = True): 
            cmds.modelEditor('blasterCam', e=True, imagePlane = False) 
            staticValues.modify('imagePlane', False) 
        else: 
            cmds.modelEditor('blasterCam', e=True, imagePlane = True) 
            staticValues.modify('imagePlane', True) 
 
    def toogleGreasePencils(self,*args): 
        staticValues = functions.jsonPlayblaster() 
        if cmds.modelEditor('blasterCam', q=True, greasePencils = True): 
            cmds.modelEditor('blasterCam', e=True, greasePencils = False) 
            staticValues.modify('greasePencils', False) 
        else: 
            cmds.modelEditor('blasterCam', e=True, greasePencils = True) 
            staticValues.modify('greasePencils', True) 
 
    def toogleMotionTrails(self,*args): 
        staticValues = functions.jsonPlayblaster() 
        if cmds.modelEditor('blasterCam', q=True, motionTrails = True): 
            cmds.modelEditor('blasterCam', e=True, motionTrails = False) 
            staticValues.modify('motionTrails', False) 
        else: 
            cmds.modelEditor('blasterCam', e=True, motionTrails = True) 
            staticValues.modify('motionTrails', True) 
 
    def wireFrameOnShaded(self,*args): 
            cmds.modelEditor('blasterCam',e=True, wos= 1) 
            cmds.modelEditor('blasterCam',e=True, displayAppearance= 'smoothShaded') 
            cmds.symbolButton('shadedCtr', image='Shaded.png', e= True) 
 
    def toogleAppereance(self,*args): 
        if cmds.modelEditor('blasterCam', q=True, udm= True): 
            cmds.modelEditor('blasterCam',e=True, udm= False) 
            cmds.symbolButton('texturedCtr', image='Textured.png', e= True) 
        else: 
            cmds.modelEditor('blasterCam',e=True, udm= True) 
            cmds.symbolButton('texturedCtr', image='UseDefaultMaterial.png', e= True)
