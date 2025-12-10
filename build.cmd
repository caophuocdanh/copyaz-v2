@echo off
ECHO Building project CopyAZ...
ECHO.

ECHO [1/5] Cleaning up old builds and artifacts...
IF EXIST build ( rmdir /S /Q build )
IF EXIST dist ( rmdir /S /Q dist )
IF EXIST wb.exe ( del wb.exe )
del /f *.spec > nul 2>&1
ECHO Done.
ECHO.

ECHO [2/5] Building Web Server (wb.exe)...
pyinstaller --onefile --noconsole --icon="wb.ico" --name=wb wb.py
IF NOT EXIST dist\wb.exe (
    ECHO ERROR: Failed to build wb.exe. Aborting.
    GOTO :EOF
)
ECHO Done.
ECHO.

ECHO [3/5] Building Main Application (CopyAZ.exe)...
ECHO      (This will bundle wb.exe from the previous step)
pyinstaller --onefile --windowed --icon="icon.ico" --name "CopyAZ" --hidden-import "win32timezone" --add-data "icon.ico;." CopyAZ.py
ECHO Done.
ECHO.

ECHO [4/5] Building Server (CopyAZServer.exe)...
pyinstaller --onefile --noconsole --icon="server.ico" --name "CopyAZServer" --hidden-import "win32timezone" CopyAZServer.py
ECHO Done.
ECHO.

ECHO [5/5] Finalizing and cleaning up...
rmdir /S /Q build
del /f *.spec
ECHO Done.
ECHO.

ECHO.
ECHO =======================================================
ECHO  BUILD COMPLETE!
ECHO  All executables are in the 'dist' folder.
ECHO =======================================================
