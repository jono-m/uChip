from cx_Freeze import setup, Executable

includeFiles = ["Assets"]
setup(name="uChip",
      version="0.1",
      description="Control software for microfluidic prototyping.",
      author="Jonathan Matthews",
      options={'build_exe': {'include_files': includeFiles}},
      executables=[Executable(
          base="Win32GUI",
          script="main.py",
          icon="Assets/icon.ico")])
