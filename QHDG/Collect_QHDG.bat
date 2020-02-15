@echo off

title Collect QHDG Communities
D:
cd D:\MyData\PythonProjects\py3\nCoV2019\QHDG

:start
echo Collect QHDG communities started: %date:~0,10% %time:~0,8%
python qhdg_community.py
echo last QHDG communities collected time: %date:~0,10% %time:~0,8%
choice /t 10790 /d y /n >nul

goto start
pause