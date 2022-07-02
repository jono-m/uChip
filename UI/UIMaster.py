class UIMaster:
    _instance = None

    def __init__(self):
        super().__init__()

    @staticmethod
    def Instance():
        if UIMaster._instance is None:
            UIMaster._instance = UIMaster()
        return UIMaster._instance
