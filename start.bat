ECHO OFF
set old=%CD%
IF NOT EXIST twistd.py set /P version=Please specify your version of python: 'Python26', 'Python25', or 'Python27'
IF NOT EXIST twistd.py set PATH=%PATH%;\%version%;\%version%\scripts
IF NOT EXIST twistd.py set PATHEXT=%PATHEXT%;.py;.pyc;.pyw;.pyo
IF NOT EXIST twistd.py copy \%version%\Scripts\Twistd.py %old%
IF EXIST twistd.py python twistd.py -y bravo.tac
pause