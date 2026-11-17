@echo off
rem Zapusk GR1804 v DOSBox (Windows): papka montiruetsya kak C:
cd /d "%~dp0"
start "" dos.exe -noconsole -c "mount c ." -c "c:" -c "rus" -c "gr1804"
