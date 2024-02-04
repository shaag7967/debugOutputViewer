from PySide6.QtCore import Qt, Slot, Signal
from PySide6.QtGui import QTextCursor, QClipboard
from PySide6.QtWidgets import QApplication, QMdiSubWindow, QTextEdit, QPushButton, QCheckBox
from typing import List
from text_highlighter.textHighlighter import TextHighlighter, TextHighlighterConfig
from ui.uiFileHelper import createWidgetFromUiFile


class DebugOutputWindow(QMdiSubWindow):
    closed = Signal()

    def __init__(self, windowTitle):
        super().__init__()

        widget = createWidgetFromUiFile("ui/debugOutputWindow.ui")

        self.setWidget(widget)
        self.setWindowTitle(windowTitle)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.textEdit: QTextEdit = widget.findChild(QTextEdit, 'textEdit')

        self.highlighter = TextHighlighter()
        self.highlighter.setDocument(self.textEdit.document())

        pb_clear: QPushButton = widget.findChild(QPushButton, 'pb_clear')
        pb_clear.pressed.connect(self.clear)

        pb_copy: QPushButton = widget.findChild(QPushButton, 'pb_copy')
        pb_copy.pressed.connect(self.copy)

        self.checkBox_enabled: QCheckBox = self.widget().findChild(QCheckBox, 'checkBox_enabled')

    def closeEvent(self, event):
        # is not called when mainwindow is closed
        event.accept()
        self.closed.emit()

    @Slot()
    def clear(self):
        self.textEdit.clear()

    def setHighlighterSettings(self, settings: List[TextHighlighterConfig]):
        self.highlighter.setSettings(settings)
        self.highlighter.rehighlight()

    @Slot()
    def copy(self):
        clipboard: QClipboard = QApplication.clipboard()
        cursor = self.textEdit.textCursor()

        if cursor.selection().isEmpty():
            text = self.textEdit.toPlainText()
        else:
            # copy selected text
            text = cursor.selection().toPlainText()

        if len(text) > 0:
            clipboard.setText(text)

    @Slot()
    def appendData(self, data, force=False):
        if self.checkBox_enabled.isChecked() or force:
            self.textEdit.moveCursor(QTextCursor.End)
            self.textEdit.insertPlainText(data)
            self.textEdit.ensureCursorVisible()

