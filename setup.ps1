Write-Host "Setting up environment for Blockchain Donation Application..." -ForegroundColor Green

# Try to find Python 3.10
$pythonCmd = $null

# Check if Python in PATH is 3.10
try {
    $version = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
    if ($version -eq "3.10") {
        $pythonCmd = "python"
    }
} catch {
    # Python not in path or not working
}

# Check common installation paths if not found in PATH
if (-not $pythonCmd) {
    $commonPaths = @(
        "C:\Python310\python.exe",
        "C:\Program Files\Python310\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe"
    )

    foreach ($path in $commonPaths) {
        if (Test-Path $path) {
            $pythonCmd = $path
            break
        }
    }
}

# If Python 3.10 wasn't found automatically, ask user for path
if (-not $pythonCmd) {
    Write-Host "Python 3.10 was not found in PATH or standard locations." -ForegroundColor Yellow
    Write-Host "Please enter the full path to python.exe for Python 3.10 (e.g., C:\Path\To\Python310\python.exe):"
    $pythonPath = Read-Host
    
    if (Test-Path $pythonPath) {
        $pythonCmd = $pythonPath
    } else {
        Write-Host "The specified path does not exist." -ForegroundColor Red
        Write-Host "Please install Python 3.10 or provide a valid path." -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit
    }
}

Write-Host "Found Python 3.10: $pythonCmd" -ForegroundColor Green

# Create virtual environment if it doesn't exist
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Green
    & $pythonCmd -m venv venv
}

# Activate virtual environment and install dependencies
Write-Host "Activating virtual environment and installing dependencies..." -ForegroundColor Green
& .\venv\Scripts\Activate.ps1
pip install -r requirements.txt

Write-Host "`nSetup complete! Run the application with:" -ForegroundColor Green
Write-Host ".\venv\Scripts\Activate.ps1" -ForegroundColor Cyan
Write-Host "python app.py" -ForegroundColor Cyan
Read-Host "Press Enter to continue" 