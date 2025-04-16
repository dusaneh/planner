@echo off
REM Create directories
mkdir routers
mkdir core
mkdir models
mkdir config

REM Create empty Python files
type nul > main.py
type nul > routers\admin.py
type nul > core\config_manager.py
type nul > models\planner.py
type nul > models\user.py
type nul > models\tool.py
type nul > models\content.py

REM Create empty JSON config files
type nul > config\planner.json
type nul > config\user.json
type nul > config\tools.json
type nul > config\content.json

echo Directory structure and files created successfully.
