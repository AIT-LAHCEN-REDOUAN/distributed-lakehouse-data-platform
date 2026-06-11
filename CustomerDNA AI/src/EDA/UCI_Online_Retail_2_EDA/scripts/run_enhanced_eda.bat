@echo off
REM CustomerDNA AI - PFE Project
REM Batch Execution Script for UCI Online Retail 2 Enhanced EDA
REM Author: PFE Student
REM Description: Traditional batch execution script for command prompt users

echo ================================================================
echo UCI ONLINE RETAIL 2 - ENHANCED EDA
echo ================================================================
echo.

REM Check for help parameter
if "%1"=="-help" goto HELP
if "%1"=="--help" goto HELP
if "%1"=="/?" goto HELP

echo PRE-FLIGHT CHECKS
echo -----------------
echo.

REM 1. Check Python installation
echo 1. Checking Python installation...
python --version >nul 2>&1
if %errorlevel% equ 0 (
    python --version
    echo    [OK] Python found
) else (
    echo    [ERROR] Python not found or not in PATH
    echo    Please install Python 3.7+ and add it to your PATH
    goto ERROR_EXIT
)

REM 2. Check Python packages
echo.
echo 2. Checking required Python packages...
echo    Checking pandas...
python -c "import pandas" >nul 2>&1
if %errorlevel% neq 0 (
    echo    [MISSING] pandas
    set MISSING_PACKAGES=1
) else (
    echo    [OK] pandas
)

echo    Checking numpy...
python -c "import numpy" >nul 2>&1
if %errorlevel% neq 0 (
    echo    [MISSING] numpy
    set MISSING_PACKAGES=1
) else (
    echo    [OK] numpy
)

echo    Checking matplotlib...
python -c "import matplotlib" >nul 2>&1
if %errorlevel% neq 0 (
    echo    [MISSING] matplotlib
    set MISSING_PACKAGES=1
) else (
    echo    [OK] matplotlib
)

echo    Checking seaborn...
python -c "import seaborn" >nul 2>&1
if %errorlevel% neq 0 (
    echo    [MISSING] seaborn
    set MISSING_PACKAGES=1
) else (
    echo    [OK] seaborn
)

REM Check if any packages are missing
if defined MISSING_PACKAGES (
    echo.
    echo    [WARNING] Some required packages are missing
    echo    Install missing packages with: pip install pandas numpy matplotlib seaborn
    echo.
    set /p CONTINUE="Continue anyway? (y/n): "
    if /i not "%CONTINUE%"=="y" goto ERROR_EXIT
)

REM 3. Check data file
echo.
echo 3. Checking data file...
set DATA_PATH=d:\github\Master_PFE_Project\CustomerDNA AI\base_dataset\UCI_Online_Retail_2\online_retail_2.xlsx

if exist "%DATA_PATH%" (
    for %%F in ("%DATA_PATH%") do set FILESIZE=%%~zF
    set /a FILESIZE_MB=%FILESIZE%/1048576
    echo    [OK] Data file found: %DATA_PATH%
    echo    File size: %FILESIZE_MB% MB
) else (
    echo    [ERROR] Data file not found: %DATA_PATH%
    echo    Please verify the file exists at the specified location
    goto ERROR_EXIT
)

REM 4. Check output directory
echo.
echo 4. Checking output directory...
set OUTPUT_DIR=d:\github\Master_PFE_Project\CustomerDNA AI\src\EDA\UCI_Online_Retail_2_EDA\output

if not exist "%OUTPUT_DIR%" (
    echo    Creating output directory: %OUTPUT_DIR%
    mkdir "%OUTPUT_DIR%"
)

if exist "%OUTPUT_DIR%" (
    echo    [OK] Output directory: %OUTPUT_DIR%
    
    REM Test write permissions
    echo Test > "%OUTPUT_DIR%\test_write.txt" 2>nul
    if exist "%OUTPUT_DIR%\test_write.txt" (
        del "%OUTPUT_DIR%\test_write.txt"
        echo    Write permissions verified
    ) else (
        echo    [WARNING] Cannot write to output directory
        echo    Check directory permissions
    )
) else (
    echo    [ERROR] Cannot create output directory
    goto ERROR_EXIT
)

echo.
echo ANALYSIS EXECUTION
echo ------------------
echo.

REM 5. Run the EDA analysis
echo 5. Starting EDA analysis...
set SCRIPT_PATH=%~dp0enhanced_online_retail_eda.py

if exist "%SCRIPT_PATH%" (
    echo    Running: python "%SCRIPT_PATH%"
    echo.
    
    REM Record start time
    for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set DATETIME=%%I
    set START_HOUR=%DATETIME:~8,2%
    set START_MIN=%DATETIME:~10,2%
    set START_SEC=%DATETIME:~12,2%
    
    REM Run the Python script
    python "%SCRIPT_PATH%"
    
    if %errorlevel% equ 0 (
        REM Record end time
        for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set DATETIME=%%I
        set END_HOUR=%DATETIME:~8,2%
        set END_MIN=%DATETIME:~10,2%
        set END_SEC=%DATETIME:~12,2%
        
        REM Calculate duration
        set /a DURATION=(%END_HOUR%*3600 + %END_MIN%*60 + %END_SEC%) - (%START_HOUR%*3600 + %START_MIN%*60 + %START_SEC%)
        set /a DURATION_H=%DURATION%/3600
        set /a DURATION_M=(%DURATION% %% 3600)/60
        set /a DURATION_S=%DURATION% %% 60
        
        echo.
        echo    [SUCCESS] EDA analysis completed successfully!
        echo    Duration: %DURATION_H%:%DURATION_M%:%DURATION_S%
    ) else (
        echo.
        echo    [ERROR] EDA analysis failed with exit code: %errorlevel%
        goto ERROR_EXIT
    )
) else (
    echo    [ERROR] EDA script not found: %SCRIPT_PATH%
    goto ERROR_EXIT
)

echo.
echo ANALYSIS COMPLETION
echo -------------------
echo.

echo [SUCCESS] EDA analysis completed!
echo.
echo Generated outputs:
echo • Comprehensive EDA report (comprehensive_eda_report.txt)
echo • Executive summary (executive_summary.txt)
echo • Visualization catalog (visualization_catalog.txt)
echo • 8 main visualization files (30+ individual charts)
echo.
echo Next steps:
echo 1. Review the comprehensive report for detailed findings
echo 2. Examine visualizations for key business insights
echo 3. Use RFM analysis for customer segmentation
echo 4. Apply temporal patterns for inventory optimization
echo 5. Leverage geographic analysis for market expansion
echo.

goto SUCCESS_EXIT

:HELP
echo USAGE:
echo   run_enhanced_eda.bat [-help]
echo.
echo PARAMETERS:
echo   -help    : Display this help message
echo.
echo EXAMPLES:
echo   run_enhanced_eda.bat
echo   run_enhanced_eda.bat -help
echo.
echo This script runs the comprehensive EDA analysis for the UCI Online Retail 2 dataset.
echo It performs pre-flight checks for Python installation and required packages.
echo.
goto EXIT

:ERROR_EXIT
echo.
echo ================================================================
echo ANALYSIS FAILED
echo ================================================================
echo.
echo Troubleshooting steps:
echo 1. Verify Python installation and PATH configuration
echo 2. Install required packages: pip install pandas numpy matplotlib seaborn
echo 3. Check data file accessibility at specified path
echo 4. Ensure sufficient disk space for output files
echo 5. Run the script as administrator if permission issues occur
echo.
pause
exit /b 1

:SUCCESS_EXIT
echo.
echo ================================================================
echo ANALYSIS FINISHED
echo ================================================================
echo.
pause
exit /b 0

:EXIT
pause
exit /b 0