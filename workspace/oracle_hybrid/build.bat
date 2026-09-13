@echo off
REM MSVC 빌드 (PowerShell/cmd 에서 실행)
REM   .\build.bat submission_oracle.cpp oracle
REM   .\build.bat submission_oracle.cpp oracle_st /DSINGLE_THREAD
setlocal
if "%~1"=="" goto usage

set "SRC=%~1"
set "OUT=%~2"
if "%OUT%"=="" set "OUT=%~n1"
set "EXTRA=%~3"

set "VC=C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
if not exist "%VC%" set "VC=C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"
if not exist "%VC%" goto novc

call "%VC%" >nul 2>&1
cl /nologo /utf-8 /std:c++17 /O2 /EHsc %EXTRA% /Fe:%OUT%.exe /Fo:%OUT%.obj "%SRC%"

REM MSVC/vcvars 는 성공해도 exit code 가 어긋나는 경우가 있어 파일 존재로 판정한다.
if exist "%OUT%.exe" goto ok
echo [fail] build failed
exit /b 1

:ok
echo [ok] -^> %OUT%.exe
exit /b 0

:novc
echo [fail] vcvars64.bat not found
exit /b 1

:usage
echo usage: build.bat SOURCE.cpp [OUTNAME] [/DSINGLE_THREAD]
exit /b 2
