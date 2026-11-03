$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
$projectFile = Join-Path $projectRoot 'MDK-ARM\42_lcd_hal.uvprojx'
$freertosFile = Join-Path $projectRoot 'Core\Src\freertos.c'
$portHeader = Join-Path $projectRoot 'Core\Inc\lv_port_disp.h'
$portSource = Join-Path $projectRoot 'Core\Src\lv_port_disp.c'
$dashboardSource = Join-Path $projectRoot 'Core\Src\dashboard.c'
$lvConf = Join-Path $projectRoot 'lvgl\lv_conf.h'
$freeRtosConfig = Join-Path $projectRoot 'Core\Inc\FreeRTOSConfig.h'
$failures = [System.Collections.Generic.List[string]]::new()

function Require-File([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        $failures.Add("Missing file: $Path")
    }
}

function Require-Pattern([string]$Path, [string]$Pattern, [string]$Description) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        $failures.Add("Cannot check $Description because file is missing: $Path")
        return
    }

    $content = Get-Content -LiteralPath $Path -Raw
    if ($content -notmatch $Pattern) {
        $failures.Add("Missing $Description in $Path")
    }
}

Require-File (Join-Path $projectRoot 'lvgl\lvgl.h')
Require-File (Join-Path $projectRoot 'lvgl\src\core\lv_obj.c')
Require-File $portHeader
Require-File $portSource
Require-File $dashboardSource
Require-File $freeRtosConfig

Require-Pattern $lvConf '#define\s+LV_COLOR_DEPTH\s+16' 'LV_COLOR_DEPTH 16'
Require-Pattern $lvConf '#if\s+1\s*/\* Enable this project configuration \*/' 'enabled lv_conf configuration'
Require-Pattern $lvConf '#define\s+LV_MEM_SIZE\s+\(24\s*\*\s*1024U\)' '24 KiB LVGL memory pool'
Require-Pattern $lvConf '#define\s+LV_FONT_MONTSERRAT_20\s+1' 'Montserrat 20 font'
Require-Pattern $lvConf '#define\s+LV_FONT_MONTSERRAT_40\s+1' 'Montserrat 40 font'
Require-Pattern $lvConf '#define\s+LV_BUILD_EXAMPLES\s+0' 'LV_BUILD_EXAMPLES 0'
Require-Pattern $lvConf '#define\s+LV_BUILD_DEMOS\s+0' 'LV_BUILD_DEMOS 0'
Require-Pattern $portSource 'lv_display_set_flush_cb\s*\(' 'LVGL display flush callback registration'
Require-Pattern $portSource 'lv_display_flush_ready\s*\(' 'LVGL flush completion notification'
Require-Pattern $dashboardSource 'lv_arc_set_value\s*\(' 'automotive RPM arc update'
Require-Pattern $dashboardSource 'lv_label_set_text_fmt\s*\([^;]*?"%u\.%u"' 'one-decimal RPM label update'
Require-Pattern $dashboardSource 'CAN OK' 'CAN online dashboard state'
Require-Pattern $dashboardSource 'CAN LOST' 'CAN timeout dashboard state'
Require-Pattern $dashboardSource 'void\s+Dashboard_Update\s*\(\s*uint16_t\s+rpm_x10\s*,\s*uint8_t\s+can_online\s*\)' 'CAN dashboard update API'
Require-Pattern $freertosFile 'lv_init\s*\(' 'lv_init call'
Require-Pattern $freertosFile 'lv_tick_set_cb\s*\(\s*HAL_GetTick\s*\)' 'HAL tick callback registration'
Require-Pattern $freertosFile 'LV_PortDisp_Init\s*\(' 'display port initialization'
Require-Pattern $freertosFile 'lv_timer_handler\s*\(' 'periodic LVGL timer handler'
Require-Pattern $freertosFile 'void\s+StartTask03\s*\(' 'retained myTask03 task entry'
Require-Pattern $freertosFile 'myTask03Handle\s*=\s*osThreadNew\s*\(\s*StartTask03' 'retained myTask03 task creation'
Require-Pattern $freertosFile '(?s)myTask03_attributes\s*=\s*\{.*?\.stack_size\s*=\s*256\s*\*\s*4.*?\.priority\s*=\s*\(osPriority_t\)\s*osPriorityNormal' 'myTask03 debug stack and Normal priority'
Require-Pattern $freertosFile '(?s)/\* USER CODE BEGIN StartTask03 \*/.*?CAN monitor task started.*?CAN RX SEQ:.*?CAN LOST VALID:.*?/\* USER CODE END StartTask03 \*/' 'CAN monitor code inside the Task03 user-code region'
Require-Pattern $freertosFile 'TASK CREATE default:%s lvgl:%s task3:%s HEAP:%lu' 'task creation diagnostics'
Require-Pattern $freertosFile '(?s)lvgl_attributes\s*=\s*\{.*?\.stack_size\s*=\s*1536\s*\*\s*4' '6 KiB LVGL task stack'
Require-Pattern $freeRtosConfig '#define\s+configTOTAL_HEAP_SIZE\s+\(\(size_t\)12288\)' '12 KiB FreeRTOS heap'
Require-Pattern $freertosFile '#define\s+DASHBOARD_CAN_TIMEOUT_MS\s+500U' '500 ms dashboard CAN timeout'
Require-Pattern $freertosFile 'Dashboard_Update\s*\(\s*rpm_x10\s*,\s*can_online\s*\)' 'LVGL task CAN dashboard update'

if(Test-Path -LiteralPath $freertosFile -PathType Leaf) {
    $freertosDashboardContent = Get-Content -LiteralPath $freertosFile -Raw
    if($freertosDashboardContent -match '\bdemo_rpm\b|\bdemo_step\b') {
        $failures.Add('LVGL task must not retain the simulated RPM generator')
    }
}

$freertosContent = Get-Content -LiteralPath $freertosFile -Raw
$lvglTaskMatch = [regex]::Match(
    $freertosContent,
    '(?s)void\s+StartLvglTask\s*\([^)]*\)\s*\{.*?/\* USER CODE END StartLvglTask \*/')
if((-not $lvglTaskMatch.Success) -or
   ($lvglTaskMatch.Value -match '\bprintf\s*\(')) {
    $failures.Add('StartLvglTask must not call non-thread-safe printf while Task03 owns runtime UART logging')
}

Require-Pattern $freertosFile '(?s)/\* USER CODE BEGIN StartTask03 \*/.*?osDelay\s*\(\s*1000U\s*\).*?CAN monitor task started' 'Task03 startup delay before runtime UART logging'
Require-Pattern $projectFile '\.\.\\lvgl(?:\\|;)' 'LVGL include path'
Require-Pattern $projectFile 'LV_CONF_INCLUDE_SIMPLE' 'LVGL simple configuration include define'
Require-Pattern $projectFile 'lv_port_disp\.c' 'display port source in Keil project'
Require-Pattern $projectFile '\.\.\\lvgl\\src\\core\\lv_obj\.c' 'LVGL source files in Keil project'

if ($failures.Count -gt 0) {
    Write-Host "LVGL bring-up validation failed ($($failures.Count) issue(s)):" -ForegroundColor Red
    foreach ($failure in $failures) {
        Write-Host " - $failure" -ForegroundColor Red
    }
    exit 1
}

Write-Host 'LVGL bring-up validation passed.' -ForegroundColor Green
exit 0
