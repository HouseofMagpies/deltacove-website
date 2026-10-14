"""Stage only public pages/assets. Keep draft Markdown and authoring files out."""
from pathlib import Path
import shutil
root=Path(__file__).resolve().parents[1]
out=root/'_site'
if out.exists():shutil.rmtree(out)
out.mkdir()
for name in ('index.html','what-we-do.html','styles.css','.nojekyll'):
 shutil.copyfile(root/name,out/name)
for name in ('assets','musings'):
 shutil.copytree(root/name,out/name)
print('Public site staged in _site; authoring files and drafts excluded.')
