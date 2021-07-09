from cx_Freeze import setup, Executable

setup(name="μChip",
      version="1.0",
      author="Jonathan Matthews",
      description="Install μChip",
      executables=[Executable("setup.py", base="Win32GUI", target_name="setup.exe")]
      )
