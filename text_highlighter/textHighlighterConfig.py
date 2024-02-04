
class TextHighlighterConfig:
    number_of_attributes = 5

    def __init__(self):
        self.pattern = r"some text"
        self.color_foreground = 'black'
        self.color_background = 'white'
        self.italic = False
        self.bold = False

    def __str__(self):
        return (f"{self.pattern}: "
                f"  front {self.color_foreground} | back {self.color_background}"
                f"{' | italic' if self.italic is True else ''}{' | bold' if self.bold is True else ''}")

