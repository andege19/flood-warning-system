@echo off
REM Schedule to run every 2 hours
REM Place this in Windows Task Scheduler

:loop
echo.
echo [%date% %time%] Running flood warning system tasks...
python manage.py run_all_tasks
echo.
echo Next run in 2 hours...
timeout /t 7200 /nobreak
goto loop