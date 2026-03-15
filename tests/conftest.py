from pathlib import Path
import sys
import os


ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Prevent expensive index/model bootstrap during test startup.
os.environ.setdefault("SKIP_INDEX_BOOTSTRAP", "1")
os.environ.setdefault("DOCS_PATH", "./files")
os.environ.setdefault("PDF_PATH", "./files")
os.environ.setdefault("HOST_DOCS_PATH", "./files")
os.environ.setdefault("INDEX_PATH", "./temp/test-vectorstore")
