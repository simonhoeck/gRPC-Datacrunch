# MongoDB-Verbindungsdaten
$mongoHost = "ATRAPC0114"
$mongoPort = "27017"
$user = "admin"
$pass = "SecurePasswort123"

Write-Host "Teste Verbindung zu MongoDB auf ${mongoHost}:${mongoPort} ..."

try {
    # URI korrekt maskiert
    $uri = "mongodb://${user}:$pass@${mongoHost}:${mongoPort}/?authSource=admin"

    $result = mongosh "$uri" --eval "db.runCommand({ ping: 1 })"

    if ($result -match '"ok" : 1') {
        Write-Host "✅ Verbindung erfolgreich!" -ForegroundColor Green
    } else {
        Write-Host "⚠ Verbindung hergestellt, aber Ping fehlgeschlagen." -ForegroundColor Yellow
        Write-Host $result
    }
}
catch {
    Write-Host "❌ Verbindung fehlgeschlagen!" -ForegroundColor Red
    Write-Host $_
}