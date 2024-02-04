from PySide6.QtWidgets import QDialog, QVBoxLayout, QHeaderView, QStyledItemDelegate, QAbstractItemDelegate, QAbstractItemView, QItemDelegate, QComboBox
from PySide6.QtCore import Qt, QSize
from ui.uiFileHelper import createWidgetFromUiFile
from typing import List
from text_highlighter.textHighlighterConfig import TextHighlighterConfig
from text_highlighter.textHighlighterTableModel import TextHighlighterTableModel


class ColorSelectorDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        if isinstance(self.parent(), QAbstractItemView):
            self.parent().openPersistentEditor(index)
        QStyledItemDelegate.paint(self, painter, option, index)

    def createEditor(self, parent, option, index):
        combobox = QComboBox(parent)

        colors = index.data(TextHighlighterTableModel.AllColorsRole)
        for color in colors:
            combobox.insertItem(color[0], color[1])
            combobox.setItemData(color[0], color[2], Qt.DecorationRole)

        combobox.currentIndexChanged.connect(self.onCurrentIndexChanged)
        return combobox

    def onCurrentIndexChanged(self, ix):
        editor = self.sender()
        self.commitData.emit(editor)
        self.closeEditor.emit(editor, QAbstractItemDelegate.NoHint)

    def setEditorData(self, editor, index):
        ix = index.data(TextHighlighterTableModel.SelectedColorRole)
        editor.setCurrentIndex(ix)

    def setModelData(self, editor, model, index):
        ix = editor.currentIndex()
        model.setData(index, ix, TextHighlighterTableModel.SelectedColorRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

    def sizeHint(self, option, index):
        return super().sizeHint(option, index)

class TextHighlighterSettingsDialog(QDialog):
    def __init__(self, parent, settings: List[TextHighlighterConfig]):
        super().__init__(parent)

        self.setWindowTitle("Text Highlighting Settings")
        self.widget = createWidgetFromUiFile("ui/textHighlightingSettings.ui")

        self.table_model = TextHighlighterTableModel(settings)
        self.widget.tableView.setModel(self.table_model)
        self.widget.tableView.setItemDelegateForColumn(1, ColorSelectorDelegate(self.widget.tableView))
        self.widget.tableView.setItemDelegateForColumn(2, ColorSelectorDelegate(self.widget.tableView))

        # QTableView Headers
        self.horizontal_header = self.widget.tableView.horizontalHeader()
        self.vertical_header = self.widget.tableView.verticalHeader()

        # size
        self.horizontal_header.setSectionResizeMode(QHeaderView.Stretch)
        self.horizontal_header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.horizontal_header.setSectionResizeMode(4, QHeaderView.ResizeToContents)

        # buttons
        self.widget.buttonBox.accepted.connect(self.accept)
        self.widget.buttonBox.rejected.connect(self.reject)
        self.widget.pb_add.clicked.connect(self.addSetting)
        self.widget.pb_delete.clicked.connect(self.deleteSetting)

        QVBoxLayout(self).addWidget(self.widget)

    def addSetting(self):
        self.table_model.insertRows(self.table_model.rowCount(), 1)

    def deleteSetting(self):
        selected_model_indices = self.widget.tableView.selectionModel().selectedRows()
        for index in selected_model_indices:
            self.table_model.removeRows(index.row(), 1)
