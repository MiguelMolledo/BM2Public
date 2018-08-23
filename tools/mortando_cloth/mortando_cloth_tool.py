import os
from Framework.lib.gui_loader import gui_loader
from Framework.lib.ui.qt.QT import QtCore, QtWidgets, QtGui

form, base = gui_loader.load_ui_type(os.path.join(os.path.dirname(__file__), "ui", "mortando_cloth_ui.ui"))

import os
from maya import mel
from maya import cmds
import shotgun_api3 as sapi
from Framework.plugins.dependency_uploader.uploader_window import UploaderBackgroundWidget
from Framework.plugins.file_manager.filetypes.folder import Folder

class MortandoCloth(form, base):
    shotSeq = None
    shotNumber = None
    seqName = None
    shotInfo = None
    shot_assets= None
    shot_chars = None
    shot_props = None
    shots = []
    sg = None
    cut_in = None
    cut_out = None
    cam_shake = False
    escenario = None
    
    def __init__(self, parent=None):
        super(MortandoCloth, self).__init__(parent)
        self.setupUi(self)
        self.logInShotgun()
        self.shotgunInfo()
        self.connectSignals()


    def connectSignals(self):
        print ("KK")
        self.aceptarButton.clicked.connect(self.publishShot)
        self.sequenceButton.currentIndexChanged.connect(self.refreshShotInfo)
        self.btn_reset_simulation.clicked.connect(self.reset)
        self.btn_new_blendshape.clicked.connect(self.new_blendshape)
        self.btn_export_wip.clicked.connect(self.export_wip)
        self.btn_export_out.clicked.connect(self.export_out)
    
    def export_wip (self):
        self._splitShotName()
        mel = "-frameRange {0} {1} -uvWrite -writeVisibility -dataFormat ogawa -root |cloth_rig|output|out_export|mortando|geo -file P:/bm2/seq/{2}/sho/{3}/cloth/wip/bm2_seqsho_seq_{2}_sho_{3}_cloth_mortando_main_wip.abc". format(0, self.cut_out, self.shotNumber, self.seqName)
        print mel
        cmds.AbcExport (j=mel)
        
    def export_out (self):
        self._splitShotName()
        mel = "-frameRange {0} {1} -uvWrite -writeVisibility -dataFormat ogawa -root |cloth_rig|output|out_export|mortando|geo -file P:/bm2/seq/{2}/sho/{3}/cloth/out/bm2_seqsho_seq_{2}_sho_{3}_cloth_mortando_main_out.abc". format(0, self.cut_out, self.shotNumber, self.seqName)
        file = cmds.AbcExport (j=mel)
        file_path_list = []
        file_path_list[0] = file
        self._sendToDropbox(file_path_list, 10)
        
        
    def basic_blendshape (self):
        blendShape = cmds.blendShape("|mortando|geo", "input_connect|mortando|geo", name="anim_to_input", o="world")
        cmds.setAttr (blendShape[0]+".geo", 1)
    
    def new_blendshape (self):
        name = self.blend_shape_frame.toPlainText()
        if name:
            blendShape = cmds.blendShape("|mortando|geo", "input_connect|mortando|geo", name="anim_to_input_{0}".format(name), o="world")
            cmds.setAttr (blendShape[0]+".geo", 1)
        
    def reset (self):
        from maya import mel
        from Framework.plugins.mortando_cloth import reset_code as rc
        mel.eval(rc.code)
            
    def logInShotgun (self):
        self.sg = sapi.Shotgun("https://esdip.shotgunstudio.com",
                                  login="tdevelopment",
                                  password="BM@Developement")
    def shotgunInfo(self):
        self.sequenceButton.clear()
        shots= self.sg.find("Shot", filters=[['project','is', {'type': 'Project','id': 86}]], fields=["code", "sg_status_list"])
        for n in range (0, len(shots)):
            self.sequenceButton.addItem(shots[n]["code"])
            self.shots.append (shots[n]["code"])
        print shots
        
    def refreshShotInfo (self):
        num = self.sequenceButton.currentIndex()
        self.shotSeq = self.shots[num]
        self.shotInfo = self.sg.find("Shot", filters=[["code", "is", self.shotSeq],['project','is', {'type': 'Project','id': 86}]], fields=["code", "sg_status_list", "sg_cut_in", "sg_cut_out", "assets", "sg_camera_shake", "sg_escenario"])

        self.cut_in = self.shotInfo[0]["sg_cut_in"]
        self.cut_out = self.shotInfo[0]["sg_cut_out"]
        self.shot_assets= self.shotInfo[0]["assets"]
        self.escenario = self.shotInfo[0]["sg_escenario"]
        
        elem= list()
        self.shot_chars = list()
        self.shot_props = list()
        for n in range (0, len(self.shot_assets)):
            elem= self.sg.find('Asset', filters=[['code', "is", self.shot_assets[n]["name"]], ['project','is', {'type': 'Project','id': 86}]], fields=["code","sg_asset_type"])
            if elem[0]["sg_asset_type"] == 'Character':
                self.shot_chars.append(elem[0]["code"])
            elif elem[0]["sg_asset_type"] == 'Prop':
                self.shot_props.append(elem[0]["code"])
        
        b_mortando_find = False
        for n in range (0, len(self.shot_chars)):
            if self.shot_chars[n] == "mortando":
                b_mortando_find = True
        if b_mortando_find == False:
            raise Exception ("imbecil mortando no existe en este plano")
        
        self.charsButton.setText(str(self.shot_chars))
        self.cutInButton.setText(str(self.cut_in))
        self.cutOutButton.setText(str(self.cut_out))
        self.escenarioButton.setText(str(self.escenario))
        self.propsButton.setText(str(self.shot_props))
        
    def publishShot (self):
        cmds.file(new=True, f=True)
        self._splitShotName()
        self._importCamera()
        self._importAudio ()
        self._importEscenario ()
        self._importclothRig ()
        self._importAlembics ()
        self._renderSetting()
        self.basic_blendshape()
        self._saveShot()
        
    def _splitShotName (self):
        shotPartsList= []
        shot = self.shotSeq
        print self.shotSeq
        shotPartsList = self.shotSeq.split(".")
        self.shotNumber = shotPartsList[0]
        self.seqName = shotPartsList[1]
        print "plano numero {} y secuencia {}".format( self.shotNumber, self.seqName)
               
    def _importAudio (self):
        audio_path = "P:/BM2/seq/{0}/sho/{1}/audio/out/bm2_shoaud_seq_{0}_sho_{1}_audio_default_none_out.wav".format(self.shotNumber, self.seqName)
        self._downloadFromDropbox(audio_path)
        node = cmds.file( audio_path, reference=True)
        node = cmds.referenceQuery(node, n=True)
        cmds.setAttr ("{}.offset".format(node[0]), 76)
        cmds.playbackOptions (minTime=self.cut_in, animationStartTime=(self.cut_in-25), maxTime=self.cut_out, animationEndTime=(self.cut_out+25) )
        
    def _importEscenario (self):
        if self.escenario:
            escenarioList = []
            escenarioList = self.escenario.split("_")
            location = escenarioList[0]
            sublocation = escenarioList[1]
            location_path = "P:/BM2/loc/{0}/scn/animPrep/main/out/bm2_locscn_loc_{0}_scn_animPrep_main_{1}_none_out.ma".format(location, sublocation)
            self._downloadFromDropbox(location_path)
            node = cmds.file( location_path, reference=True, namespace=":")
    
    def _importclothRig (self):
        char_path = "P:/bm2/chr/mortando/cfx/thingHigh/cloth/out/bm2_chrcfx_chr_mortando_cfx_thingHigh_cloth_default_scene_out.ma"
        self._downloadFromDropbox(char_path)
        node = cmds.file(char_path, i=True, mnc= True)

    def _importAlembics (self):
        path = "P:/bm2/seq/{0}/sho/{1}/animation/out".format(self.shotNumber, self.seqName)
        list_abc = self.remote_files(path)
        for n in range (0, len(list_abc)):
            abc_fields = self.split_fields(list_abc[n])
            if abc_fields["extension"] == "abc":
                abc_path = path + "/" + list_abc[n]
                print "descargando {0}".format( abc_path)
                self._downloadFromDropbox(abc_path)
                node = cmds.AbcImport (abc_path, m="import" )
                self.renamer(node, abc_fields["partition"])
    
    def _importCamera (self):
        path = "P:/bm2/seq/{0}/sho/{1}/camera/out".format(self.shotNumber, self.seqName)
        list_camera = self.remote_files(path)
        for n in range (0, len(list_camera)):
            camera_fields = self.split_fields(list_camera[n])
            if camera_fields["extension"]== "ma" or camera_fields["extension"]== "mb":
                if camera_fields["layer"]== "camera":
                    camera_path = path + "/" + list_camera[n]
                    self._downloadFromDropbox(camera_path)
                    cmds.file( list_camera[n], reference=True, namespace=":")
    
    def _renderSetting (self):
        if self.cam_shake == False:
            cmds.setAttr ("defaultResolution.width", 1920)
            cmds.setAttr ("defaultResolution.height", 1080)
        elif self.cam_shake == True:
            cmds.setAttr ("defaultResolution.width", 3424)
            cmds.setAttr ("defaultResolution.height", 2202)
            
    def _saveShot (self):
        
        directory = ( "P:/BM2/seq/{0}/sho/{1}/cloth/wip/".format(self.shotNumber, self.seqName))
        try:
            os.makedirs(directory)
        except:
            pass    
        file_path_list=[]
        file_path_list.append( "P:/BM2/seq/{0}/sho/{1}/cloth/wip/bm2_shoscn_seq_{0}_sho_{1}_cfx_cloth_scene_wip.ma".format(self.shotNumber, self.seqName))
        listNodes = cmds.ls(type = 'unknown')
        cmds.delete(listNodes)
        cmds.file( rename=file_path_list[0] )
        cmds.file (save=True, type='mayaAscii', f=True)   
        self._sendToDropbox(file_path_list, 1)
        
    def _sendToDropbox(self, file_path_list, max_threads):
        uploader_background_widget = UploaderBackgroundWidget(file_path_list=file_path_list, max_threads=max_threads)
        x = uploader_background_widget.execute_upload_process()
        print x
        
    def _downloadFromDropbox (self, path):
        from Framework.plugins.dependency_loader.downloader import Downloader, DownloaderResponse
        from Framework.lib.ui.qt.QT import QtCore, QtWidgets, QtGui
        print "estamos descargando {0}".format( path)
        if os.path.isfile(path) == True:
            print "estamos dentro del if del path" + path
            print os.path.isfile(path)
        else:
            self.download_finished = False
            downloader = Downloader()
            file_list = []
            file_list.append(path)
            print file_list
            downloader.set_files_to_process(file_list)
            downloader.set_maxium_threads(1)
            downloader.on_finish_download.connect(self.on_download_finished, QtCore.Qt.QueuedConnection)
            downloader.start_download_process()
            x = 0
            while self.download_finished  == False:            
                #if os.path.isfile(path) == False:
                import time
                x = x+1
                time.sleep(10)
                if x >= 10:
                    break
                print "Downloading {}....".format(path)
                if self.download_finished:
                    break
                self.download_finished  = False
                #elif os.path.isfile(path) == True: 
                #    break

    def on_download_finished(self):
          self.download_finished  = True
          print self.download_finished, "TERMINA JODER "   
          
    def remote_files (self, path):
        path = path.replace("P:/bm2/", "P:/BM2/")
        raw_metadata = Folder(path).remote_children()
        list_files = []
        for n in range (1, len(raw_metadata)):
            list_files.append (raw_metadata[n].name)    
        return list_files
            
    def split_fields (self, file_name):
        list_fields = {}
        file_name, list_fields["extension"] =(file_name).split(".")
        list_fields["proyect"], list_fields["filetype"], list_fields["group"], list_fields["seqName"], list_fields["area"], list_fields["step"], list_fields["layer"], list_fields["partition"], list_fields["description"], list_fields["pipe"] = (file_name).split("_")                  
        return list_fields
    
    def renamer(self, node, name):
        list_mesh =cmds.listConnections(node, d=True)
        name_geo_raw =cmds.listRelatives(list_mesh[1], f=True)
        name_geo = (name_geo_raw[0]).split("|")
        group = "|" + name_geo[1]
        node_name_group = cmds.group(group, n=name)
        return node_name_group 
        
            
            
            
            
            
            
            
            
            
            
            
            