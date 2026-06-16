# gemini-loop.ps1 - Autonomous loop for Gemini CLI
# This script polls the inbox and prints messages to the terminal.
# It helps the Gemini CLI "see" what's happening in the app without manual checks.

$PORT = 4321
# scoped to a dedicated "gemini" section so it never steals Claude's inbox
$URL = "http://localhost:$PORT/api/inbox?section=gemini&drain=true"

Write-Host "`n  🧠 Gemini Autonomous Observer started..." -ForegroundColor Cyan
Write-Host "  Watching for messages at: $URL"
Write-Host "  (Press Ctrl+C to stop)`n"

while ($true) {
    try {
        $response = Invoke-RestMethod -Uri $URL -Method Get -ErrorAction SilentlyContinue
        if ($response -and $response.items -and $response.items.Count -gt 0) {
            foreach ($item in $response.items) {
                $time = [DateTime]::Now.ToString("HH:mm:ss")
                Write-Host "[$time] 🔔 New Message: " -NoNewline -ForegroundColor Yellow
                Write-Host $item.text -ForegroundColor White
                
                # We could trigger a CLI command here if needed, 
                # but for now we just make the message visible for Gemini to see.
            }
        }
    } catch {
        # Silent wait if server is down
    }
    Start-Sleep -Seconds 5
}
