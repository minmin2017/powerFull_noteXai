Add-Type -AssemblyName presentationCore
$resolved = Resolve-Path $args[0]
$uri = New-Object System.Uri($resolved.Path)
$player = New-Object System.Windows.Media.MediaPlayer
$player.Open($uri)

# Wait for media duration metadata to load
$maxWait = 30
while (-not $player.NaturalDuration.HasTimeSpan -and $maxWait -gt 0) {
    Start-Sleep -Milliseconds 100
    $maxWait--
}

$player.Play()
Start-Sleep -Milliseconds 300

# Dynamically wait until audio finishes playing completely
while ($player.NaturalDuration.HasTimeSpan -and $player.Position -lt $player.NaturalDuration.TimeSpan) {
    Start-Sleep -Milliseconds 200
}

# Extra safety buffer before closing
Start-Sleep -Milliseconds 400
$player.Close()
