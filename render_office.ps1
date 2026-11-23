param([string]$Root = $PSScriptRoot)
$ErrorActionPreference = 'Stop'
$outdir = Join-Path $Root 'deliverables'
$previewdir = Join-Path $outdir 'slide_previews'
New-Item -ItemType Directory -Force -Path $previewdir | Out-Null
$status = [System.Collections.Generic.List[string]]::new()
$word = $null
try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $word.AutomationSecurity = 3
    foreach ($name in @('Bao_cao_Gamer_Clustering','Bai_noi_va_Hoi_dap')) {
        $path = Join-Path $outdir ($name + '.docx')
        $document = $word.Documents.Open($path,$false,$true,$false)
        # Word cập nhật trường theo w:updateFields khi mở; không gọi Fields.Update
        # toàn bộ vì một số cấu hình Office bị kẹt khi xử lý TOC qua COM.
        Write-Output "Opened read-only: $name"
        $temporaryPdf = Join-Path $outdir ($name + '.' + [guid]::NewGuid().ToString('N') + '.pdf')
        $document.ExportAsFixedFormat($temporaryPdf,17)
        $document.Close(0)
        Move-Item -LiteralPath $temporaryPdf -Destination (Join-Path $outdir ($name + '.pdf')) -Force
        $status.Add("Word export OK (read-only): $name")
    }
} catch { $status.Add('Word export ERROR: ' + $_.Exception.Message) }
finally { if ($null -ne $word) { $word.Quit(); [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) } }
$ppt = $null
try {
    $ppt = New-Object -ComObject PowerPoint.Application
    $presentation = $ppt.Presentations.Open((Join-Path $outdir 'Thuyet_trinh_Gamer_Clustering.pptx'),0,0,0)
    $animations = 0
    foreach ($slide in $presentation.Slides) {
        # ppEffectFade = 1793; animation fade = 10, after previous = 3.
        $slide.SlideShowTransition.EntryEffect = 1793
        $slide.SlideShowTransition.AdvanceOnClick = -1
        $slide.SlideShowTransition.AdvanceOnTime = 0
        foreach ($shape in $slide.Shapes) {
            if ($shape.Name.StartsWith('STATIC_')) { continue }
            if ($shape.Top -lt 100) { continue }
            $effect = $slide.TimeLine.MainSequence.AddEffect($shape,10,0,3)
            $effect.Timing.Duration = 0.4
            $animations++
        }
        $slide.Export((Join-Path $previewdir ('slide_{0:D2}.png' -f $slide.SlideIndex)),'PNG',1600,900)
    }
    $presentation.Save()
    $presentation.SaveAs((Join-Path $outdir 'Thuyet_trinh_Gamer_Clustering.pdf'),32)
    $count = $presentation.Slides.Count
    $presentation.Close()
    $status.Add("PowerPoint export OK: slides=$count, fade_animations=$animations")
} catch { $status.Add('PowerPoint export ERROR: ' + $_.Exception.Message) }
finally { if ($null -ne $ppt) { $ppt.Quit(); [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($ppt) } }
$status | Set-Content -LiteralPath (Join-Path $outdir 'office_export_log.txt') -Encoding UTF8
$status
