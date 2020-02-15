@echo off

title Collect 2019 nCoV realtime
D:
cd D:\MyData\PythonProjects\py3\nCoV2019

:start
echo Collect data started: %date:~0,10% %time:~0,8%
python china_data_mining.py
echo last collected time: %date:~0,10% %time:~0,8%
choice /t 1794 /d y /n >nul

goto start
pause