$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Drawing

$outputPath = Join-Path $PSScriptRoot "ophanim.png"
$bitmap = New-Object System.Drawing.Bitmap 512, 512
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias

$background = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(6, 8, 20))
$cyanPen = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(6, 182, 212)), 22
$indigoPen = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(99, 102, 241)), 26
$purplePen = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(168, 85, 247)), 18
$centerBrush = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(99, 102, 241))
$eyeBrush = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(223, 249, 255))

try {
    $graphics.FillRectangle($background, 0, 0, 512, 512)
    $graphics.DrawEllipse($indigoPen, 92, 92, 328, 328)
    $graphics.DrawEllipse($cyanPen, 92, 182, 328, 148)
    $graphics.DrawEllipse($purplePen, 182, 92, 148, 328)
    $graphics.FillEllipse($centerBrush, 198, 198, 116, 116)
    $graphics.FillEllipse($eyeBrush, 229, 229, 54, 54)
    $bitmap.Save($outputPath, [System.Drawing.Imaging.ImageFormat]::Png)
}
finally {
    $eyeBrush.Dispose()
    $centerBrush.Dispose()
    $purplePen.Dispose()
    $indigoPen.Dispose()
    $cyanPen.Dispose()
    $background.Dispose()
    $graphics.Dispose()
    $bitmap.Dispose()
}
