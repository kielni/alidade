from qgis.core import QgsProject
from qgis.PyQt.QtCore import QTimer
from qgis.PyQt.QtGui import QKeySequence
from qgis.PyQt.QtWidgets import QShortcut
from qgis.utils import iface


def reload_project():
    path = QgsProject.instance().fileName()
    if not path:
        return
    iface.mapCanvas().stopRendering()
    # clear() lets the layer model process removals before read() adds new
    # layers; without it, the model's sort comparator accesses freed layer
    # objects and segfaults.
    QgsProject.instance().clear()
    QTimer.singleShot(0, lambda: QgsProject.instance().read(path))


def register():
    shortcut = QShortcut(QKeySequence("Ctrl+R"), iface.mainWindow())
    shortcut.activated.connect(reload_project)


iface.initializationCompleted.connect(register)
