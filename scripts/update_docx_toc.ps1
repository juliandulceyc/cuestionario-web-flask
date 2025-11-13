# Script PowerShell para actualizar los campos (incluida la Tabla de Contenido) de un .docx
# Uso: desde PowerShell en la raíz del repo:
# powershell -ExecutionPolicy Bypass -File .\scripts\update_docx_toc.ps1 -Path docs\Manual_Tecnico_Completo.docx
param(
    [string] $Path = "docs\Manual_Tecnico_Completo.docx"
)

if (-not (Test-Path $Path)) {
    Write-Error "Archivo no encontrado: $Path"
    exit 1
}

# Crear objeto COM de Word
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$null = [void] $word.DisplayAlerts = 0

$fullPath = (Resolve-Path $Path).Path
$doc = $word.Documents.Open($fullPath)

# Actualizar todos los campos
$doc.Fields | ForEach-Object { $_.Update() }
# Actualizar tablas de contenido si existen
if ($doc.TablesOfContents.Count -gt 0) {
    $doc.TablesOfContents | ForEach-Object { $_.Update() }
}

# Guardar y cerrar
$doc.Save()
$doc.Close()
$word.Quit()

Write-Host "Campos y TOC actualizados y archivo guardado: $Path" -ForegroundColor Green
