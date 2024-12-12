from PySide6.QtWidgets import QApplication, QProxyStyle, QStyle
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt, QSettings, QSize, QPoint, Slot
from typing import List
import copy

from mainWindow import MainWindow
from debugOutputController import DebugOutputController
from debugOutput import DebugOutput, SerialConnectionSettings
from text_highlighter.textHighlighterConfig import TextHighlighterConfig


class ProxyStyle(QProxyStyle):
    def subElementRect(self, element, opt, widget=None):
        if element == QStyle.SE_ItemViewItemCheckIndicator and not opt.text:
            rect = super().subElementRect(element, opt, widget)
            rect.moveCenter(opt.rect.center())
            return rect
        return super().subElementRect(element, opt, widget)


class Application(QApplication):
    def __init__(self, arguments):
        super().__init__(arguments)

        self.controller = {}
        self.highlighterSettings: List[TextHighlighterConfig] = []

        self.mainWindow = MainWindow()
        self.mainWindow.signal_showDebugOutputCreateDialog.connect(self.showCreateDebugOutputDialog)
        self.mainWindow.signal_createDebugOutput.connect(self.createDebugOutput)
        self.mainWindow.signal_clearAll.connect(self.clearAll)
        self.mainWindow.signal_connectionStateChanged.connect(self.changeConnectionState)
        self.mainWindow.signal_aboutToBeClosed.connect(self.saveDebugOutputSettings)
        self.mainWindow.signal_aboutToBeClosed.connect(self.saveHighlighterSettings)
        self.mainWindow.signal_aboutToBeClosed.connect(self.stopAllDebugOutputs)
        self.mainWindow.signal_editHighlighterSettings.connect(self.showHighlighterSettingsDialog)
        self.mainWindow.signal_applyHighlighterSettings.connect(self.setHighlighterSettings)

        self.loadHighlighterSettings()
        self.loadDebugOutputSettings()

        self.setStyle(ProxyStyle())
        self.mainWindow.show()

        # with open("ElegantDark.qss", "r") as f:
        #     _style = f.read()
        #     self.setStyleSheet(_style)

    def initDefaultHighlighterSettings(self):
        self.highlighterSettings = []

        cfg = TextHighlighterConfig()
        cfg.pattern = r'<DBGVMSG: .* :GSMVGBD>'
        cfg.color_foreground = 'darkgreen'
        cfg.color_background = 'white'
        cfg.italic = False
        cfg.bold = True
        cfg.font_size = QApplication.font().pointSize()
        self.highlighterSettings.append(cfg)

        cfg = TextHighlighterConfig()
        cfg.pattern = r'<DBGVERR: .* :RREVGBD>'
        cfg.color_foreground = 'darkred'
        cfg.color_background = 'white'
        cfg.italic = False
        cfg.bold = True
        cfg.font_size = QApplication.font().pointSize()
        self.highlighterSettings.append(cfg)

    @Slot(object)
    def setHighlighterSettings(self, settings: List[TextHighlighterConfig]):
        self.highlighterSettings = settings
        for ctrl in self.controller.values():
            ctrl.view.setHighlighterSettings(self.highlighterSettings)

    @Slot()
    def showCreateDebugOutputDialog(self):
        already_used_ports = list(self.controller.keys())
        self.mainWindow.showDebugOutputCreateDialog(already_used_ports)

    @Slot(str, SerialConnectionSettings)
    def createDebugOutput(self, window_title: str, settings: SerialConnectionSettings, size: QSize = None):
        if settings.portName in self.controller:
            raise Exception(f"DebugOutput {settings.portName} exists already")

        debug_output = DebugOutput(settings)
        view = self.mainWindow.createDebugOutputView(window_title, size)
        view.setHighlighterSettings(self.highlighterSettings)
        ctrl = DebugOutputController(debug_output, view)

        ctrl.terminated.connect(self.deleteDebugOutput)
        self.controller[settings.portName] = ctrl

        if self.mainWindow.getConnectionState():
            ctrl.start()

    @Slot()
    def deleteDebugOutput(self, portName):
        print(portName)
        if portName in self.controller:
            del self.controller[portName]
        else:
            raise Exception("Controller to remove does not exist in list")

    @Slot()
    def clearAll(self):
        for ctrl in self.controller.values():
            ctrl.view.clear()

    @Slot(bool)
    def changeConnectionState(self, state):
        if len(self.controller.values()) > 0:
            if state:
                failed_to_connect = False

                # try to connect all ports
                for ctrl in self.controller.values():
                    if not ctrl.start():
                        failed_to_connect = True

                if failed_to_connect:
                    # cleanup if connect failed
                    for ctrl in self.controller.values():
                        ctrl.stop()
                    self.mainWindow.setConnectionState(False)
                else:
                    self.mainWindow.setConnectionState(True)
            else:
                for ctrl in self.controller.values():
                    ctrl.stop()
                self.mainWindow.setConnectionState(False)

    def loadDebugOutputSettings(self):
        settings = QSettings('settings.ini', QSettings.Format.IniFormat)

        number_of_connections = settings.beginReadArray("connections")
        for i in range(number_of_connections):
            settings.setArrayIndex(i)

            # check if all needed keys exist
            if all(elem in settings.allKeys() for elem in ['debugOutput', 'view/size', 'view/title']):
                self.createDebugOutput(settings.value("view/title"), settings.value("debugOutput"),
                                       settings.value("view/size"))
        settings.endArray()

    @Slot()
    def saveDebugOutputSettings(self):
        settings = QSettings('settings.ini', QSettings.Format.IniFormat)

        settings.beginWriteArray("connections")
        settings.remove("")  # remove all existing connections

        for i, ctrl in enumerate(self.controller.values()):
            settings.setArrayIndex(i)
            settings.setValue("debugOutput", ctrl.debugOutput.receiver.settings)
            settings.setValue("view/title", ctrl.view.windowTitle())
            settings.setValue("view/size", ctrl.view.size())
            settings.setValue("view/pos", ctrl.view.pos())

        settings.endArray()

    def loadHighlighterSettings(self):
        settings = QSettings('text_highlighter/settings_highlighter.ini', QSettings.Format.IniFormat)

        number_of_settings = settings.beginReadArray("settings")
        if number_of_settings > 0:
            self.highlighterSettings = []

            for i in range(number_of_settings):
                settings.setArrayIndex(i)

                # check if all needed keys exist
                if all(elem in settings.allKeys() for elem in ['pattern', 'color_foreground', 'color_background', 'italic', 'bold']):
                    cfg = TextHighlighterConfig()
                    cfg.pattern = settings.value("pattern")
                    cfg.color_foreground = settings.value("color_foreground")
                    cfg.color_background = settings.value("color_background")
                    cfg.italic = settings.value("italic", type=bool)
                    cfg.bold = settings.value("bold", type=bool)
                    cfg.font_size = settings.value("font_size", type=int)
                    self.highlighterSettings.append(cfg)
            settings.endArray()
        else:
            self.initDefaultHighlighterSettings()

    @Slot()
    def saveHighlighterSettings(self):
        settings = QSettings('text_highlighter/settings_highlighter.ini', QSettings.Format.IniFormat)

        settings.beginWriteArray("settings")
        settings.remove("")  # remove all existing settings

        for i, cfg in enumerate(self.highlighterSettings):
            settings.setArrayIndex(i)
            settings.setValue("pattern", cfg.pattern)
            settings.setValue("color_foreground", cfg.color_foreground)
            settings.setValue("color_background", cfg.color_background)
            settings.setValue("italic", cfg.italic)
            settings.setValue("bold", cfg.bold)
            settings.setValue("font_size", cfg.font_size)
        settings.endArray()

    @Slot()
    def stopAllDebugOutputs(self):
        for ctrl in self.controller.values():
            ctrl.debugOutput.stop()

    @Slot()
    def showHighlighterSettingsDialog(self):
        self.mainWindow.showHighlighterSettingsDialog(copy.deepcopy(self.highlighterSettings))
