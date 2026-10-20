"""Execute the checked-in notebooks in place without replacing their content.

Run from the repository root with notebook dependencies installed:
    python scripts/build_notebooks.py
"""

from pathlib import Path

import nbformat
from nbconvert.preprocessors import ExecutePreprocessor

ROOT = Path(__file__).resolve().parent.parent
NOTEBOOKS = sorted((ROOT / "notebooks").glob("*.ipynb"))


def main() -> None:
    if not NOTEBOOKS:
        raise SystemExit("No notebooks found")
    executor = ExecutePreprocessor(timeout=600, kernel_name="python3")
    for path in NOTEBOOKS:
        notebook = nbformat.read(path, as_version=4)
        executor.preprocess(notebook, {"metadata": {"path": str(ROOT)}})
        nbformat.write(notebook, path)
        print(f"Executed {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
