nuitka --standalone --output-dir=output suplicmap_tilemap.py
nuitka --standalone --output-dir=output merge_tiles.py

nuitka --standalone  --show-memory --show-progress --nofollow-imports --plugin-enable=qt-plugins --follow-import-to=need --recurse-all --output-dir=output suplicmap_tilemap.py

nuitka --standalone  --show-progress --plugin-enable=qt-plugins,numpy --output-dir=release frmMain.py