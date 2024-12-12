from PySide6.QtCore import QObject, Slot, Signal
from debugOutput import DebugOutput
from debugOutputWindow import DebugOutputWindow

class DebugOutputController(QObject):
    terminated = Signal(str)

    def __init__(self, debugOutput, view):
        super().__init__()
        self.debugOutput: DebugOutput = debugOutput
        self.view: DebugOutputWindow = view

        self.view.closed.connect(self.terminate)
        self.debugOutput.dataAvailable.connect(self.view.appendData)

    def start(self) -> bool:
        started = self.debugOutput.start()
        if started:
            self.show_message(f'Opened {self.debugOutput.getPortName()}')
        else:
            self.show_error(f'Failed to open {self.debugOutput.getPortName()}')
        return started

    def stop(self):
        if self.debugOutput.isActive():
            self.debugOutput.stop()
            self.show_message(f'Closed {self.debugOutput.getPortName()}')

    def show_message(self, text):
        self.view.appendData(f'\n<DBGVMSG: {text} :GSMVGBD>\n', True)

    def show_error(self, text):
        self.view.appendData(f'\n<DBGVERR: {text} :RREVGBD>\n', True)

    @Slot()
    def terminate(self):
        # view is already closed
        self.debugOutput.stop()
        self.terminated.emit(self.debugOutput.getPortName())
