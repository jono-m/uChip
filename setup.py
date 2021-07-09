import zipfile
import os
from pathlib import Path

os.chdir(os.path.dirname(__file__))
zipFilePath = Path("./uChip.zip")
programFilesPath = Path(os.environ["ProgramFiles"])
with zipfile.ZipFile(zipFilePath, 'r') as zip_ref:
    zip_ref.extractall(programFilesPath / "uChip")
