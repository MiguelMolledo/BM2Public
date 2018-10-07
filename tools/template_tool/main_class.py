
import os
import sys
from Framework.lib.ui.qt.QT import QtCore, QtWidgets, QtGui
from Framework import get_environ_file, get_css_path, get_icon_path, get_environ_config
from Framework.lib.gui_loader import gui_loader
from Framework.lib import ui
form_class, base_class = gui_loader.load_ui_type(os.path.join(os.path.dirname(__file__), "gui", "main.ui"))

class TemplateClass(base_class, form_class):
    
    def __init__(self, file_path="",parent=None):
        super(TemplateClass, self).__init__(parent=parent)
        self.setupUi(self)
        ui.apply_resource_style(self)

if __name__ == "__main__":
    from Framework.lib.ui.qt.QT import QtCore, QtWidgets, QtGui
    import sys
    from Framework.lib.gui_loader import gui_loader
    app = QtWidgets.QApplication(sys.argv)
    widget = TemplateClass()
    obj = gui_loader.get_default_container(widget, "test")
    obj.show()
    app.exec_()

