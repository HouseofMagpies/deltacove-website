"""Stage the current single-page site for GitHub Pages."""
from pathlib import Path
import shutil

root = Path(__file__).resolve().parents[1]
out = root / '_site'
if out.exists():
    shutil.rmtree(out)
out.mkdir()
for name in ('index.html', '.nojekyll'):
    shutil.copyfile(root / name, out / name)
print('Public site staged in _site.')
