from PySide6.QtWidgets import QMdiArea, QMainWindow, QPushButton
from PySide6.QtCore import QSettings, QSize, QPoint, Signal

from typing import List

from debugOutput import SerialConnectionSettings
from ui.uiFileHelper import createWidgetFromUiFile
from debugOutputWindow import DebugOutputWindow
from createDebugOutputDialog import CreateDebugOutputDialog
from text_highlighter.textHightlighterSettingsDialog import TextHighlighterSettingsDialog
from text_highlighter.textHighlighter import TextHighlighterConfig


class MainWindow(QMainWindow):
    signal_showDebugOutputCreateDialog = Signal()
    signal_createDebugOutput = Signal(str, SerialConnectionSettings)
    signal_clearAll = Signal()
    signal_connectionStateChanged = Signal(bool)
    signal_aboutToBeClosed = Signal()
    signal_editHighlighterSettings = Signal()
    signal_applyHighlighterSettings = Signal(object)

    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle('Debug Output Viewer')

        widget = createWidgetFromUiFile("ui/mainWindow.ui")

        self.mdiArea = widget.findChild(QMdiArea, 'mdiArea')
        self.pb_changeConnectionState: QPushButton = widget.findChild(QPushButton, 'pb_changeConnectionState')

        self.setCentralWidget(widget)
        self.setConnectionState(False)
        self.loadSettings()

        # connections
        widget.pb_create.clicked.connect(self.signal_showDebugOutputCreateDialog)
        widget.pb_clear.clicked.connect(self.signal_clearAll)
        widget.pb_changeConnectionState.clicked.connect(self.signal_connectionStateChanged)
        widget.pb_highlighter.clicked.connect(self.signal_editHighlighterSettings)

    def showDebugOutputCreateDialog(self, disabled_ports: list):
        dialog = CreateDebugOutputDialog(self)
        dialog.disablePorts(disabled_ports)
        if dialog.exec():
            port_name = dialog.getPortName()
            if len(port_name) > 0:
                settings = SerialConnectionSettings(port_name)
                settings.baudrate = dialog.getBaudrate()
                settings.bytesize = dialog.getDataBits()
                settings.parity = dialog.getParity()
                settings.stopbits = dialog.getStopBits()

                self.signal_createDebugOutput.emit(dialog.getName(), settings)

    def createDebugOutputView(self, viewTitle: str, size: QSize = None):
        view = DebugOutputWindow(viewTitle)
        if size:
            view.resize(size)
        self.mdiArea.addSubWindow(view)
        view.show()
        return view

    def showHighlighterSettingsDialog(self, settings: List[TextHighlighterConfig]):
        dialog = TextHighlighterSettingsDialog(self, settings)
        if dialog.exec():
            self.signal_applyHighlighterSettings.emit(dialog.table_model.settings)

    def getConnectionState(self):
        return self.pb_changeConnectionState.isChecked()

    def setConnectionState(self, state):
        self.pb_changeConnectionState.setChecked(state)
        if state:
            self.pb_changeConnectionState.setText('Stop')
        else:
            self.pb_changeConnectionState.setText('Start')

    def loadSettings(self):
        settings = QSettings('settings.ini', QSettings.Format.IniFormat)

        settings.beginGroup("MainWindow")
        self.resize(settings.value("size", QSize(800, 800)))
        settings.endGroup()

    def saveSettings(self):
        settings = QSettings('settings.ini', QSettings.Format.IniFormat)

        settings.beginGroup("MainWindow")
        settings.setValue("size", self.size())
        settings.endGroup()

    def closeEvent(self, event):
        self.signal_aboutToBeClosed.emit()
        self.saveSettings()
        event.accept()
