@echo off
REM =================================================================
REM Retailrocket Recommender System - Enhanced EDA Runner
REM =================================================================
REM This batch file runs the comprehensive exploratory data analysis
REM for the Retailrocket e-commerce recommender system dataset.
REM
REM Usage: run_enhanced_eda.bat [output_dir] [sample_size]
REM
REM Example: run_enhanced_eda.bat C:\MyResults 50000
REM =================================================================

echo.
echo ================================================================
echo RETAILROCKET RECOMMENDER SYSTEM - ENHANCED EDA
echo ================================================================
echo.

REM Check if Python is installed
echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo   [ERROR] Python is not installed or not in PATH
    echo   Please install Python 3.7 or higher and ensure it's in your PATH
    pause
    exit /b 1
)
echo   [OK] Python found

REM Set environment variables from command line arguments
if not "%1"=="" (
    set OUTPUT_DIR=%1
    echo   [INFO] Output directory set to: %1
)

if not "%2"=="" (
    set SAMPLE_SIZE=%2
    echo   [INFO] Sample size set to: %2
)

REM Run the Python script
echo.
echo Starting comprehensive EDA analysis...
echo This may take several minutes depending on your system performance.
echo.

python enhanced_retailrocket_eda.py

if errorlevel 1 (
    echo.
    echo ================================================================
    echo [FAILED] EDA analysis failed with exit code: %errorlevel%
    echo ================================================================
    pause
    exit /b %errorlevel%
)

echo.
echo ================================================================
echo [SUCCESS] EDA completed successfully!
echo ================================================================
echo.

REM Display summary
set OUTPUT_PATH=..\output
if not "%OUTPUT_DIR%"=="" set OUTPUT_PATH=%OUTPUT_DIR%

if exist "%OUTPUT_PATH%" (
    echo Generated files in %OUTPUT_PATH% :
    echo ----------------------------------------
    
    REM Count files by type
    dir /b "%OUTPUT_PATH%\*.png" >nul 2>&1
    if not errorlevel 1 (
        echo   Visualizations:
        for %%f in ("%OUTPUT_PATH%\*.png") do echo     - %%~nxf
        echo.
    )
    
    dir /b "%OUTPUT_PATH%\*.txt" >nul 2>&1
    if not errorlevel 1 (
        echo   Reports:
        for %%f in ("%OUTPUT_PATH%\*.txt") do echo     - %%~nxf
        echo.
    )
    
    dir /b "%OUTPUT_PATH%\*.json" >nul 2>&1
    if not errorlevel 1 (
        echo   Data files:
        for %%f in ("%OUTPUT_PATH%\*.json") do echo     - %%~nxf
    )
    
    echo.
    echo Key files to review:
    echo   1. comprehensive_eda_report.txt - Complete analysis summary
    echo   2. eda_results.json - Detailed statistics in JSON format
    echo   3. event_type_distribution.png - Event distribution visualization
    echo.
) else (
    echo   [WARNING] Output directory not found: %OUTPUT_PATH%
    echo.
)

echo Analysis completed at: %date% %time%
echo Check the output directory for all generated files and reports.
echo.

pause