dism  /online /Get-Features

SET /P INPUTSTR="���z����L���ɂ��܂����Hy/n"

if "%INPUTSTR%" == "y" (
dism /online /Enable-Feature /FeatureName:HypervisorPlatform
dism /online /Enable-Feature /FeatureName:VirtualMachinePlatform
pause
) else (
dism /online /Disable-Feature /FeatureName:HypervisorPlatform
dism /online /Disable-Feature /FeatureName:VirtualMachinePlatform
pause
)

