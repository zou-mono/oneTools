# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['frmMain.py', 'frmCoordTransform.py', 'frmTileMap.py', 'frmVectorMap.py', 'icons_rc.py',
              'UI\\listview_dialog.py',
              'UI\\UICoordTransform.py',
              'UI\\UIMain.py',
              'UI\\UITileMap.py',
              'UI\\UIVectorMap.py',
              'UICore\\asyncRequest.py',
              'UICore\\common.py',
              'UICore\\coordTransform.py',
              'UICore\\coordTransform_dwg.py',
              'UICore\\coordTransform_table.py',
              'UICore\\coordTransform_web.py',
              'UICore\\DataFactory.py',
              'UICore\\Gv.py',
              'UICore\\log4p.py',
              'UICore\\merge_tiles2.py',
              'UICore\\pycomcad.py',
              'UICore\\suplicmap_tilemap.py',
              'UICore\\suplicmap_vector2.py',
              'UICore\\workerThread.py',
              'widgets\\CollapsibleSplitter.py',
              'widgets\\mTable.py'],
             pathex=['D:\\Codes\\oneTools'],
             binaries=[('C:\\Program Files\\GDAL\\gdalplugins', 'Library\\lib\\gdalplugins'),
                       ('C:\\Program Files\\GDAL\\FileGDBAPI.dll', '.')],
             datas=[('C:\\Program Files\\GDAL\\projlib', 'Library\\share\\proj'),
                    ('C:\\Users\\mono-office-laptop\\miniconda3\\envs\\test_python3.7'
                     '\\Lib\\site-packages\\PyQt5\\Qt\\plugins\\styles\\qwindowsvistastyle.dll', 'Library\\styles\\qwindowsvistastyle.dll')],
             hiddenimports=['osgeo'],
             hookspath=[],
             runtime_hooks=['hook.py'],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
          cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          exclude_binaries=False,
          name='oneTools',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=False,
          icon="D:\\Codes\\oneTools\\icons\\GeoprocessingToolbox.ico",
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False,
          version="version.py")
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=False,
               upx_exclude=[],
               name='oneTools')
