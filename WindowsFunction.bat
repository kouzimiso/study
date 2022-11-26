dism  /online /Get-Features

SET /P INPUTSTR="‰¼‘z‰»‚ğ—LŒø‚É‚µ‚Ü‚·‚©Hy/n"

if "%INPUTSTR%" == "y" (
dism /online /Enable-Feature /FeatureName:HypervisorPlatform
dism /online /Enable-Feature /FeatureName:VirtualMachinePlatform
pause
) else (
dism /online /Disable-Feature /FeatureName:HypervisorPlatform
dism /online /Disable-Feature /FeatureName:VirtualMachinePlatform
pause
)

