$backendPath = Join-Path $PSScriptRoot "backend"
$frontendPath = Join-Path $PSScriptRoot "frontend"

Start-Process powershell.exe -WorkingDirectory $backendPath -ArgumentList @(
	"-NoExit",
	"-Command",
	"python -m uvicorn main:app --reload --port 8000"
)

Start-Process powershell.exe -WorkingDirectory $frontendPath -ArgumentList @(
	"-NoExit",
	"-Command",
	"npm run dev"
)
