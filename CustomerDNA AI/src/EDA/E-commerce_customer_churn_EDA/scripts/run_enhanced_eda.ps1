param(
    [string]$OutputDir,
    [switch]$Help,
    [switch]$Verbose
)

# Set execution policy for current process
$ErrorActionPreference = "Stop"

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "E-COMMERCE CUSTOMER CHURN - ENHANCED EDA" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# Display help if requested
if ($Help) {
    Write-Host "Usage: .\run_enhanced_eda.ps1 [options]" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Options:" -ForegroundColor Yellow
    Write-Host "  -OutputDir <path>    : Specify custom output directory" -ForegroundColor Yellow
    Write-Host "  -Help                : Display this help message" -ForegroundColor Yellow
    Write-Host "  -Verbose             : Enable verbose output" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Example:" -ForegroundColor Yellow
    Write-Host "  .\run_enhanced_eda.ps1 -Verbose" -ForegroundColor Yellow
    Write-Host "  .\run_enhanced_eda.ps1 -OutputDir C:\MyAnalysis\output" -ForegroundColor Yellow
    Write-Host ""
    exit 0
}

# Check Python installation
Write-Host "Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Python not found or not in PATH"
    }
    Write-Host "  [SUCCESS] Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "  Please install Python 3.7 or higher and ensure it's in your PATH" -ForegroundColor Yellow
    exit 1
}

# Check Python version
Write-Host "Checking Python version..." -ForegroundColor Yellow
try {
    $versionOutput = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
    $majorVersion = [int]$versionOutput.Split('.')[0]
    $minorVersion = [int]$versionOutput.Split('.')[1]
    
    if ($majorVersion -lt 3 -or ($majorVersion -eq 3 -and $minorVersion -lt 7)) {
        throw "Python version $versionOutput is below minimum required version 3.7"
    }
    Write-Host "  [SUCCESS] Python version $versionOutput meets requirements" -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "  Please upgrade to Python 3.7 or higher" -ForegroundColor Yellow
    exit 1
}

# Check required Python packages
Write-Host "Checking required Python packages..." -ForegroundColor Yellow
$requiredPackages = @("pandas", "numpy", "matplotlib", "seaborn", "openpyxl")
$missingPackages = @()

foreach ($package in $requiredPackages) {
    try {
        $check = python -c "import $package; print('OK')" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  [SUCCESS] $package is installed" -ForegroundColor Green
        } else {
            $missingPackages += $package
            Write-Host "  [WARNING] $package is not installed" -ForegroundColor Yellow
        }
    } catch {
        $missingPackages += $package
        Write-Host "  [WARNING] $package is not installed" -ForegroundColor Yellow
    }
}

# Check optional packages
Write-Host "Checking optional Python packages..." -ForegroundColor Yellow
$optionalPackages = @("scipy", "scikit-learn", "plotly", "networkx")
$optionalMissing = @()

foreach ($package in $optionalPackages) {
    try {
        $check = python -c "import $package; print('OK')" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  [INFO] $package is installed (optional)" -ForegroundColor Cyan
        } else {
            $optionalMissing += $package
            Write-Host "  [INFO] $package is not installed (optional)" -ForegroundColor Gray
        }
    } catch {
        $optionalMissing += $package
        Write-Host "  [INFO] $package is not installed (optional)" -ForegroundColor Gray
    }
}

# Warn about missing required packages
if ($missingPackages.Count -gt 0) {
    Write-Host ""
    Write-Host "  [ERROR] Missing required packages: $($missingPackages -join ', ')" -ForegroundColor Red
    Write-Host "  Please install missing packages using: pip install $($missingPackages -join ' ')" -ForegroundColor Yellow
    exit 1
}

# Check data file exists
Write-Host "Checking data file..." -ForegroundColor Yellow
$dataPath = "d:\github\Master_PFE_Project\CustomerDNA AI\base_dataset\E-commerce_customer_churn\E-commerce_customer_churn.xlsx"
if (-not (Test-Path $dataPath)) {
    Write-Host "  [ERROR] Data file not found: $dataPath" -ForegroundColor Red
    Write-Host "  Please ensure the Excel file exists at the specified location" -ForegroundColor Yellow
    exit 1
}
Write-Host "  [SUCCESS] Data file found: $dataPath" -ForegroundColor Green

# Check output directory
Write-Host "Checking output directory..." -ForegroundColor Yellow
if ($OutputDir) {
    $outputPath = $OutputDir
} else {
    $outputPath = "d:\github\Master_PFE_Project\CustomerDNA AI\src\EDA\E-commerce_customer_churn_EDA\output"
}

try {
    if (-not (Test-Path $outputPath)) {
        New-Item -ItemType Directory -Force -Path $outputPath | Out-Null
        Write-Host "  [INFO] Created output directory: $outputPath" -ForegroundColor Cyan
    } else {
        Write-Host "  [INFO] Output directory exists: $outputPath" -ForegroundColor Cyan
    }
} catch {
    Write-Host "  [ERROR] Failed to create output directory: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Check logs directory
Write-Host "Checking logs directory..." -ForegroundColor Yellow
$logsPath = "d:\github\Master_PFE_Project\CustomerDNA AI\src\EDA\E-commerce_customer_churn_EDA\logs"
try {
    if (-not (Test-Path $logsPath)) {
        New-Item -ItemType Directory -Force -Path $logsPath | Out-Null
        Write-Host "  [INFO] Created logs directory: $logsPath" -ForegroundColor Cyan
    } else {
        Write-Host "  [INFO] Logs directory exists: $logsPath" -ForegroundColor Cyan
    }
} catch {
    Write-Host "  [WARNING] Failed to create logs directory: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Summary
Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "PRE-FLIGHT CHECK SUMMARY" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "Python:        $pythonVersion" -ForegroundColor White
Write-Host "Data file:     $dataPath" -ForegroundColor White
Write-Host "Output dir:    $outputPath" -ForegroundColor White
Write-Host "Logs dir:      $logsPath" -ForegroundColor White
Write-Host "Required pkgs: $($requiredPackages.Count) installed" -ForegroundColor Green
Write-Host "Optional pkgs: $($optionalPackages.Count - $optionalMissing.Count)/$($optionalPackages.Count) installed" -ForegroundColor Cyan

if ($optionalMissing.Count -gt 0) {
    Write-Host ""
    Write-Host "Note: Missing optional packages:" -ForegroundColor Yellow
    foreach ($pkg in $optionalMissing) {
        Write-Host "  - $pkg (install with: pip install $pkg)" -ForegroundColor Gray
    }
    Write-Host "  These packages enable advanced visualizations but are not required." -ForegroundColor Gray
}

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "STARTING ENHANCED EDA ANALYSIS" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# Get current directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonScript = Join-Path $scriptDir "enhanced_ecommerce_eda.py"

# Run the Python script
Write-Host "Executing: python $pythonScript" -ForegroundColor Yellow
Write-Host ""

try {
    $startTime = Get-Date
    Write-Host "Analysis started at: $startTime" -ForegroundColor Cyan
    
    # Run Python script
    python $pythonScript
    
    $endTime = Get-Date
    $duration = $endTime - $startTime
    
    Write-Host ""
    Write-Host "================================================================" -ForegroundColor Green
    Write-Host "ANALYSIS COMPLETED SUCCESSFULLY!" -ForegroundColor Green
    Write-Host "================================================================" -ForegroundColor Green
    Write-Host "Start time:  $startTime" -ForegroundColor White
    Write-Host "End time:    $endTime" -ForegroundColor White
    Write-Host "Duration:    $($duration.ToString('hh\:mm\:ss'))" -ForegroundColor White
    Write-Host ""
    Write-Host "Output files saved to:" -ForegroundColor Cyan
    Write-Host "  $outputPath" -ForegroundColor White
    
    # List generated files
    if (Test-Path $outputPath) {
        $files = Get-ChildItem -Path $outputPath -File | Select-Object -First 10
        if ($files.Count -gt 0) {
            Write-Host ""
            Write-Host "Generated files:" -ForegroundColor Cyan
            foreach ($file in $files) {
                Write-Host "  - $($file.Name) ($($file.Length/1KB).ToString('N2') KB)" -ForegroundColor Gray
            }
            if ((Get-ChildItem -Path $outputPath -File).Count -gt 10) {
                Write-Host "  ... and more" -ForegroundColor Gray
            }
        }
    }
    
    Write-Host ""
    Write-Host "Log file saved to:" -ForegroundColor Cyan
    Write-Host "  $logsPath\eda_run.log" -ForegroundColor White
    
} catch {
    Write-Host ""
    Write-Host "================================================================" -ForegroundColor Red
    Write-Host "ANALYSIS FAILED!" -ForegroundColor Red
    Write-Host "================================================================" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    
    if ($Verbose) {
        Write-Host "Full error details:" -ForegroundColor Yellow
        Write-Host $_.Exception.StackTrace -ForegroundColor Gray
    }
    
    exit 1
}

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "ANALYSIS COMPLETE" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "You can now:" -ForegroundColor White
Write-Host "1. Review the visualizations in the output folder" -ForegroundColor Gray
Write-Host "2. Check the comprehensive report for key insights" -ForegroundColor Gray
Write-Host "3. Use the findings for preprocessing and modeling" -ForegroundColor Gray
Write-Host ""

# Keep window open if running interactively
if ($Host.Name -eq "ConsoleHost") {
    Write-Host "Press any key to continue..." -ForegroundColor Gray
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}