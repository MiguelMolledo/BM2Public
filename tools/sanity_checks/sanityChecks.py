# Developer: JMedina
# Version: 0.8
# Description: The scripts check all scene and geometry
# to find not allowed nodes in the publishing process.
# Checks geometry integrity showing with faces or edges
# which can provoque errors in renderprocess.

#########################################
##SANITY CHECKS FOR PROPS AND ELLEMENTS##
#########################################

try:
    import maya.mel as mel
    import maya.cmds as cmds
    import re
except Exception as e:
    print e
    print "IF its executed outsite of maya this imports fails"
#Declaring some variables
#def varDeclaration():

myListObj = ""

def checkStructure():
    # Checking Root Structure
    '''En esta funcion chequeo que la estructura en la escena y del propia escena sea la correcta,
    es decir que contenga los nulls geo, basemesh debajo del nombre del asset'''
    global childNode    # variable que contiene el path de el nodo principal |gato|geo|basemesh
    global rootNode     # variable que contiene el path de el nodo principal |gato|geo
    global rootNodes    # contiene la lista de objetos en el root de la esecna
    global labelChkStr, myListStr, colorTextStr, numRowsStr    # variables para configurar el panel de estructura en la UI
    global cameras      # variable para las camaras de la escena
    rootNodes = cmds.ls( assemblies = True )     # variable con la lista de objetos de la escena

    '''Se comprueba que solo exista un root null en la escena obviando las camaras'''

    cameras = cmds.listCameras()
    for cam in cameras:
        rootNodes.remove(cam)

    '''Compruebo que la estructura del root es correcta'''
    if len(rootNodes) == 0:
        # cmds.deleteUI("myWindow")
        showError()
        exit()

    else:
        rootNode = cmds.listRelatives( rootNodes[0], fullPath = True)
        childNode = cmds.listRelatives( rootNode[0], fullPath = True)

        '''Preparo las opcinoes de interfaz dependiendo de si es correcta o no la estructura'''

        if len(rootNodes) != 1:
            labelChkStr =  "Checking Structure: Too many root nodes!!"
            myListStr = rootNodes
            colorTextStr = [1.0,0.5,0.0]
            numRowsStr = 6
        elif "|geo|basemesh" not in childNode[0]:
            labelChkStr =  "Checking Structure: Revise asset hierarchy structure!!"
            myListStr = childNode
            colorTextStr = [1.0,0.5,0.0]
            numRowsStr = 6
        else:
            labelChkStr =  "Checking Structure: Structure is OK!!"
            myListStr = []
            colorTextStr = [0.0,1.0,0.0]
            numRowsStr = 1

def checkRefs():
    # Checking Refs
    '''Compruebo que la escena no contiene ninguna referencia cargada'''

    global labelChkRefs, myListRefs, colorTextRefs, numRowsRefs, references
    myListRefs = []
    '''Leemos todas las referencias de la escena si existe alguna'''
    references = cmds.file(query = True, reference = True)
    if len(references) != 0:
        labelChkRefs =  "Checking References: References found in scene!!"
        myListRefs = references
        colorTextRefs = [1.0,0.5,0.0]
        numRowsRefs = 6
    else:
        labelChkRefs =  "Checking References: Free of references!!"
        colorTextRefs = [0.0,1.0,0.0]
        numRowsRefs = 1

def checkgeo():
    # Checking Unicodecaracters in names, geo suffix, catmulkCrarks attributes, transformations, contruct histrory
    '''En esta funcion se compruban varias cosas relativas a la geometria, caracteres ilegales en el nombre,
    sufijos erroneos, si contienen keyframes en algun atributo, si los catmuls son los corrcetos,
    si las transformaciones estan en (0,0,0), si mantienen el historico de construccion,
    si contienen intermediate objects'''

    global geoNodes # Variable para guardar las meshes de la escena
    '''Variables para configurar los paneles del UI'''
    global labelChkSuffix, myListSuffix, colorTextSuffix, numRowsSuffix
    global labelChkCatmul, myListCatmul, colorTextCatmul, numRowsCatmul
    global labelChkTransf, myListTransf, colorTextTransf, numRowsTransf
    global labelChkHist, myListHist, colorTextHist, numRowsHist
    global labelChkInto, myListInto, colorTextInto, numRowsInto
    global labelChkIleg, myListIlle, colorTextIlle, numRowsIlle
    global labelChkKeys, myListKeys, colorTextKeys, numRowsKeys
    '''Variables para guardar el objeto selecionado en las scrolllist de los paneles del UI'''
    global someListStr, someListSuffix, someListCatmul, someListTransf
    '''Variables para capturar los valores del de los catmul'''
    global catmulIter, catmulType, legalnames, keys
    '''Iniciamos las listas con los objetos que no pasan el check'''
    myListSuffix = []
    myListCatmul = []
    myListTransf = []
    myListHist = []
    myListInto = []
    myListIlle = []
    myListKeys = []
    legalnames = []
    geoNodes = cmds.ls( geometry = True, noIntermediate = False )
    '''Ignoramos la rama de rig'''
    for node in geoNodes:
        longName = cmds.ls(node, long = True )
        if '|rig|' in longName[0]:
            geoNodes.remove(str(node))

    '''Iteramos los objetos de la escena'''

    for geonode in geoNodes:

        '''Comprobamos que no contengan ningun caracter no permitido, caracteres especiales y numeros. 
        En cualquiera de las comprobaciones de este script se configura el interfaz para el resultado muestre con una lista 
        con lso objetos erroneos encontrados y un mensaje de error en el caso de que encuentre ualgun fallo, 
        y si es correcto no mostrara nada simplemente un mensaje diciendo que la fase comprobada es correcta'''

        # Checking node containing numbers
        geoNodeTransf = cmds.listRelatives( geonode, fullPath = True, parent = True )
        if re.findall('[0-9]+',geonode):
            legalnames.append(geonode)
        if re.findall('[0-9]+',geoNodeTransf[0]):
            legalnames.append(geoNodeTransf[0])
        # Find Illegal Names
        if len(legalnames) != 0:
            labelChkIleg = "Checking Illegal Names: Revise node names!!"
            myListIlle = legalnames
            colorTextIlle = [1.0,0.5,0.0]
            numRowsIlle = 6
        else:
            labelChkIleg = "Checking Illegal Names: names OK!!"
            colorTextIlle = [0.0,1.0,0.0]
            numRowsIlle = 1

        '''Desde aqui comenzamos a comprobar otros aspectos, uso un try para comprobar que el nodo checkeado 
        no contiene caracteres especiales, si no es capaz de capturarlo porque que contiene algun caracter 
        especial lo anade a la lista de de nodos con caracteres prohibidos'''

        try:

            # Checking geo suffix
            '''Se chequean los sufijos , es decir, que las geometrias contengan el sufijo "_geo_"'''
            if geonode.find("_geo_") == -1:
                labelChkSuffix = "Checking Suffixes: Missing suffix!!"
                myListSuffix.append(geonode)
                colorTextSuffix = [1.0,0.5,0.0]
                numRowsSuffix = 6
            elif geonode.find("_ctl_") == -1:
                labelChkSuffix = "Checking Suffixes: Missing suffix!!"
                myListSuffix.append(geonode)
                colorTextSuffix = [1.0,0.5,0.0]
                numRowsSuffix = 6
            else:
                labelChkSuffix = "Checking Suffixes: Suffixes OK!!"
                colorTextSuffix = [0.0,1.0,0.0]
                numRowsSuffix = 1

            # Checking keyframes
            '''Se comprueba que ningun elemento de la escena este aniamado o contenga key frames'''
            geoNodeTransf = cmds.listRelatives( geonode, parent=True, fullPath = True )
            keys =  cmds.listConnections(geoNodeTransf, type = "animCurve")

            if keys:
                labelChkKeys = "Checking keyframes: Animation curves found!!"
                myListKeys.extend(keys)
                colorTextKeys = [1.0,0.5,0.0]
                numRowsKeys = 6
            elif not myListKeys:
                labelChkKeys = "Checking keyframes: No keyframes!!"
                colorTextKeys = [0.0,1.0,0.0]
                numRowsKeys = 1

            # Checking catmulCrarks attributes
            '''Se comprubas que los catmuls esten en el rango perimitido,
             para ello comprobamos que el plugin de arnold esta cargado, 
             de no estarlo nos avisa de ello en el panel correspondiente'''
            listPlugs = cmds.pluginInfo( query=True, listPlugins=True )
            if 'mtoa' not in listPlugs:
                labelChkCatmul = "Cannot check Catmuls: Load PLUGIN!!"
                colorTextCatmul = [1.0,0.5,0.0]
                numRowsCatmul = 1
            else:
                catmulType = cmds.getAttr(str(geonode) + ".aiSubdivType")
                catmulIter = cmds.getAttr(str(geonode) + ".aiSubdivIterations")
                catmulPixer = cmds.getAttr(str(geonode) + ".aiSubdivPixelError")
                if catmulType != 1 or catmulPixer > 1 or catmulIter > 2 or catmulIter < 1:
                    labelChkCatmul = "Checking Catmuls: Revise Catmuls!!"
                    myListCatmul.append(geonode)
                    colorTextCatmul = [1.0,0.5,0.0]
                    numRowsCatmul = 6
                else:
                    labelChkCatmul = "Checking Catmuls: Catmuls OK!!"
                    colorTextCatmul = [0.0,1.0,0.0]
                    numRowsCatmul = 1


            # Checking geoemetry transforms
            '''Se comprueba que los nodos no tengan transformaciones aplicadas, es decir que todas las traslaciones, 
            escalas, rotaciones, y shears esten en (0,0,0)'''

            geoNodeTransf = cmds.listRelatives( geonode, parent=True, fullPath = True )
            mNode = cmds.xform(str(geoNodeTransf[0]), q = True, matrix = True)
            matrixDeafult = [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0]

            if mNode != matrixDeafult :
                print geonode, geoNodeTransf, mNode
                myListTransf.append(geoNodeTransf[0])

            if len(myListTransf) != 0:
                labelChkTransf = "Checking Transforms: Revise Transforms!!"
                colorTextTransf = [1.0,0.5,0.0]
                numRowsTransf = 6
            else:
                labelChkTransf = "Checking Transforms: Transforms OK!!"
                colorTextTransf = [0.0,1.0,0.0]
                numRowsTransf = 1

            # TODO Checking nulls transforms, ahora mismo solo comprueba las geometias pero no los nulls (grupos)

            # Find objects with history
            '''Comprobamos que los objetos no contengan historico de construccion'''

            cH = cmds.listRelatives( geonode, allParents = True, allDescendents = True)
            if len(cH) >= 2:
                labelChkHist = "Checking History: Revise History!!"
                myListHist.append(geonode)
                colorTextHist = [1.0,0.5,0.0]
                numRowsHist = 6
            else:
                labelChkHist = "Checking History: meshes OK!!"
                colorTextHist = [0.0,1.0,0.0]
                numRowsHist = 1

            # Find objects with intermediate objects
            '''Comprobamos que los objetos no contengan inermediate objects de alguna operacion anterior, 
            suele ocurrir con los binds, y shapes creo recordar.'''

            if len(cmds.ls( geonode, intermediateObjects = True)) != 0:
                labelChkInto = "Checking Intermediate Objects: Revise Intermediate Objects!!"
                myListInto.append(geonode)
                colorTextInto = [1.0,0.5,0.0]
                numRowsInto = 6
            else:
                labelChkInto = "Checking Intermediate Objects: meshes OK!!"
                colorTextInto = [0.0,1.0,0.0]
                numRowsInto = 1

        except:
            legalnames.append(geonode)
            continue

def checkUnecesarySceneNodes():
    # Checking if exists Lights, Cameras, Shaders, textures, Display Layers, Render Layers, etc
    '''Comprobamos que si existen nodos inncesarios ccomo pueden Luces, Camaras, Materiales, Texturas,
    Display Layers, Render Layers, etc'''

    global sceneLigNodes, sceneCamNodes, sceneShaNodes, sceneTexNodes, sceneDlayNodes, sceneRlayNodes
    global labelChkUnne, myListUnne, colorTextUnne, numRowsUnne
    myListUnne = []
    sceneLigNodes = cmds.ls(type="light")
    sceneCamNodes = cmds.ls(type="camera", l=True)
    startup_cameras = [camera for camera in sceneCamNodes if cmds.camera(cmds.listRelatives(camera,
                                                                     parent=True)[0],
                                                                     startupCamera=True, q=True)]
    non_startup_cameras = list(set(sceneCamNodes) - set(startup_cameras))
    sceneShaNodes = cmds.ls(materials = True)
    sceneShaNodes.remove('lambert1')
    sceneShaNodes.remove('particleCloud1')
    sceneTexNodes = cmds.ls(textures = True)
    sceneDlayNodes = cmds.ls(type="displayLayer")
    sceneDlayNodes.remove("defaultLayer")
    sceneRlayNodes = cmds.ls(type="renderLayer", l=True)
    sceneRlayNodes.remove("defaultRenderLayer")
    if len(sceneLigNodes) != 0 or \
        len(non_startup_cameras) != 0 or \
        len(sceneShaNodes) != 0 or \
        len(sceneTexNodes)!= 0 or \
        len(sceneDlayNodes) != 0 or \
        len(sceneRlayNodes) != 0:
        labelChkUnne = "Checking unnecesary nodes: Revise useless nodes!!"
        myListUnne.extend(sceneLigNodes)
        myListUnne.extend(non_startup_cameras)
        myListUnne.extend(sceneShaNodes)
        myListUnne.extend(sceneTexNodes)
        myListUnne.extend(sceneDlayNodes)
        myListUnne.extend(sceneRlayNodes)
        colorTextUnne = [1.0,0.5,0.0]
        numRowsUnne = 6
    else:
        labelChkUnne = "Checking unnecesary nodes: No Nodes!!"
        colorTextUnne = [0.0,1.0,0.0]
        numRowsUnne = 1

# TODO Checking UVs, he encontrado una herramienta ya hecha en internet no la he anadido
# porque lleva bastante tiempo ejecutarla dependiendo de la cantidad de poligonos
#def checkUvsNodes():

def checkMorphologyNodes():
    # Check morphology and cleanup
    '''Comprobamos la morfologia de las meshes , facetas con mas de 4 lados, poligonos y edges con 0 area,
    agujeros, facetas compartiendo lados , coplanares, manifolds. los errores encontrados se muestran en la lista'''

    global facesSides, facesHoles, facesNonPlanar, facesSharing, facesNonManifold, edgesZero, facesZero
    global labelChkMorph, myListMorph, colorTextMorph, numRowsMorph
    myListMorph = []
    #Faces with more than 4 sides
    facesSides = mel.eval( 'polyCleanupArgList 4 { "1","2","1","0","1","0","0","0","0","1e-005","0","1e-005","0","1e-005","0","-1","0","0" };')
    #Faces with holes
    facesHoles = mel.eval( 'polyCleanupArgList 4 { "1","2","1","0","0","0","1","0","0","1e-005","0","1e-005","0","1e-005","0","-1","0","0" };')
    #Non planar faces
    #facesNonPlanar = mel.eval( 'polyCleanupArgList 4 { "1","2","1","0","0","0","0","1","0","1e-005","0","1e-005","0","1e-005","0","-1","0","0" };')
    #Faces sharing edges, coplanar faces
    facesSharing = mel.eval( 'polyCleanupArgList 4 { "1","2","1","0","0","0","0","0","0","1e-005","0","1e-005","0","1e-005","0","-1","1","0" };')
    #Nonmanifold geometry
    facesNonManifold = mel.eval( 'polyCleanupArgList 4 { "1","2","1","0","0","0","0","0","0","1e-005","0","1e-005","0","1e-005","0","1","0","0" };')
    #Edges with zero length
    edgesZero = mel.eval( 'polyCleanupArgList 4 { "1","2","1","0","0","0","0","0","0","1e-005","1","1e-005","0","1e-005","0","-1","0","0" };')
    #Faces with zero geometry length
    facesZero = mel.eval( 'polyCleanupArgList 4 { "1","2","1","0","0","0","0","0","1","1e-005","0","1e-005","0","1e-005","0","-1","0","0" };')
    if len(facesSides) != 0 or \
        len(facesHoles) != 0 or \
        len(facesSharing) != 0 or \
        len(facesNonManifold) != 0 or\
        len(edgesZero) != 0 or\
        len(facesZero) != 0:
        #len(facesNonPlanar)!= 0 or \

        labelChkMorph = "Checking geometry morphology: Revise meshes!!"
        myListMorph.extend(facesSides)
        myListMorph.extend(facesHoles)
        #myListMorph.extend(facesNonPlanar)
        myListMorph.extend(facesSharing)
        myListMorph.extend(facesNonManifold)
        myListMorph.extend(edgesZero)
        myListMorph.extend(facesZero)
        colorTextMorph = [1.0,0.5,0.0]
        numRowsMorph = 6
    else:
        labelChkMorph = "Checking geometry morphology: Morphology OK!!"
        colorTextMorph = [0.0,1.0,0.0]
        numRowsMorph = 1

def checkDuplicates():
    # Checking Unique Names
    '''Se compruba si existen nodos con nombres duplicado solo se muestra uno de ellos,
    para encontar los demas hay que usar la herramienta de seleccion de Maya por nombre'''

    global duplicates, nodeNamesDup
    global labelChkUniq, myListUniq, colorTextUniq, numRowsUniq
    myListUniq = []
    nodeNamesDup = []
    #Find all objects that have the same shortname as another
    #We can indentify them because they have | in the name
    duplicates = [f for f in cmds.ls() if '|' in f]
    #Sort them by hierarchy so that we don't rename a parent before a child.
    duplicates.sort(key=lambda obj: obj.count('|'), reverse=True)
    if len(duplicates) != 0:
        labelChkUniq = "Checking unique names: Names duplicated found!!"
        myListUniq = duplicates
        colorTextUniq = [1.0,0.5,0.0]
        numRowsUniq = 6
    else:
        labelChkUniq = "Checking geometry morphology: Unique names OK!!"
        colorTextUniq = [0.0,1.0,0.0]
        numRowsUniq = 1

def chekUnknowNodes():
    # Checking Unknow Nodes
    '''Encuentra nodos desconocidos normalemente introducidos al ser salvadas las escenas en ordenadores
    con plugins no instalados que no se encuentran en el ordenador local'''

    global labelChkUnk, myListUnk, colorTextUnk, numRowsUnk
    global unkNodes
    myListUnk = []
    unkNodes = cmds.ls(type = "unknown")
    if len(unkNodes) != 0:
        labelChkUnk = "Checking unknown nodes: Unknown nodes found!!"
        myListUnk = unkNodes
        colorTextUnk = [1.0,0.5,0.0]
        numRowsUnk = 6
    else:
        labelChkUnk = "Checking unknown nodes: Unknown nodes not exist OK!!"
        colorTextUnk = [0.0,1.0,0.0]
        numRowsUnk = 1

'''Desde aqui estan las funciones que se dedican a contruir la interfaz tanto las acciones asignadas a los botones 
como la seleccion de los nodos en la escena al ser selecionedos en las scorlllists '''

def runButtonPush(*args):
    #Delete window if exist
    '''Borramos la ventana si ya existe y ejecutamos de nuevo la diagnosis de la escena'''

    if (cmds.window("myWindow", exists = True)):
        cmds.deleteUI("myWindow")
    #To call a Py script
    cmds.evalDeferred('sc.createUI()')

def closelButtonPush(*args):
    '''Borramos la ventana de UI'''
    cmds.deleteUI("myWindow")

# Actions on selectioin scrolllist items
'''Con estas funiones seleccionamos en las listas de los scroll list del UI
los objetos fallidos para su correcion manual por el operador '''
def selIlle():
    # Selecion de objetos con characteres no permitridos
    someListIlle = cmds.textScrollList( "myListObjIlle", q=True, si=True)
    cmds.select(someListIlle)
def selStr():
    # Selecion de objetos con la estructura erronea
    someListStr = cmds.textScrollList( "myListObj", q=True, si=True)
    cmds.select(someListStr)
def selRefs():
    # TODO Selecion de referencias, da un error al seleccionar pero no afecta al funcionamiento.
    someListRefs = cmds.textScrollList( "myListObjRefs", q=True, si=True)
    cmds.select(someListRefs)
def selSuffix():
    # Selecion de objetos con sufijos erroneos
    someListSuffix = cmds.textScrollList( "myListObjSuffix", q=True, si=True)
    cmds.select(someListSuffix)
def selKeys():
    # Selecion de objetos con animacon o que contengas key frames
    someListKeys = cmds.textScrollList( "myListObjKeys", q=True, si=True)
    cmds.select(someListKeys)
def selCatmul():
    # Selecion de objetos con atributos de catmuls no permitridos
    someListCatmul = cmds.textScrollList( "myListObjCatmul", q=True, si=True)
    cmds.select(someListCatmul)
def selTrans():
    # Selecion de objetos transformaciones no permitridos
    someListTransf = cmds.textScrollList( "myListObjTransf", q=True, si=True)
    cmds.select(someListTransf)
def selHist():
    # Selecion de objetos con historicos de construccion
    someListHist = cmds.textScrollList( "myListObjHist", q=True, si=True)
    cmds.select(someListHist)
def selInto():
    # Selecion de objetos que contienen intermediate objects ocultos
    someListInto = cmds.textScrollList( "myListObjInto", q=True, si=True)
    cmds.select(someListInto)
def selUnne():
    # Selecion de objetos innecesarios
    someListUnne = cmds.textScrollList( "myListObjUnne", q=True, si=True)
    cmds.select(someListUnne)
def selMorph():
    # Selecion de componentes , normalmente facetas de poligonos, no permitridos
    someListMorph = cmds.textScrollList( "myListObjMorph", q=True, si=True)
    cmds.select(someListMorph)
def selUniq():
    # Selecion de objetos que ya existen en la escena con el mismo nombre, solo se selciona uno de ellos
    someListUnk = cmds.textScrollList( "myListObjUniq", q=True, si=True)
    cmds.select(someListUnk)
def selUnk():
    # Selecion de objetos desconocidos en la escena
    someListUnk = cmds.textScrollList( "myListObjUnk", q=True, si=True)
    cmds.select(someListUnk)

def createUI():
    # Create UI window
    '''Creamos la interfaz tomando los datos de las comprobaciones anteriores,
    al ejecutar esta funcion se llaman a las funciones de checking anteriores
    cada panel de la interfaz esta separado un
    ############Begin....
    codigo
    codigo
    codigo
    ......
    ##########Ends.......'''

    checkStructure()
    checkRefs()
    checkgeo()
    checkUnecesarySceneNodes()
    checkMorphologyNodes()
    checkDuplicates()
    chekUnknowNodes()
    #Delete window if exist
    if (cmds.window("myWindow", exists = True)):
        cmds.deleteUI("myWindow")
    #Create list with structure
    cmds.window("myWindow", title = "Modelling Sanity Checks",
                nestedDockingEnabled = True,
                widthHeight = (300,300),
                sizeable = True,
                resizeToFitChildren = True)
    cmds.scrollLayout(
        horizontalScrollBarThickness=16,
        verticalScrollBarThickness=16)

    #################################
    # Begin ANALITICS
    cmds.rowColumnLayout()
    cmds.text("ANALITICS", font = "boldLabelFont", height=30, wordWrap=1 )
    cmds.textFieldGrp( label="Root structure: ", text=str(len(rootNodes)) + "  objects found ", editable=False , columnAlign = (1,"left"))
    cmds.textFieldGrp( label="References found: ", text=str(len(myListRefs)) + "  objects found ", editable=False , columnAlign = (1,"left"))
    cmds.textFieldGrp( label="Nodes without Suffixes: ", text=str(len(myListSuffix)) + "  objects found ", editable=False, columnAlign = (1,"left") )
    cmds.textFieldGrp( label="Illegal Chars: ", text=str(len(myListIlle)) + "  objects found ", editable=False, columnAlign = (1,"left") )
    cmds.textFieldGrp( label="Nodes with keys: ", text=str(len(myListKeys)) + "  objects found ", editable=False, columnAlign = (1,"left") )
    cmds.textFieldGrp( label="Erroneus Catmuls: ", text=str(len(myListCatmul)) + "  objects found ", editable=False, columnAlign = (1,"left") )
    cmds.textFieldGrp( label="Erroneus transforms: ", text=str(len(myListTransf)) + "  objects found ", editable=False, columnAlign = (1,"left") )
    cmds.textFieldGrp( label="Nodes with History: ", text=str(len(myListHist)) + "  objects found ", editable=False, columnAlign = (1,"left") )
    cmds.textFieldGrp( label="Nodes with Interm. Objs.: ", text=str(len(myListInto)) + "  objects found ", editable=False, columnAlign = (1,"left") )
    cmds.textFieldGrp( label="Useless nodes.: ", text=str(len(myListUnne)) + "  objects found ", editable=False, columnAlign = (1,"left") )
    cmds.textFieldGrp( label="Erroneus morphology meshes: ", text=str(len(myListMorph)) + "  objects found ", editable=False, columnAlign = (1,"left") )
    cmds.textFieldGrp( label="Not unique nodes: ", text=str(len(myListUniq)) + "  objects found ", editable=False, columnAlign = (1,"left") )
    cmds.textFieldGrp( label="Unknow nodes: ", text=str(len(myListUnk)) + "  objects found ", editable=False, columnAlign = (1,"left") )
    # Ends analitics
    #################################
    column = cmds.columnLayout(adjustableColumn = 1 )
    # Begin Illegal names panellayout
    cmds.text (str(labelChkIleg),
        align = "left",
        font = "boldLabelFont",
        backgroundColor = colorTextIlle)
    cmds.textScrollList("myListObjIlle",
        sc = selIlle,
        numberOfRows = numRowsIlle,
        allowMultiSelection = True,
        append = myListIlle)
    # Ends Illegal names panellayout
    #################################
    # Begin Structure panellayout
    cmds.text (str(labelChkStr),
        align = "left",
        font = "boldLabelFont",
        backgroundColor = colorTextStr)
    cmds.textScrollList("myListObj",
        sc = selStr,
        numberOfRows = numRowsStr,
        allowMultiSelection = True,
        append = myListStr)
    # Ends Structure panellayout
    #################################
    # Begin Refs panellayout
    cmds.text (str(labelChkRefs),
        align = "left",
        font = "boldLabelFont",
        backgroundColor = colorTextRefs)
    cmds.textScrollList("myListObjRefs",
        sc = selRefs,
        numberOfRows = numRowsRefs,
        allowMultiSelection = True,
        append = myListRefs)
    # Ends Structure panellayout
    #################################
    # Begins Suffix panellayout
    cmds.text (str(labelChkSuffix),
        align = "left",
        font = "boldLabelFont",
        backgroundColor = colorTextSuffix)
    cmds.textScrollList("myListObjSuffix",
        sc = selSuffix,
        numberOfRows = numRowsSuffix,
        allowMultiSelection = True,
        append = myListSuffix)
    # Ends Suffix panellayout
    #################################
    # Begins keys panellayout
    cmds.text (str(labelChkKeys),
        align = "left",
        font = "boldLabelFont",
        backgroundColor = colorTextKeys)
    cmds.textScrollList("myListObjKeys",
        sc = selKeys,
        numberOfRows = numRowsKeys,
        allowMultiSelection = True,
        append = myListKeys)
    # Ends keys panellayout
    #################################
    # Begins Catmul panellayout
    cmds.text (str(labelChkCatmul),
        align = "left",
        font = "boldLabelFont",
        backgroundColor = colorTextCatmul)
    cmds.textScrollList("myListObjCatmul",
        sc = selCatmul,
        numberOfRows = numRowsCatmul,
        allowMultiSelection = True,
        append = myListCatmul)
    # Ends Catmul panellayout
    #################################
    # Begins transforms panellayout
    cmds.text (str(labelChkTransf),
        align = "left",
        font = "boldLabelFont",
        backgroundColor = colorTextTransf)
    cmds.textScrollList("myListObjTransf",
        sc = selTrans,
        numberOfRows = numRowsTransf,
        allowMultiSelection = True,
        append = myListTransf)
    # Ends transforms panellayout
    #################################
    # Begins history panellayout
    cmds.text (str(labelChkHist),
        align = "left",
        font = "boldLabelFont",
        backgroundColor = colorTextHist)
    cmds.textScrollList("myListObjHist",
        sc = selHist,
        numberOfRows = numRowsHist,
        allowMultiSelection = True,
        append = myListHist)
    # Ends history panellayout
    #################################
    # Begins intermediate objects panellayout
    cmds.text (str(labelChkInto),
        align = "left",
        font = "boldLabelFont",
        backgroundColor = colorTextInto)
    cmds.textScrollList("myListObjInto",
        sc = selInto,
        numberOfRows = numRowsInto,
        allowMultiSelection = True,
        append = myListInto)
    # Ends intermediate objects panellayout
    #################################
    # Begins unnecesary nodes panellayout
    cmds.text (str(labelChkUnne),
        align = "left",
        font = "boldLabelFont",
        backgroundColor = colorTextUnne)
    cmds.textScrollList("myListObjUnne",
        sc = selUnne,
        numberOfRows = numRowsUnne,
        allowMultiSelection = True,
        append = myListUnne)
    # Ends unnecesary nodes panellayout
    #################################
    # Begins morphology nodes panellayout
    #cmds.paneLayout(configuration = "quad")
    cmds.text (str(labelChkMorph),
        align = "left",
        font = "boldLabelFont",
        backgroundColor = colorTextMorph)
    #cmds.text ("")
    cmds.textScrollList("myListObjMorph",
        sc = selMorph,
        numberOfRows = numRowsMorph,
        allowMultiSelection = True,
        append = myListMorph)
    '''cmds.textScrollList("myListObjMorph2",
        sc = selMorph,
        numberOfRows = numRowsMorph,
        allowMultiSelection = True,
        append = myListMorph)
    '''
    # Ends morphology nodes panellayout
    #################################
    # Begins Unique nodes panellayout
    cmds.text (str(labelChkUniq),
        align = "left",
        font = "boldLabelFont",
        backgroundColor = colorTextUniq)
    cmds.textScrollList("myListObjUniq",
        sc = selUniq,
        numberOfRows = numRowsUniq,
        allowMultiSelection = True,
        append = myListUniq)
    # Ends Unique nodes panellayout
    #################################
    # Begins unknown nodes panellayout
    cmds.text (str(labelChkUnk),
        align = "left",
        font = "boldLabelFont",
        backgroundColor = colorTextUnk)
    cmds.textScrollList("myListObjUnk",
        sc = selUnk,
        numberOfRows = numRowsUnk,
        allowMultiSelection = True,
        append = myListUnk)
    # Ends unknown nodes panellayout
    #################################

    cmds.rowLayout( numberOfColumns = 2, rowAttach =(1, "bottom",0))
    cmds.button( label='Run Diagnosis', command = runButtonPush )
    #cmds.button( label='Del. History', command = delButtonPush )
    cmds.button( label='Close', command = closelButtonPush )
    cmds.select(deselect = True, clear = True)
    cmds.showWindow("myWindow")

def showError():
    '''Mostramos una venta de error si no existe ningun nodo principal en la escena'''

    cmds.confirmDialog( title='Warning', message = "Please, load a scene or create an asset to evaluate!", icon = "information", button=['OK'] )
