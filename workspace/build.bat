@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul 2>&1
cd /d "%~dp0"
cl /nologo /O2 /EHsc /std:c++17 /utf-8 seed_opt.cpp /Fe:seed_opt.exe /Fo:seed_opt.obj
echo BUILD_EXITCODE=%ERRORLEVEL%
