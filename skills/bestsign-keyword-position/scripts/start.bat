@echo off
chcp 65001 >nul
cd /d "%~dp0..\..\.."
set PYTHON=C:\Users\wanglanzhou\.workbuddy\binaries\python\envs\default\Scripts\python.exe
echo 鍚姩 PDF 鍏抽敭瀛楀潗鏍囧畾浣嶆湇鍔?..
%PYTHON% .workbuddy\skills\bestsign-keyword-position\scripts\server.py
pause
