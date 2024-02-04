from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QBrush, QFont, QColor
from PySide6.QtGui import QColor
import re
from typing import List
from text_highlighter.textHighlighterConfig import TextHighlighterConfig


class TextHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        QSyntaxHighlighter.__init__(self, parent)
        self._settings: List[TextHighlighterConfig] = []

    def setSettings(self, settings: List[TextHighlighterConfig]):
        self._settings = settings

    def highlightBlock(self, text):
        if len(text) < 1:
            return

        for setting in self._settings:
            for match in re.finditer(setting.pattern, text):
                text_format = QTextCharFormat()
                text_format.setFontItalic(bool(setting.italic))
                text_format.setFontWeight(bool(setting.bold))
                text_format.setFontPointSize(int(setting.font_size))
                text_format.setForeground(QColor(setting.color_foreground))
                text_format.setBackground(QColor(setting.color_background))

                start, end = match.span()
                self.setFormat(start, end - start, text_format)
