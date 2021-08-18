echo Build Pysaurus package using poetry
call poetry build || goto :error

echo Create conda environment
md exedir || goto :error
call conda create -y python=3.8 --prefix=exedir\exenv || goto :error

echo Install Pysaurus package into conda environment
call conda activate .\exedir\exenv || goto :error
call pip install dist\pysaurus-0.1.0-py3-none-any.whl || goto :error

echo Copy (de)activation scripts into conda environment
copy scripts\fromcondapack\activate.bat exedir\exenv\Scripts || goto :error
copy scripts\fromcondapack\deactivate.bat exedir\exenv\Scripts || goto :error
copy scripts\run.bat .\exedir || goto :error

echo Deactivate conda environment
call conda deactivate || goto :error

echo Generate ZIP file "pysaurus.zip"
call python -c "import shutil; shutil.make_archive('pysaurus', 'zip', 'exedir')" || goto :error
move pysaurus.zip dist\

echo Cleanup
rmdir /S /Q exedir || goto :error

echo Success
goto :EOF

:error
set ERROR=#%errorlevel%
echo Failed with error #%errorlevel%.
REM cleanup here?
exit /b %ERROR%

