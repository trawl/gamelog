try:
    from PySide import QtCore
except ImportError as error:
    from PyQt4 import QtCore
    QtCore.Signal = QtCore.pyqtSignal
    QtCore.Slot = QtCore.pyqtSlot
    
class Communicator(QtCore.QObject): 
    addedNewPlayer = QtCore.Signal(str)

