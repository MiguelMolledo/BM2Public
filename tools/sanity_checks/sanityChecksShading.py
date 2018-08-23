#from __future__ import print_function
import maya.cmds as cmds
import os
import sys

myListMats = []

def checkMats():
    '''
    Esta funcion crea una lista con los shaders de la escena,
    eliminado de la lista los materiales pro defecto de maya.
    '''

    '''
    Declaro agunas variables necesarias para el UI
    '''
    global labelChkMats, myListMats, colorTextMats, numRowsMats, materialNodes, legalnames
    legalnames = []
    '''Leemos todas los materiales de la escena '''

    materialNodes = cmds.ls( materials = True)

    '''Borramos los materiales por defecto y actualizamos la lista'''

    defaultShaders = {'lambert1','particleCloud1', 'shaderGlow'}

    materialNodes = [e for e in materialNodes if e not in defaultShaders]

    for material in materialNodes:
        '''Iteramos la lista de materiales para comprobar su integridad'''
        shaStr = material.split('_')

        if shaStr[0] != allNodes[0] or shaStr[1] != 'shader' or any(ord(char)>126 for char in material):
            '''comprueba que la estructura del shader es correcta'''
            legalnames.append(material)

    if len(legalnames) != 0:
        '''si la lista es diferente de 0, hay materiales erroneos y crea una lista y
        cambia los valores de la variables de la UI para mostrar los textos en diferenete color'''
        labelChkMats =  "Checking shaders: Revise name convention!!"
        colorTextMats = [1.0,0.5,0.0]
        numRowsMats = 6
        myListMats = legalnames

    else:
        '''Si no, muestra un mensaje informando de que no ha encontardo materiales y
        cambia los valores de la variables de UI para mostrar los textos en diferenete color'''
        labelChkMats =  "Checking shaders: materials Correct!"
        colorTextMats = [0.0,1.0,0.0]
        numRowsMats= 1
def checkSG():
    '''Shaders
    Esta funcion crea una lista con los shadersEngines de la escena,
    eliminado de la lista los que estan por defecto de maya.
    '''

    '''
    Declaro agunas variables necesarias para el UI
    '''
    global labelChkSG, myListSG, colorTextSG, numRowsSG, sglegalnames, sgNodes
    sglegalnames = []
    myListSG = []
    '''Leemos todas los sgs de la escena '''

    sgNodes = cmds.ls( type = 'shadingEngine')

    '''Borramos los sgs por defecto y actualizamos la lista'''

    defaultShaderEngines = {'initialParticleSE', 'initialShadingGroup'}

    sgNodes = [e for e in sgNodes if e not in defaultShaderEngines]

    for sg in sgNodes:
        '''Iteramos la lista de sgs para comprobar su integridad'''
        sgStr = sg.split('_')

        if sgStr[0] != allNodes[0] or sgStr[1] != 'SG' or any(ord(char)>126 for char in sg):
            '''comprueba que la estructura del sg es correcta'''
            sglegalnames.append(sg)

    if len(sglegalnames) != 0:
        '''si la lista es diferente de 0, hay sgs erroneos y crea una lista y
        cambia los valores de la variables de la UI para mostrar los textos en diferenete color'''
        labelChkSG =  "Checking shadersEngines: Revise name convention!!"
        colorTextSG = [1.0,0.5,0.0]
        numRowsSG = 6
        myListSG = sglegalnames

    else:
        '''Si no, muestra un mensaje informando de que no ha encontardo sgs erroneos y
        cambia los valores de la variables de UI para mostrar los textos en diferenete color'''
        labelChkSG =  "Checking shaders: materials Correct!"
        colorTextSG = [0.0,1.0,0.0]
        numRowsSG= 1
def checkTexturesSG():
    '''Textures
    Esta funcion crea una lista con los texturas de la escena,
    eliminado de la lista los que estan por defecto de maya.
    '''

    '''
    Declaro agunas variables necesarias para el UI
    texture node : bm2_elmsha_elm_jetpack_sha_high_shading_2K_f0_mps_1
    file texture : P:/BM2/elm/jetPack/sha/high/shading/mps/bm2_elmsha_elm_jetpack_sha_high_shading_2K_f0_mps.tx
    '''
    global labelChkTxt, myListTxt, colorTextTxt, numRowsTxt, txlegalnames, TxtNodes, errorDescription
    myListTxt = []
    txlegalnames = []
    errorDescription = []
    '''Leemos todas los sgs de la escena '''

    TxtNodes = cmds.ls(type='file')
    r = range(1024,4096)

    for tx in TxtNodes:
        '''
        Iteramos la lista de txt para comprobar su integridad
        descomponemos la ruta y el archivo
        '''
        txPath = cmds.getAttr(str(tx) + '.fileTextureName')
        drive, path_and_file = os.path.splitdrive(txPath)
        path, file = os.path.split(path_and_file)
        fileName, ext = os.path.splitext(file)
        xRes = int(cmds.getAttr(str(tx) + '.outSizeX'))
        yRes = int(cmds.getAttr(str(tx) + '.outSizeY'))

        if drive != 'P:':
            '''comprueba que la ruta apunta a P:'''
            txlegalnames.append(tx)
            errorDescription.append(str(tx) + ' Is not rooted to drive P')
        if path.lower() != ('/BM2/elm/' + str(allNodes[0])  + '/sha/high/shading/mps').lower():
            '''comprueba que la ruta apunte a las texturas del asset, para ello ignoramos case sensitive'''
            txlegalnames.append(tx)
            errorDescription.append(str(tx) + ' Incorrect path')
        if ext != '.tx':
            '''comprueba que la extension sea tx'''
            txlegalnames.append(tx)
            errorDescription.append(str(tx) + ' Incorrect extension')
        if xRes not in r and yRes not in r:
            '''comprueba que la resolucion'''
            txlegalnames.append(tx)
            errorDescription.append(str(tx) + ' Resolution out of range')
            #print drive, path, fileName, ext, xRes, yRes
    print("\n".join(errorDescription))

    if len(txlegalnames) != 0:
        '''si la lista es diferente de 0, hay sgs erroneos y crea una lista y
        cambia los valores de la variables de la UI para mostrar los textos en diferenete color'''
        labelChkTxt =  "Checking texture paths: Revise root path and name convention and extension!!"
        colorTextTxt = [1.0,0.5,0.0]
        numRowsTxt = 6
        myListTxt = txlegalnames

    else:
        '''Si no, muestra un mensaje informando de que no ha encontardo sgs erroneos y
        cambia los valores de la variables de UI para mostrar los textos en diferenete color'''
        labelChkTxt =  "Root path, Name convention and Extension OK !!"
        colorTextTxt = [0.0,1.0,0.0]
        numRowsTxt= 1
def showError():
    '''Mostramos una venta de error si no existe ningun nodo principal en la escena'''

    cmds.confirmDialog( title='Warning', message = "There is any asset to analyze!!", icon = "information", button=['OK'] )


def runButtonPush(*args):

    #Delete window if exist
    ''' Boton paar reiniciar el chequeo,
    borramos la ventana si ya existe
    y ejecutamos de nuevo la diagnosis de la escena'''

    if (cmds.window("checkShadWindow", exists = True)):
        cmds.deleteUI("checkShadWindow")

    '''Llama a la ejecucion de nuevo del script'''

    cmds.evalDeferred('scs.createUI()')
def closelButtonPush(*args):
    '''Boton para cerrar la ventana,
    borramos la ventana de UI'''

    cmds.deleteUI("checkShadWindow")

def selMats():
    '''
    esta es la funcion que se ejecuta
    al seleccionar un item de la lista (scrollist)de shaders
    '''
    someListMats = cmds.textScrollList( "myListObjMats", q=True, si=True)
    print someListMats

    '''selecciona en la escena el item seleccionado de la lista'''

    cmds.select(someListMats)
def selSG():
    '''
    esta es la funcion que se ejecuta
    al seleccionar un item de la lista (scrollist)de shaders
    '''
    someListSG = cmds.textScrollList( "myListObjSG", q=True, si=True)
    print someListSG

    '''selecciona en la escena el item seleccionado de la lista'''

    cmds.select(someListSG)
def selTxt():
    '''
    esta es la funcion que se ejecuta
    al seleccionar un item de la lista (scrollist)de texturas
    '''
    someListTxt = cmds.textScrollList( "myListObjTxt", q=True, si=True)
    print someListTxt

    '''selecciona en la escena el item seleccionado de la lista'''

    cmds.select(someListTxt)

def createUI():
    '''Esta funcion crea la UI'''
    global allNodes
    try:
        allNodes = cmds.listRelatives('geo', parent = True) # Contiene lso objetos en el root de la escena
        print allNodes[0]
        global childNode, rootNode, rootNodes, partNodes, labelChkStr, cameras
        rootNodes = cmds.ls( assemblies = True )
        cameras = cmds.listCameras()
        for cam in cameras:
            rootNodes.remove(cam)
        rootNode = cmds.listRelatives( rootNodes[0], fullPath = True)
        childNode = cmds.listRelatives( rootNode[0], fullPath = True)
        partNodes = cmds.listRelatives( childNode[0], fullPath = True)
    except:
        showError()
        sys.exit()

    '''Borra la ventana si ya existe una y ejecutamos la funcion para chequear tetxuras'''

    if (cmds.window("checkShadWindow", exists = True)):
        cmds.deleteUI("checkShadWindow")

    '''Crea la ventana UI'''
    checkMats()
    checkSG()
    checkTexturesSG()

    chWindowUI = cmds.window("checkShadWindow", title = "Shadding Sanity Checks",
                nestedDockingEnabled = True,
                widthHeight = (400,300),
                sizeable = True,
                resizeToFitChildren = True,
                dockCorner = ("topRight","right"))
    cmds.scrollLayout(
	    horizontalScrollBarThickness=8,
	    verticalScrollBarThickness=8,
        childResizable = True,
        parent = chWindowUI)

    #################################

    # Begin ANALITICS
    print allNodes
    rcLayout = cmds.rowColumnLayout( parent = chWindowUI )
    cmds.text("ANALITICS", font = "boldLabelFont", height=30, wordWrap=1, parent = rcLayout )
    cmds.textFieldGrp( label="Asset Name: ", text=str(allNodes[0]), parent = rcLayout)
    cmds.textFieldGrp( label="Errors in Shaders: ", text=str(len(legalnames)), parent = rcLayout)
    cmds.textFieldGrp( label="Errors in ShaderEngines: ", text=str(len(sglegalnames)), parent = rcLayout)
    cmds.textFieldGrp( label="Errors in texture paths: ", text=str(len(txlegalnames)), parent = rcLayout)
    # Ends ANALITICS

    #################################

    # Begin Materials panellayout
    cmds.text (str(labelChkMats),
        align = "left",
        font = "boldLabelFont",
        backgroundColor = colorTextMats)
    cmds.textScrollList("myListObjMats",
        sc = selMats,
        numberOfRows = numRowsMats,
        allowMultiSelection = True,
        append = myListMats,
        parent = rcLayout)
    # Ends Materials panellayout

    #################################

    # Begin Shading Engines panellayout
    cmds.text (str(labelChkSG),
        align = "left",
        font = "boldLabelFont",
        backgroundColor = colorTextSG)
    cmds.textScrollList("myListObjSG",
        sc = selSG,
        numberOfRows = numRowsSG,
        allowMultiSelection = True,
        append = myListSG,
        parent = rcLayout)
    # Ends Shading Engines panellayout

    #################################

    # Begin root paths panellayout
    cmds.text (str(labelChkTxt),
        align = "left",
        font = "boldLabelFont",
        backgroundColor = colorTextTxt)
    cmds.textScrollList("myListObjTxt",
        sc = selTxt,
        numberOfRows = numRowsTxt,
        allowMultiSelection = True,
        append = myListTxt,
        parent = rcLayout)
    # Ends root paths panellayout

    cmds.rowLayout( numberOfColumns = 2, rowAttach =(1, "bottom",0))

    cmds.select(deselect = True, clear = True)
    cmds.setParent( '..' )
    cmds.button( label='Run Diagnosis', command = runButtonPush )
    cmds.button( label='Close', command = closelButtonPush )
    cmds.showWindow("checkShadWindow")
