#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Run Enhanced EDA for Retailrocket Recommender System Dataset

.DESCRIPTION
    This script executes the comprehensive exploratory data analysis (EDA) for the
    Retailrocket e-commerce recommender system dataset. It generates visualizations,
    statistical summaries, and insights for building effective recommendation systems.

.PARAMETER OutputDir
    Optional output directory for results. Defaults to the configured output directory.

.PARAMETER SampleSize
    Optional sample size for performance optimization. Defaults to 100,000.

.EXAMPLE
    .\run_enhanced_eda.ps1

.EXAMPLE
    .\run_enhanced_eda.ps1 -OutputDir "C:\MyResults" -SampleSize 50000

.NOTES
    Author: Retailrocket EDA Team
    Date: 2026-06-02
    Version: 1.0.0
#>

param(
    [string]$OutputDir,
    [int]$SampleSize = 100000
)

# Set execution policy for current process
$ErrorActionPreference = "Stop"

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "RETAILROCKET RECOMMENDER SYSTEM - ENHANCED EDA" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# Check Python installation
Write-Host "Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Python not found or not in PATH"
    }
    Write-Host "  [OK] Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "  Please install Python 3.7 or higher and ensure it's in your PATH" -ForegroundColor Yellow
    exit 1
}

# Check required Python packages
Write-Host "Checking required Python packages..." -ForegroundColor Yellow
$requiredPackages = @("pandas", "numpy", "matplotlib", "seaborn")

foreach ($package in $requiredPackages) {
    try {
        $check = python -c "import $package; print('OK')" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  [OK] $package installed" -ForegroundColor Green
        } else {
            Write-Host "  [WARNING] $package not installed" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  [WARNING] $package not installed" -ForegroundColor Yellow
    }
}

# Set environment variables if parameters provided
if ($OutputDir) {
    $env:OUTPUT_DIR = $OutputDir
    Write-Host "  [INFO] Output directory set to: $OutputDir" -ForegroundColor Blue
}

if ($SampleSize -ne 100000) {
    $env:SAMPLE_SIZE = $SampleSize.ToString()
    Write-Host "  [INFO] Sample size set to: $SampleSize" -ForegroundColor Blue
}

# Run the EDA script
Write-Host ""
Write-Host "Starting comprehensive EDA analysis..." -ForegroundColor Cyan
Write-Host "This may take several minutes depending on your system performance." -ForegroundColor Yellow
Write-Host ""

$scriptPath = Join-Path $PSScriptRoot "enhanced_retailrocket_eda.py"

try {
    # Run the Python script
    python $scriptPath
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "================================================================" -ForegroundColor Green
        Write-Host "[SUCCESS] EDA completed successfully!" -ForegroundColor Green
        Write-Host "================================================================" -ForegroundColor Green
        
        # Display summary of generated files
        $outputPath = if ($OutputDir) { $OutputDir } else { 
            Join-Path (Split-Path $PSScriptRoot -Parent) "output" 
        }
        
        if (Test-Path $outputPath) {
            $files = Get-ChildItem $outputPath -File
            Write-Host ""
            Write-Host "Generated files in $outputPath :" -ForegroundColor Cyan
            Write-Host "----------------------------------------" -ForegroundColor Cyan
            
            # Group files by type
            $pngFiles = $files | Where-Object { $_.Extension -eq '.png' }
            $txtFiles = $files | Where-Object { $_.Extension -eq '.txt' }
            $jsonFiles = $files | Where-Object { $_.Extension -eq '.json' }
            
            if ($pngFiles.Count -gt 0) {
                Write-Host "  Visualizations ($($pngFiles.Count) files):" -ForegroundColor Yellow
                foreach ($file in $pngFiles) {
                    Write-Host "    - $($file.Name)" -ForegroundColor White
                }
                Write-Host ""
            }
            
            if ($txtFiles.Count -gt 0) {
                Write-Host "  Reports ($($txtFiles.Count) files):" -ForegroundColor Yellow
                foreach ($file in $txtFiles) {
                    Write-Host "    - $($file.Name)" -ForegroundColor White
                }
                Write-Host ""
            }
            
            if ($jsonFiles.Count -gt 0) {
                Write-Host "  Data files ($($jsonFiles.Count) files):" -ForegroundColor Yellow
                foreach ($file in $jsonFiles) {
                    Write-Host "    - $($file.Name)" -ForegroundColor White
                }
            }
            
            Write-Host ""
            Write-Host "Key files to review:" -ForegroundColor Cyan
            Write-Host "  1. comprehensive_eda_report.txt - Complete analysis summary" -ForegroundColor White
            Write-Host "  2. eda_results.json - Detailed statistics in JSON format" -ForegroundColor White
            Write-Host "  3. event_type_distribution.png - Event distribution visualization" -ForegroundColor White
            Write-Host ""
            
        } else {
            Write-Host "  [WARNING] Output directory not found: $outputPath" -ForegroundColor Yellow
        }
        
    } else {
        Write-Host ""
        Write-Host "================================================================" -ForegroundColor Red
        Write-Host "[FAILED] EDA analysis failed with exit code: $LASTEXITCODE" -ForegroundColor Red
        Write-Host "================================================================" -ForegroundColor Red
        exit $LASTEXITCODE
    }
    
} catch {
    Write-Host ""
    Write-Host "================================================================" -ForegroundColor Red
    Write-Host "[ERROR] Unexpected error occurred:" -ForegroundColor Red
    Write-Host "  $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "================================================================" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Analysis completed at: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
Write-Host "Check the output directory for all generated files and reports." -ForegroundColor Cyan
Write-Host ""