@echo off
echo ========================================
echo CustomerDNA AI - Complete Library Installation
echo ========================================
echo.

echo [INFO] Installing all required libraries for Python 3.11...
echo.

REM Install core data processing libraries
echo 1. Installing core data processing libraries...
pip install pandas==2.2.0
pip install numpy==1.26.4
pip install scipy==1.13.0

REM Install database connection
echo.
echo 2. Installing database connection library...
pip install psycopg2-binary==2.9.9

REM Install machine learning & analytics
echo.
echo 3. Installing machine learning & analytics libraries...
pip install scikit-learn==1.5.0
pip install matplotlib==3.8.4
pip install seaborn==0.13.2

REM Install utilities
echo.
echo 4. Installing utility libraries...
pip install python-dotenv==1.0.1
pip install tqdm==4.66.2
pip install openpyxl==3.1.2

echo.
echo ========================================
echo ✅ Installation Complete!
echo ========================================
echo.
echo 📋 Next steps:
echo   1. Run: python verify_installation.py
echo   2. Check all libraries are installed correctly
echo   3. Proceed with data warehouse setup
echo.
pause