# -*- mode: python ; coding: utf-8 -*-

# pyinstaller.py --windowed --noconsole --clean --onefile AppStart\AppStart.spec
# pyinstaller --windowed --noconsole --clean --onefile run.spec


block_cipher = None


a = Analysis(['pysaurus\\interface\\qtwebview\\run.py'],
             pathex=['c:\\data\\git\\pysaurus'],
             binaries=[
                (r'pysaurus\bin\win64\alignmentRaptor.dll', r'pysaurus\bin\win64'),
                (r'pysaurus\bin\win64\avcodec-58.dll', r'pysaurus\bin\win64'),
                (r'pysaurus\bin\win64\avdevice-58.dll', r'pysaurus\bin\win64'),
                (r'pysaurus\bin\win64\avformat-58.dll', r'pysaurus\bin\win64'),
                (r'pysaurus\bin\win64\avutil-56.dll', r'pysaurus\bin\win64'),
                (r'pysaurus\bin\win64\libgcc_s_seh-1.dll', r'pysaurus\bin\win64'),
                (r'pysaurus\bin\win64\libgomp-1.dll', r'pysaurus\bin\win64'),
                (r'pysaurus\bin\win64\libwinpthread-1.dll', r'pysaurus\bin\win64'),
                (r'pysaurus\bin\win64\runVideoRaptorBatch.exe', r'pysaurus\bin\win64'),
                (r'pysaurus\bin\win64\runVideoRaptorThumbnails.exe', r'pysaurus\bin\win64'),
                (r'pysaurus\bin\win64\swresample-3.dll', r'pysaurus\bin\win64'),
                (r'pysaurus\bin\win64\swscale-5.dll', r'pysaurus\bin\win64'),
             ],
             datas=[
                (r'pysaurus\interface\web\index.html', r'pysaurus\interface\web'),
                (r'pysaurus\interface\web\onload.js', r'pysaurus\interface\web'),
                (r'pysaurus\interface\web\qt.js', r'pysaurus\interface\web'),
                (r'pysaurus\interface\web\lib\*.js', r'pysaurus\interface\web\lib'),
                (r'pysaurus\interface\web\css\*.css', r'pysaurus\interface\web\css'),
                (r'pysaurus\interface\web\build', r'pysaurus\interface\web\build'),
             ],
             hiddenimports=[],
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
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
          name='pysaurus',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=False,
          upx_exclude=[],
          console=False,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None )
