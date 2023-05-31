set PythonPath=D:\ProgramFiles\Coding\WPy64-38100\python-3.8.10.amd64\


%PythonPath%python -m PyInstaller --onefile --distpath .\Debug --name output  --clean  .\test_jsonprint.py

pause