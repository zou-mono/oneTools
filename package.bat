nuitka --standalone --output-dir=output suplicmap_tilemap.py
nuitka --standalone --output-dir=output merge_tiles.py

nuitka --standalone  --show-memory --show-progress --nofollow-imports --plugin-enable=qt-plugins --follow-import-to=need --recurse-all --output-dir=output suplicmap_tilemap.py

nuitka --standalone  --show-progress --plugin-enable=qt-plugins,numpy --output-dir=release frmMain.py
nuitka --standalone  --windows-disable-console --show-progress --plugin-enable=qt-plugins,numpy --include-qt-plugins=all --output-dir=release frmMain.py

nuitka --standalone  --show-progress --nofollow-imports --follow-import-to=UI --follow-import-to=UICore --follow-import-to=widgets --follow-import-to=frmCoordTransform --follow-import-to=frmTileMap --follow-import-to=frmVectorMap --follow-import-to=icons_rc  --follow-import-to=win32 --output-dir=release frmMain.py

--windows-disable-console

nuitka --standalone  --show-progress --nofollow-import-to=osgeo  --nofollow-import-to=PyQt5 --nofollow-import-to=numpy --follow-import-to=UI --follow-import-to=UICore --follow-import-to=widgets --follow-import-to=frmCoordTransform.py --follow-import-to=frmTileMap.py --follow-import-to=frmVectorMap.py --follow-import-to=icons_rc.py  --output-dir=release frmMain.py