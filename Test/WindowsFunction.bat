dism  /online /Get-Features

SET /P INPUTSTR="仮想化を有効にしますか？y/n"

if %INPUTSTR%=="y" (
dism /online /Enable-Feature /FeatureName:HypervisorPlatform
dism /online /Enable-Feature /FeatureName:VirtualMachinePlatform
) else (
dism /online /Disable-Feature /FeatureName:HypervisorPlatform
dism /online /Disable-Feature /FeatureName:VirtualMachinePlatform
)

pause