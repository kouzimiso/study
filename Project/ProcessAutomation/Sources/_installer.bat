set PythonPath=D:\ProgramFiles\Coding\WPy64-38100\python-3.8.10.amd64\
Rem OK

Rem TEST
%PythonPath%python -m PyInstaller --onefile --distpath ..\ --name FunctionControl --clean  --exclude jaraco/text/Lorem\ipsum.txt  .\Common\FunctionControl.py

pause