import json 
import os 
import shutil 
import maya.cmds as cmds 
import playblasterClass 
from Framework.lib.ext_lib import shotgun_api3 as sapi
from Framework.plugins.dependency_uploader.uploader_window import UploaderBackgroundWidget 
from Framework.plugins.file_manager.settings import CustomSettings

 
 
 
def sendToCheck(filePath): 
 
    userCheck = cmds.confirmDialog(db='ok', b= ['ok', 'cancel'], cb='cancel', t="Warning: ", m="it's about to send playblast and scene to review, \nThe scene will be saved, are you sure??") 
    if userCheck == 'ok': 
        fileInfo = pipeInfo()
        sceneFullName = fileInfo['folder'] + fileInfo['fileName'] + fileInfo['extension']    
        chkFullName = getPaths(description=fileInfo['description'], fileType='scene', prodState='chk') 
        cmds.file(save=True) 
        shutil.copy(sceneFullName, chkFullName) 
        sendToDropbox([filePath, chkFullName],4) 

        createShotgunVersion(shotName=fileInfo['seq'] + '.' + fileInfo['shot'], movieFilePath= filePath, description=None, department='Animation', shotgunWeb = "https://esdip.shotgunstudio.com", project = 'b&m2')
 
    else: 
        print 'send to review canceled',
     
 
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

 
def createShotgunVersion(shotName, movieFilePath, description, department='Animation', shotgunWeb = "https://esdip.shotgunstudio.com", project = 'b&m2'):
    settings = CustomSettings("BM2", "FileManager")
    userName=settings["login"]
    
    try:
        loginPassword=settings["password"]
        sg = sapi.Shotgun(shotgunWeb, 
                           login=userName, 
                           password=loginPassword) 
                           
        shotgunProjectInfo = sg.find_one("Project", [['name', 'is', project]])  
    
    except:
        loginPassword=settings.value('password').rstrip()
        sg = sapi.Shotgun(shotgunWeb, 
                           login=userName, 
                           password=loginPassword) 
                           
        shotgunProjectInfo = sg.find_one("Project", [['name', 'is', project]])  
        

    shotInfoFilters = [ ['project', 'is', {'type': 'Project','id': shotgunProjectInfo['id']}],
                ['code', 'is', shotName] ]
    shotgunShotInfo = sg.find_one('Shot', shotInfoFilters)
    
    taskInfoFiltersfilters = [ ['project', 'is', {'type': 'Project', 'id': shotgunProjectInfo['id']}],
                ['entity', 'is',{'type':'Shot', 'id': shotgunShotInfo['id']}],
                ['content', 'is', department] ]
    shotgunTaskInfo = sg.find_one('Task', taskInfoFiltersfilters)

    userInfofilters = [ ['login', 'is', userName] ]
    shotgunUserInfo = sg.find_one('HumanUser', userInfofilters)



    previousVersionsFilters = [['entity', 'is', {'type': 'Shot', 'id': shotgunShotInfo['id']}],
              ['sg_task', 'is', {'type': 'Task', 'id': shotgunTaskInfo['id']}],
              ['user', 'is', {'type': 'HumanUser', 'id': shotgunUserInfo['id']}]
              ]
    previousVersionsFields = [
        'id',
        'code',
        'user',
        ]

    previousVersionsFilterPresets = [ {
        'preset_name': 'LATEST',
        'latest_by': 'ENTITIES_CREATED_AT'
    } ]

    userLatestVersion = sg.find_one('Version', previousVersionsFilters, previousVersionsFields, additional_filter_presets=previousVersionsFilterPresets)
    if userLatestVersion:
        versionName=incrementalName(userLatestVersion['code'])
    else:
        versionName=os.path.basename(movieFilePath)


    versionFilters = { 'project': {'type': 'Project','id': shotgunProjectInfo['id']},
                       'description': 'version to review',
                       'sg_status_list': 'rev',
                       'entity': {'type': 'Shot', 'id': shotgunShotInfo['id']},
                       'sg_task': {'type': 'Task', 'id': shotgunTaskInfo['id']},
                       'code': versionName,
                       'user': {'type': 'HumanUser', 'id': shotgunUserInfo['id']} }
    shotgunVersionInfo = sg.create('Version', versionFilters)
    
    fileUploaded =sg.upload("Version", shotgunVersionInfo['id'], movieFilePath,'sg_uploaded_movie')
 

    relatedNoteFilters = [['subject','contains', 'SEGUIMIENTO AN'],
                         ['tasks', 'is', {'type': 'Task', 'id': shotgunTaskInfo['id']}]]
           
    noteFields = ['id','subject','note_links']
    relatedNote= sg.find('Note', relatedNoteFilters , noteFields)[0]
    relatedNote['note_links'].append({'type': 'Version', 'id': shotgunVersionInfo['id'], 'name': versionName})

    noteLinksData= {'note_links':relatedNote['note_links']}

    sg.update('Note',relatedNote['id'],noteLinksData)


    print 'new version was created on shotgun',

 
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
        self.file_path= os.path.dirname(playblasterClass.__file__)+'/playblasterValues.json' 
 
 
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

