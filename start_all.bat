@echo off
cd /d C:\Users\lianxiang\WorkBuddy\2026-07-23-09-09-54

start "LocalGallery :8090" cmd /k "py serve_local_gallery.py"
start "DeployGallery :8091" cmd /k "py serve_deploy_gallery.py"
start "XChecker :8000" cmd /k "cd /d D:\PromptHunter && py server.py"

echo.
echo  Three local servers launched in separate windows:
echo    http://localhost:8000  X Checker     (D:\PromptHunter\server.py)
echo    http://localhost:8090  Local Gallery (shuixian-prompts)
echo    http://localhost:8091  Deploy Gallery(shuixian-deploy)
echo.
echo  Close a window to stop that service. Or double-click a start_*.bat to launch one.
echo.
pause
