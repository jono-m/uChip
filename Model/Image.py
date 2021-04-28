import typing


class Image:
    def __init__(self):
        self.xPosition: float = 0
        self.yPosition: float = 0
        self.filename: typing.Optional[str] = None
        self.width: float = 0
        self.height: float = 0
