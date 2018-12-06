# -*- coding: utf-8 -*-
import os, re
from maya import cmds
from Framework.lib.gui_loader import gui_loader
from Framework.lib.ui.qt.QT import QtCore, QtWidgets, QtGui

from .  import shader_list_dialog
reload(shader_list_dialog)


form, base = gui_loader.load_ui_type(os.path.join(os.path.dirname(__file__), "ui", "select_method.ui"))


class ShaderManager(form, base):
    s_elemname      = ''
    s_pipepath      = ''
    s_file          = ''
    s_current_path  = ''
    s_mpspath       = ''
    s_ext           = ''
    b_filter        = False
    d_textures      = dict()
    l_basic_types   = ['diffuse','f0','normal','roughness','specular']
    l_avail_types   = []


    def __init__(self, parent=None):
        super(ShaderManager, self).__init__(parent)
        self.setupUi(self)
        self._initializeUI()
        self._connectSignals()



    def _initializeUI(self):
        self.le_info.setVisible(False)
        self._populate_list()

        # somewhat it ignores this designer option, so force it
        self.lw_txtarget.setAcceptDrops(False)
        self.lw_txselected.setAcceptDrops(False)
        
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)

                                                                      
    def _connectSignals(self):

        self.cb_browse.stateChanged.connect(self._manage_browsing)
        self.pb_browse.clicked.connect(self._browsedir)

        self.cb_filter.stateChanged.connect(self._manage_filtering)

        self.pb_add.clicked.connect(self._action_add_textures)
        self.pb_remove.clicked.connect(self._action_remove_textures)

        self.rb_tif.toggled.connect(self._filter_textures)

        self.pb_accept.clicked.connect(self._start_creation)
        self.pb_cancel.clicked.connect(self._cancel)


    def _populate_list(self, s_path=None, s_filter=None):

        self.lw_txtarget.clear()
        self.lw_txselected.clear()
        if not s_path:
            if self._check_scene_and_paths() and self.s_mpspath:
                # if scene and paths are ok look for textures in mps path
                self.s_current_path = self.s_mpspath
            else:
                s_msg = "La escena de maya no esta salvado o no tiene la nomenclatura correcta"
                cmds.error(s_msg)
        else:
            self.s_current_path = s_path

        b_success = self.get_textures_in_path(self.s_current_path, self.s_elemname, s_filter)
        if b_success:
            self.le_browse.setText(self.s_current_path)
            for s_texture in sorted(self.d_textures.keys()):
                self.lw_txtarget.addItem(s_texture)


        for elem in cmds.ls(type='aiStandard', l=True):
            self.lw_aiStandar.addItem(elem)


    def _action_add_textures(self):
        for o_selected in self.lw_txtarget.selectedItems():
            self.lw_txtarget.takeItem(self.lw_txtarget.row(o_selected))
            self.lw_txselected.addItem(o_selected)

            d_texture_info = self.d_textures[o_selected.text()]

            s_texture_type = d_texture_info['type']
            self.l_avail_types.append(s_texture_type)
            self.l_avail_types = list(set(self.l_avail_types))

        self.lw_txtarget.clearSelection()
        self.lw_txselected.sortItems(QtCore.Qt.AscendingOrder)
        self._manage_available_textures()


    def _action_remove_textures(self):
        for o_selected in self.lw_txselected.selectedItems():
            self.lw_txselected.takeItem(self.lw_txselected.row(o_selected))
            self.lw_txtarget.addItem(o_selected)

            d_texture_info = self.d_textures[o_selected.text()]

            s_texture_type = d_texture_info['type']
            self.l_avail_types.remove(s_texture_type)

        self.lw_txselected.clearSelection()
        self.lw_txtarget.sortItems(QtCore.Qt.AscendingOrder)
        self._manage_available_textures()


    def _manage_available_textures(self):
        l_not_there = list(set(self.l_basic_types) - set(self.l_avail_types))
        
        if l_not_there:
            s_msg = "Warning: {} no estan en la lista de seleccionados".format(l_not_there)
            self.le_info.setPlaceholderText(s_msg)
            self.le_info.setStyleSheet('background: transparent;')

            self.le_info.setVisible(True)
        else:
            self.le_info.setVisible(False)



    def _check_scene_and_paths(self):
        # pattern for maya files
        s_mayapattern = "bm2_(elm|chr)sha_(chr|elm)_([A-Za-z0-9]+)_sha_([A-Za-z0-9]+)_shading_([A-Za-z0-9]+)_([A-Za-z0-9]+)_out.ma"
        # pattern for working directory
        s_pathpattern = "P:/bm2/(elm|chr)/([A-Za-z0-9]+)/sha/([A-Za-z0-9]+)/shading/(work|wip|out)"

        s_filepath = r"{}".format(cmds.file(q=True, sn=True))
        o_found = re.search(s_pathpattern, s_filepath) 

        if s_filepath and o_found:
            self.s_elemname = o_found.group(2)
            (self.s_pipepath, self.s_file) = os.path.split(s_filepath)

            self.s_mpspath = os.path.join(os.path.dirname(self.s_pipepath), 'mps')
        else:
            s_message = 'Graba primero la escena\ncon la nomenclatura correcta\npara poder usar esta tool'
            cmds.confirmDialog( title='Error', message=s_message, button=['Ok'] )
            return False
        return True


    def get_textures_in_path(self, s_path, s_elemname, s_filter=None):
        '''
        Search and retrieve texture files for s_elemname in the directory s_path filtered by s_filter if exists
        '''
        d_text = {}
        self.d_textures.clear()
        # pattern for texture names
        # ex result:     bm2_elmsha_elm_maquinavoy_sha_high_shading_1K_diffuse_mps.1001.tif
        s_textpattern = "bm2_(elm|chr)sha_(chr|elm)_({elem1}|{elem2})_sha_([A-Za-z0-9]+)_shading_(\\dK)_([A-Za-z0-9]+)_mps".format(
                                                            elem1=s_elemname, 
                                                            elem2=s_elemname.lower())
        # Extend pattern with possible udim 
        s_textpattern =  s_textpattern +'(\.\d{4})?'
        # Extend pattern with filtering extension or all allowed extensions 
        s_textpattern =  s_textpattern + '\.{}'.format(s_filter if s_filter else '(tiff|tif|tx)')


        if os.path.exists(s_path):
            for s_elem in os.listdir(s_path):
                s_pathcomplete = os.path.join(s_path, s_elem)
                if os.path.isfile(s_pathcomplete):
                    o_found = re.search(s_textpattern, s_elem)
                    if o_found:
                        self.get_texture_info(s_elem, s_path, o_found)


        else:
            s_message = 'No existe el directorio de texturas:\n{}'.format(s_path)
            cmds.confirmDialog( title='Error', message=s_message, button=['Ok'] )

            return False

        return True if self.d_textures else False


    def get_texture_info(self, s_file, s_path, o_match):
        '''
        '''
        d_info = dict()
        s_elemname   = o_match.group(3)
        s_resolution =  o_match.group(5)
        s_texttype   =  o_match.group(6)
        s_udim       =  o_match.group(7)
        s_ext        =  o_match.group(8)

        if s_udim:
            s_file = s_file.replace(s_udim, ".<UDIM>")
        s_name = os.path.splitext(s_file)[0]

        if not s_file in self.d_textures.keys():
            d_info= {
                   'file_path' : s_path,
                   #'elem_name' : s_elemname, 
                   's_name'    : s_name, 
                   'resolution': s_resolution,
                   'type'      : s_texttype.lower(),
                   'extension' : s_ext    
                   }

            self.d_textures[s_file] = d_info


    def _manage_browsing(self, o_state):
        b_state = True if o_state == QtCore.Qt.Checked else False
        self.le_browse.setEnabled(b_state)
        self.pb_browse.setEnabled(b_state)
        if not b_state:
            self.le_browse.setText(self.s_mpspath)
            self.s_current_path =  self.s_mpspath
            if self.cb_filter.isChecked():
                self._filter_textures(self.rb_tif.isChecked())
            else:
                self._populate_list()

    def _browsedir(self):
        s_title = "Browse directory with textures"
        s_startingDirectory = self.s_mpspath if self.s_mpspath else self.s_pipepath
        l_dirs = cmds.fileDialog2(caption=s_title,  startingDirectory=s_startingDirectory, dialogStyle=2, fileMode=3)

        if l_dirs:
            self.s_current_path = l_dirs[0]
            self.le_browse.setText(self.s_current_path)
            if self.cb_filter.isChecked():
                self._filter_textures(self.rb_tif.isChecked())
            else:
                self._populate_list(self.s_current_path)

    def _manage_filtering(self, o_state):
        b_state = True if o_state == QtCore.Qt.Checked else False
        self.rb_tif.setEnabled(b_state)
        self.rb_tx.setEnabled(b_state)
        if b_state:
            self._filter_textures(self.rb_tif.isChecked())
        if not b_state:
            self._populate_list(self.s_current_path)


    def _filter_textures(self, s_state=None):
        s_filter = '(tiff|tif)' if s_state else '(tx)'
        self._populate_list(self.s_current_path, s_filter)


    def _start_creation(self):
        l_names = []
        index_sel = self.tw_tabs.currentIndex()
        if index_sel==0:
            l_tx_selected = []
            if self.lw_txselected.count() > 0:
                self.le_info.setVisible(False)
                o_names_dialog = shader_list_dialog.ShaderList( s_element=self.s_elemname)
                o_names_dialog.exec_()
                l_names = o_names_dialog.get_names()
                if l_names:

                    for i_index in range(self.lw_txselected.count()):
                        o_item_texture = self.lw_txselected.item(i_index)
                        l_tx_selected.append(o_item_texture.text())
                    # get only texture data selected
                    d_tx_selected = {tx_selected:self.d_textures[tx_selected] for tx_selected in l_tx_selected}

                    for s_name in l_names:
                        o_shader = ShaderCreation(d_tx_selected, s_name, self.s_elemname)
                        o_shader.create()

            else:
                s_message = 'Selecciona primero alguna textura para poder crear el/los nuevo/s nodos aiStandard'
                self.le_info.setPlaceholderText(s_message)
                self.le_info.setVisible(True)

        elif index_sel==1 and self.lw_aiStandar.currentItem() is not None:
            self.le_info.setVisible(False)
            s_shader_selected=self.lw_aiStandar.currentItem().text()
            l_selection = QtWidgets.QInputDialog.getText(self, self.tr("Duplicando shader"),
                                     self.tr("Introduce el nombre para nuevo el shader\nEl nombre sera:\n{}_shader_[lo que pongas]".format(self.s_elemname)))
            if l_selection[1]==True:
                s_name = l_selection[0]
                o_shader = ShaderCreation(s_name=s_name, s_elem=self.s_elemname)
                o_shader.duplicate(s_shader_selected)

        else:
            s_message = 'Selecciona la textura que quieras duplicar'
            self.le_info.setPlaceholderText(s_message)
            self.le_info.setVisible(True)

    



    def _cancel(self):
        ''' TODO:  rollback'''
        self.close()




class ShaderCreation():
    s_element_name = ''
    d_tx_data      = {}
    s_base_name    = '{elem}_shader_{desc}'
    s_sgbase_name  = '{elem}_SG_{desc}'
    l_tx           = ['diffuse','f0','normal','roughness','specular']

    def __init__(self, d_tx_selected=None, s_name=None, s_elem=None):

        self.d_tx_data = d_tx_selected
        self.s_name    = self.s_base_name.format(elem=s_elem, desc=s_name)
        self.s_sgname  = self.s_sgbase_name.format(elem=s_elem, desc=s_name)
        self.s_element_name = s_elem

    def create(self):

        # Create aiStandard and SG and connect them
        s_aishader = cmds.shadingNode('aiStandard', name=self.s_name, asShader=True)
        s_sg = cmds.sets(renderable=True, name=self.s_sgname, noSurfaceShader=True, empty=True)
        cmds.connectAttr('{}.outColor'.format(s_aishader) ,'{}.surfaceShader'.format(s_sg))
        
        # 
        cmds.setAttr("{}.Ks".format(s_aishader), 1)
        # activate fresnel to allow f0 connections
        cmds.setAttr("{}.specularFresnel".format(s_aishader), 1)

        for s_file in self.d_tx_data.keys():
            s_filepath = os.path.join(self.d_tx_data[s_file]['file_path'], s_file)
            # first create texture file node  
            s_filenode = self.create_texture_node(s_name=self.d_tx_data[s_file]['s_name'], s_file=s_filepath)

            cmds.setAttr("{}.uvTilingMode".format(s_filenode), 3) #  set this for all textures

            s_type = self.d_tx_data[s_file]['type']
            s_ext = self.d_tx_data[s_file]['extension']


            if s_ext == 'tx':
                # If in tx mode set sRGB to all
                cmds.setAttr('{}.colorSpace'.format(s_filenode), 'sRGB', type='string')

            elif s_ext == 'tif' and s_type in ['f0', 'normal', 'roughness']:
                # If in tiff mode set f0,Normal,Roughness to RAW
                cmds.setAttr('{}.colorSpace'.format(s_filenode), 'Raw', type='string')

            # Different connections depending of texture type
            if s_type == 'diffuse':
                cmds.connectAttr('{}.outColor'.format(s_filenode) ,'{}.color'.format(s_aishader))

            elif s_type == 'specular':
                cmds.connectAttr('{}.outColor'.format(s_filenode) ,'{}.KsColor'.format(s_aishader))
                
            elif s_type == 'f0':
                cmds.connectAttr('{}.outAlpha'.format(s_filenode) ,'{}.Ksn'.format(s_aishader))
                cmds.setAttr("{}.alphaIsLuminance".format(s_filenode), 1)
                
            elif s_type == 'roughness':
                cmds.connectAttr('{}.outAlpha'.format(s_filenode) ,'{}.specularRoughness'.format(s_aishader))
                cmds.setAttr("{}.alphaIsLuminance".format(s_filenode), 1)

            elif s_type == 'normal':
                # Create bump2d and setting bump2d attrs
                s_bump = cmds.shadingNode('bump2d', name='bump2d{}'.format(self.s_element_name), asShader=True)
                cmds.setAttr("{}.bumpInterp".format(s_bump), 1)
                cmds.setAttr("{}.aiFlipR".format(s_bump), 0)
                cmds.setAttr("{}.aiFlipG".format(s_bump), 0)
                # Connect file with aiStandard via bump2d
                cmds.connectAttr('{}.outAlpha'.format(s_filenode) ,'{}.bumpValue'.format(s_bump))
                cmds.connectAttr('{}.outNormal'.format(s_bump) ,'{}.normalCamera'.format(s_aishader))


    def duplicate(self, s_node_target):
        ''' 
        '''
        s_newnode =cmds.duplicate(s_node_target, ic=True )[0]
        cmds.rename(s_newnode, self.s_name)
        s_sg = cmds.sets(renderable=True, name=self.s_sgname, noSurfaceShader=True, empty=True)
        cmds.connectAttr('{}.outColor'.format(self.s_name) ,'{}.surfaceShader'.format(s_sg))

    def create_texture_node(self, s_name, s_file=None):
        ''' 
        '''
        if s_file:
            s_filenode  = cmds.shadingNode('file', name=s_name, asTexture=True)
            cmds.setAttr('{}.fileTextureName'.format(s_filenode), s_file, type = 'string')
        else:
            s_filenode = s_name
        s_place2d = cmds.shadingNode("place2dTexture", asUtility=True)
        
        try:
            cmds.connectAttr('{}.coverage'.format(s_place2d) ,'{}.coverage'.format(s_filenode))
            cmds.connectAttr('{}.translateFrame'.format(s_place2d) ,'{}.translateFrame'.format(s_filenode))
            cmds.connectAttr('{}.rotateFrame'.format(s_place2d) ,'{}.rotateFrame'.format(s_filenode))
            cmds.connectAttr('{}.mirrorU'.format(s_place2d) ,'{}.mirrorU'.format(s_filenode))
            cmds.connectAttr('{}.mirrorV'.format(s_place2d) ,'{}.mirrorV'.format(s_filenode))
            cmds.connectAttr('{}.stagger'.format(s_place2d) ,'{}.stagger'.format(s_filenode))
            cmds.connectAttr('{}.wrapU'.format(s_place2d) ,'{}.wrapU'.format(s_filenode))
            cmds.connectAttr('{}.wrapV'.format(s_place2d) ,'{}.wrapV'.format(s_filenode))
            cmds.connectAttr('{}.repeatUV'.format(s_place2d) ,'{}.repeatUV'.format(s_filenode))
            cmds.connectAttr('{}.offset'.format(s_place2d) ,'{}.offset'.format(s_filenode))
            cmds.connectAttr('{}.rotateUV'.format(s_place2d) ,'{}.rotateUV'.format(s_filenode))
            cmds.connectAttr('{}.noiseUV'.format(s_place2d) ,'{}.noiseUV'.format(s_filenode))
            cmds.connectAttr('{}.vertexUvOne'.format(s_place2d) ,'{}.vertexUvOne'.format(s_filenode))
            cmds.connectAttr('{}.vertexUvTwo'.format(s_place2d) ,'{}.vertexUvTwo'.format(s_filenode))
            cmds.connectAttr('{}.vertexUvThree'.format(s_place2d) ,'{}.vertexUvThree'.format(s_filenode))
            cmds.connectAttr('{}.vertexCameraOne'.format(s_place2d) ,'{}.vertexCameraOne'.format(s_filenode))
            cmds.connectAttr('{}.outUV'.format(s_place2d) ,'{}.uv'.format(s_filenode))
            cmds.connectAttr('{}.outUvFilterSize'.format(s_place2d) ,'{}.uvFilterSize'.format(s_filenode))
        except Exception, e:
            # Rollback in case of error
            #cmds.delete(s_filenode)
            cmds.delete(s_place2d)
            cmds.error("Ha surgido un problema en create_texture_node \n {}".format(e))
        return s_filenode


