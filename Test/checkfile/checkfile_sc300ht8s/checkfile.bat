@echo off

for /f "tokens=*" %%s in (checkfiledata.txt) do (
if exist %%s (
	echo OK: %%s
) else (
        echo  X: %%s
)
)
pause
