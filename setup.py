from cx_Freeze import setup, Executable

setup(name="uChip",
      version="0.1",
      description="",
      executables=[Executable(
            script="main.py",
            icon="Assets/icon.ico")])
