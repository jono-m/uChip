from cx_Freeze import setup, Executable

files = {"include_files": ['Assets/']}
setup(name="μChip",
      version="1.0",
      author="Jonathan Matthews",
      description="Microfluidic device prototyping control software.",
      options={'build_exe': files},
      executables=[Executable("main.py", base="Win32GUI", icon="Assets/Images/icon.ico", target_name="uChip.exe")]
      )
