param(
    [string]$Deck = (Join-Path $PSScriptRoot 'BCS超导理论与计算入门.pptx'),
    [string]$OutDir = (Join-Path $PSScriptRoot 'preview')
)
$ErrorActionPreference = 'Stop'
$Deck = (Resolve-Path -LiteralPath $Deck).Path
$OutDir = [System.IO.Path]::GetFullPath($OutDir)
New-Item -ItemType Directory -Path $OutDir -Force | Out-Null
$app = $null
$presentation = $null
try {
    $app = New-Object -ComObject PowerPoint.Application
    # WithWindow=false keeps the export non-interactive.
    $presentation = $app.Presentations.Open($Deck, $true, $false, $false)
    $presentation.Export($OutDir, 'PNG', 1600, 900)
    $pdfName = [System.IO.Path]::GetFileNameWithoutExtension($Deck) + '.pdf'
    $presentation.SaveAs((Join-Path $OutDir $pdfName), 32)
    Write-Output ('Rendered slides: ' + $presentation.Slides.Count)
}
finally {
    if ($null -ne $presentation) {
        $presentation.Close()
        [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($presentation)
    }
    if ($null -ne $app) {
        $app.Quit()
        [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($app)
    }
}
