import os
from Framework.lib.gui_loader import gui_loader
from Framework.lib.ui.qt.QT import QtCore, QtWidgets, QtGui
from maya import mel
from maya import cmds
#con esto llamamos a la ui
form, base = gui_loader.load_ui_type(os.path.join(os.path.dirname(__file__), "ui", "replacer.ui"))


class replacerWidget(form, base):

    def __init__(self):
        #el __init__ es lo primero que se ejecuta automaticamente al llamar a una clase
        super(replacerWidget, self).__init__()
        self.setupUi(self)
        #Aqui inicializamos las variables que vamos a usar en diferentes funciones
        #si empieza por l es una lista
        #si empieza por s un string
        #si empieza por b booleana
        #si esta en minusculas variable
        #si esta en mayusculas constante
        self.l_to_add = []
        self.l_to_remove = []
        self.l_scene_elements = []
        self.b_selection_mode = False
        #Aqui llamamos a la funcion que hace las conexiones entre los botones de la ui y las funciones
        self.connectSignals()

    def connectSignals(self):
        #Si abres la ui veras que hay un botton BTN_ACEPTAR y un check box BTN_SELECTION
        #lo unico que hacer aqui es conectar la senal clicked con la funcion a la que llama el boton
        self.BTN_ACEPTAR.clicked.connect(self._initProcess)
        self.BTN_SELECTION.clicked.connect(self._selection_mode)
        
    def _selection_mode (self):
        #si el check box de BTN_SELECTION se activa o desactiva llamamos a esta funcion que setea una variable booleana
        if self.BTN_SELECTION.isChecked() == True:
            self.b_selection_mode = True
            return
        if self.BTN_SELECTION.isChecked() == False:
            self.b_selection_mode = False
            return
            
    def _initProcess(self):
        #Esta es la funcion que se ejecuta al pulsar el boton aceptar, y llama una a una a todas las funciones que 
        #necesitamos en orden, esto es mucho mas limpio y claro que llamar a las funciones unas dentro de otras
        #encadenadas es dificil de trakear
        #al tenerlo asi es facil ver lo que hace y cambiar el orden
        self._recolectData()
        self._listElements()
        self._cleanElements()
        
    
    def _recolectData(self):
        #recolecta la info de los espacios de la ui y los almacena en variables tipo string
        s_to_add = self.BTN_TOADD.toPlainText()
        s_to_remove = self.BTN_TOREMOVE.toPlainText()
        #lo corta por las comas y lo mete en listas
        self.l_to_add = s_to_add.split(",")
        self.l_to_remove = s_to_remove.split(",")
    
    def _listElements(self):
        #aqui almacenamos todos los elementos de la escena en una lista, si el b_selection_mode es == true,
        #significa que el check box esta marcado y trabajaremos sobre seleccion
        #si tienes dudas de donde viene b_selection_mode mira la funcion _selection_mode
        self.l_scene_elements = cmds.ls (sl=self.b_selection_mode, type="mesh")
        list_transforms= cmds.ls (sl=self.b_selection_mode, type="transform")
        for n in range (0, len(list_transforms)):
            self.l_scene_elements.append(list_transforms[n])
        
    def _cleanElements(self):
        #por cada elemento de la lista, comparamos cada una de sus letras con los elementos a eliminar que son los de la lista l_to_remove
        #si alguna posicion del nombre es == a alguno de los elementos de l_to_remove
        #reemplazaremos esta posicion por su igual en la lista l_to_add
        for element in self.l_scene_elements:
            for n in range (0, len(element)):
                for m in range (0, len(self.l_to_remove)):
                    if element[n] == self.l_to_remove[m]:
                        caracters_list_element = list(element)
                        caracters_list_element[n] = str(self.l_to_add[m])
                        new_element = "".join(caracters_list_element)
                        cmds.rename(element, new_element)
                        element = new_element
        print "hecho"

                        