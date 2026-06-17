@echo off
rem ============================================================
rem  WebGantt server edition  ->  GitHub Pages deploy
rem  Publishes this folder (index.html etc.) to a GitHub repo
rem  and (optionally) enables GitHub Pages.
rem  Required: git.  Optional: GitHub CLI (gh) to auto-create a repo.
rem  ASCII-only on purpose to avoid console codepage issues.
rem ============================================================
setlocal enableextensions
cd /d "%~dp0"

echo(
echo === WebGantt deploy (GitHub) ===
echo(

rem ---- locate git automatically ----
set "GITEXE="
where git >nul 2>&1 && set "GITEXE=git"
if not defined GITEXE if exist "%ProgramFiles%\Git\cmd\git.exe" set "GITEXE=%ProgramFiles%\Git\cmd\git.exe"
if not defined GITEXE if exist "%ProgramFiles(x86)%\Git\cmd\git.exe" set "GITEXE=%ProgramFiles(x86)%\Git\cmd\git.exe"
if not defined GITEXE if exist "%LocalAppData%\Programs\Git\cmd\git.exe" set "GITEXE=%LocalAppData%\Programs\Git\cmd\git.exe"
if not defined GITEXE for /d %%D in ("%LocalAppData%\GitHubDesktop\app-*") do if exist "%%D\resources\app\git\cmd\git.exe" set "GITEXE=%%D\resources\app\git\cmd\git.exe"

:askgit
if defined GITEXE goto :gitfound
echo(
echo git.exe was not found automatically.
echo Enter the full path to git.exe. Example:
echo    C:\Program Files\Git\cmd\git.exe
echo Leave empty and press Enter to abort.
set /p "GITEXE=git.exe path: "
if not defined GITEXE goto :nogit
set GITEXE=%GITEXE:"=%
if not exist "%GITEXE%" (
  echo [ERROR] not found: %GITEXE%
  set "GITEXE="
  goto :askgit
)
:gitfound

set "GITDIR="
if /i not "%GITEXE%"=="git" for %%I in ("%GITEXE%") do set "GITDIR=%%~dpI"
if defined GITDIR set "PATH=%GITDIR%;%PATH%"
git --version >nul 2>&1
if errorlevel 1 ( echo [ERROR] could not run git. & goto :fail )
for /f "delims=" %%V in ('git --version') do echo Using %%V

rem ---- check required files ----
set "FILES=index.html gantt.html gantt_core.js config.js crypto.js providers.js"
for %%F in (%FILES%) do (
  if not exist "%%F" (
    echo [ERROR] %%F not found. Run this inside the WebGantt folder.
    goto :fail
  )
)

rem ---- repository input (accepts URL / owner-repo / name) ----
echo(
echo Enter your GitHub repository. Any of these is OK:
echo    Full URL    : https://github.com/kouzimiso/study
echo    owner/repo  : kouzimiso/study
echo    name only   : study     (auto-create needs GitHub CLI)
echo NOTE: your username is part of the URL. You do NOT type it separately.
echo       Git asks for username + token only during push.
set "RAW="
set /p "RAW=Repository: "
set RAW=%RAW:"=%
if "%RAW%"=="" set "RAW=webgantt"
if "%RAW:~-1%"=="/" set "RAW=%RAW:~0,-1%"

set "REPOURL="
set "OWNER="
set "REPO="
if not "%RAW%"=="%RAW:github.com=%" set "REPOURL=%RAW%"
if not "%RAW%"=="%RAW:://=%" set "REPOURL=%RAW%"
if defined REPOURL (
  call :derive
) else (
  if not "%RAW%"=="%RAW:/=%" (
    set "REPOURL=https://github.com/%RAW%"
    call :derive
  ) else (
    set "REPO=%RAW: =%"
  )
)

rem ---- mode ----
set "MODE=gist"
set /p "MODE=Mode gist / selfserver / local [gist]: "
if "%MODE%"=="" set "MODE=gist"
set "APIBASE=https://your-server.example.com/api"
if /i "%MODE%"=="selfserver" set /p "APIBASE=Self-server API base URL: "

rem ---- build a separate deploy folder ----
set "BUILD=%~dp0_deploy"
if exist "%BUILD%" rmdir /s /q "%BUILD%"
mkdir "%BUILD%"
for %%F in (%FILES%) do copy /y "%%F" "%BUILD%\" >nul

rem ---- generate config.js for the chosen mode ----
(
  echo window.WEBGANTT_CONFIG = {
  echo   mode: "%MODE%",
  echo   gist: { clientId: "" },
  echo   selfserver: { apiBase: "%APIBASE%" },
  echo   kdf: { iterations: 600000 },
  echo   sampleIfEmpty: false
  echo };
) > "%BUILD%\config.js"

rem ---- git init and commit ----
pushd "%BUILD%"
git config --global --add safe.directory "*" >nul 2>&1
set "G=git -c safe.directory=*"
%G% init -q
%G% symbolic-ref HEAD refs/heads/main
%G% config --local user.name  "webgantt-deploy"
%G% config --local user.email "deploy@example.com"
%G% config --local core.autocrlf false
%G% add -A
%G% commit -q -m "Deploy WebGantt (mode=%MODE%)"
if errorlevel 1 ( echo [ERROR] commit failed. & popd & goto :fail )

rem ---- decide how to publish ----
if defined REPOURL goto :push_existing

where gh >nul 2>&1
if errorlevel 1 goto :manual
echo(
echo gh CLI detected. Creating repository "%REPO%" and pushing...
gh repo create "%REPO%" --public --source . --remote origin --push
if errorlevel 1 ( echo [WARN] gh create failed. Falling back to manual. & goto :manual )
for /f "delims=" %%U in ('gh api user --jq .login 2^>nul') do set "OWNER=%%U"
goto :after_push

:push_existing
echo(
echo Pushing to existing repository:
echo    %REPOURL%
echo (If prompted: Username = your GitHub name, Password = a Personal Access Token)
%G% remote add origin "%REPOURL%" 2>nul
%G% push -u origin main
if errorlevel 1 ( echo [ERROR] push failed. Check URL / credentials / token. & popd & goto :fail )
goto :after_push

:manual
echo(
echo === Manual mode ===
echo Create an EMPTY "Public" repository on github.com first (no README/.gitignore).
set "URL="
set /p "URL=Paste the repo URL (e.g. https://github.com/USER/REPO.git): "
if "%URL%"=="" (
  echo [ABORT] No URL entered. Run later from "%BUILD%":
  echo     git remote add origin ^<URL^>
  echo     git push -u origin main
  popd
  goto :done
)
set URL=%URL:"=%
set "REPOURL=%URL%"
call :derive
%G% remote add origin "%REPOURL%" 2>nul
%G% push -u origin main
if errorlevel 1 ( echo [ERROR] push failed. Check URL / credentials / token. & popd & goto :fail )
goto :after_push

:after_push
where gh >nul 2>&1
if errorlevel 1 goto :after_msg
if defined OWNER gh api -X POST "repos/%OWNER%/%REPO%/pages" -f "source[branch]=main" -f "source[path]=/" >nul 2>nul
:after_msg
echo(
echo ============================================================
echo  Push complete!
if defined OWNER echo  After enabling Pages, the site will be at:
if defined OWNER echo     https://%OWNER%.github.io/%REPO%/
echo  Enable GitHub Pages:
echo     GitHub repo -^> Settings -^> Pages -^>
echo     Build and deployment: Branch = main / (root) -^> Save
echo ============================================================
popd
goto :done

:nogit
echo(
echo [ERROR] git is required. Install from https://git-scm.com/ and re-run.
goto :fail

:fail
echo(
echo *** Setup aborted ***
endlocal
pause
exit /b 1

:done
echo(
echo Notes:
echo  - gist mode: users log in with a GitHub Fine-grained PAT
echo    (Gists: Read and write). Data is encrypted in each user's private Gist.
echo  - Re-running rebuilds the _deploy folder. Add "_deploy" to the parent
echo    repo .gitignore to avoid nested-repo commits.
endlocal
pause
exit /b 0

rem ============================================================
rem  subroutine: derive OWNER and REPO from REPOURL
rem ============================================================
:derive
set "REPOPATH=%REPOURL%"
set "REPOPATH=%REPOPATH:*github.com/=%"
set "REPOPATH=%REPOPATH:*github.com:=%"
set "REPOPATH=%REPOPATH:.git=%"
if "%REPOPATH:~-1%"=="/" set "REPOPATH=%REPOPATH:~0,-1%"
for /f "tokens=1,2 delims=/" %%a in ("%REPOPATH%") do set "OWNER=%%a"& set "REPO=%%b"
exit /b
