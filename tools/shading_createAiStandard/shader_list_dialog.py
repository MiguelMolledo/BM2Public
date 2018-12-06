# -*- coding: utf-8 -*-
import os, re
import functools
from maya import cmds
from Framework.lib.gui_loader import gui_loader
from Framework.lib.ui.qt.QT import QtCore, QtWidgets, QtGui



form, base = gui_loader.load_ui_type(os.path.join(os.path.dirname(__file__), "ui", "shaderlist.ui"))


class ShaderList(form, base):
    s_element   = ''
    s_base_name = '{elem}_shader_'
    d_contents  = {}
    l_names     = []
    
    

    def __init__(self, s_element, parent=None):
        super(ShaderList, self).__init__(parent)
        self.setupUi(self)
        self.s_base_name = self.s_base_name.format(elem=s_element)
        self._initializeUI()
        self._connectSignals()



    def _initializeUI(self):
        self.setWindowTitle("Nombra los nodos")
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)


    def __insert_spacer(self):
        self.spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.vl_list.addItem(self.spacerItem)


    def _connectSignals(self):

        self.pb_add.clicked.connect(self._add_line)
        self.pb_accept.clicked.connect(self._accept_names)
        self.pb_cancel.clicked.connect(self._cancel)


    def _add_line(self):

        for index in range(self.vl_list.count()):
            widget = self.vl_list.itemAt(index)
            if widget.spacerItem():
                self.vl_list.removeItem(widget)

        w_container = QtWidgets.QWidget()
        w_container.setObjectName("container")
        hl_shader_name = QtWidgets.QHBoxLayout(w_container)
        hl_shader_name.setSpacing(2)

        lb_name = QtWidgets.QLabel(self.gb_list)
        lb_name.setText(self.s_base_name)
        hl_shader_name.addWidget(lb_name)

        le_description = QtWidgets.QLineEdit(self.gb_list)
        le_description.setMinimumSize(QtCore.QSize(155, 0))
        hl_shader_name.addWidget(le_description)


        pb_remove = QtWidgets.QPushButton(self.gb_list)
        pb_remove.setMinimumSize(QtCore.QSize(30, 30))
        pb_remove.setText("-")

        self.d_contents[pb_remove]=le_description
        pb_remove.clicked.connect(functools.partial(self._remove_selected, pb_remove))
        hl_shader_name.addWidget(pb_remove)


        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        hl_shader_name.addItem(spacerItem)

        self.vl_list.addWidget(w_container)
        self.__insert_spacer()


    def _disable_element(self, o_container, s_state):
        o_container.setEnabled(s_state)


    def _remove_selected(self, o_sender=None):
        for o_widget in self.gb_list.children():
            if o_widget.objectName()=="container":
                for o_content in o_widget.children():
                    if o_sender and o_sender == o_content:
                        if o_content in self.d_contents:
                            self.d_contents.pop(o_content)
                        o_widget.deleteLater()


    def _accept_names(self):
        for o_widget in self.gb_list.children():
            if o_widget.objectName()=="container":
                for o_content in o_widget.children():
                    if type(o_content)==QtWidgets.QLineEdit:
                        s_new_name = o_content.text()
                        if not self._check_if_exists(s_new_name):
                            self.l_names.append(s_new_name)
                        else:
                            s_shader_name = '{base}{name}'.format(base=self.s_base_name, name=s_new_name)
                            o_result = QtWidgets.QMessageBox.warning(self, self.tr("El shader [{shader}] ya existe".format(shader=s_shader_name)),
                               self.tr("Ya existe un shader con este nombre\n" + \
                                  "Pulsa Ok para seguir con este nombre,\n" + \
                                  "(se añadirá un numero al final del nombre del shader\n" + \
                                  "o Discard si quieres cambiarlo cambiarlo."),
                                    QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Discard)
                            if o_result == QtWidgets.QMessageBox.Ok:
                                self.l_names.append(s_new_name)
                            else:
                                return


        self.close()



    def _check_if_exists(self, s_name):
        s_shader_name = '{base}{name}'.format(base=self.s_base_name, name=s_name)
        return cmds.objExists(s_shader_name)


    def get_names(self):
        return self.l_names

    def _cancel(self):
        del self.l_names[:]
        self.close()


