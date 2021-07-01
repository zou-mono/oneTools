nuitka --standalone --output-dir=output suplicmap_tilemap.py
nuitka --standalone --output-dir=output merge_tiles.py

nuitka --standalone  --show-memory --show-progress --nofollow-imports --plugin-enable=qt-plugins --follow-import-to=need --recurse-all --output-dir=output suplicmap_tilemap.py

nuitka --standalone  --show-progress --plugin-enable=qt-plugins,numpy --output-dir=release frmMain.py
nuitka --standalone  --windows-disable-console --mingw64 --show-progress --plugin-enable=qt-plugins,numpy --output-dir=release frmMain.py

nuitka --standalone --mingw64 --show-progress --nofollow-import-to=numpy,jinja2,matplotlib,scipy,sqlalchemy,pandas,pygal,pyzbar,pubunit,qtunit,dataunit,osgeo --follow-import-to=UI --follow-import-to=UICore --follow-import-to=widgets --follow-import-to=frmCoordTransform --follow-import-to=frmTileMap --follow-import-to=frmVectorMap --follow-import-to=icons_rc --plugin-enable=qt-plugins --output-dir=release frmMain.py

--windows-disable-console

nuitka --standalone  --windows-disable-console --show-progress --nofollow-import-to=osgeo  --nofollow-import-to=PyQt5 --nofollow-import-to=numpy --follow-import-to=UI --follow-import-to=UICore --follow-import-to=widgets --follow-import-to=frmCoordTransform.py --follow-import-to=frmTileMap.py --follow-import-to=frmVectorMap.py --follow-import-to=icons_rc.py  --output-dir=release frmMain.py

pyinstaller --version-file file_version_info.txt main_gdal.spec