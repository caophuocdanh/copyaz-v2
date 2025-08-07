pip install -r requirements.txt
rmdir /S /Q build
rmdir /S /Q dist

pyinstaller --onefile --noconsole --icon="wb.ico" --hidden-import="jinja2" --hidden-import="werkzeug" --name=wb wb.py
pyinstaller --onefile --windowed --icon="icon.ico" --name "CopyAZ" --hidden-import "win32timezone" CopyAZ.py
pyinstaller --onefile --console --icon="server.ico" --name "CopyAZServer-Console" --hidden-import "win32timezone" CopyAZServer.py
pyinstaller --onefile --noconsole --icon="server.ico" --name "CopyAZServer" --hidden-import "win32timezone" CopyAZServer.py
copy config.ini dist

rmdir /S /Q build
del /f *.spec