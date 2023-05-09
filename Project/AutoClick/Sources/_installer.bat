set PythonPath=D:\ProgramFiles\Coding\WPy64-38100\python-3.8.10.amd64\

%PythonPath%python -m PyInstaller --onefile --distpath ..\Resources --name Camera --clean  .\Common\Camera.py
%PythonPath%python -m PyInstaller --onefile --distpath ..\Resources --name FileControl --clean  .\Common\FileControl.py

pause