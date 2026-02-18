# --- 0. Permissions Check ---
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Error "Must run as Admin."; return
}

# --- 1. Configuration ---
$LocalDir        = "C:\IT_Management"
$NetworkDir      = "\\YourServer\SBS_Inventory$" # <--- Set your share path here
$RegistryFile    = "SBS_PC_Master_Registry.json"
$LocalRegistry   = "$LocalDir\$RegistryFile"
$NetworkRegistry = "$NetworkDir\$RegistryFile"
$LocalRegPath    = "HKLM:\SOFTWARE\SBS\Management"

if (-not (Test-Path $LocalDir)) { New-Item $LocalDir -ItemType Directory -Force | Out-Null }

# --- 2. Identity & Essential Specs ---
$UUID   = (Get-CimInstance Win32_ComputerSystemProduct).UUID
$Serial = (Get-CimInstance Win32_Bios).SerialNumber.Trim()
$Host   = $env:COMPUTERNAME
$Model  = (Get-CimInstance Win32_ComputerSystem).Model
$CPU    = (Get-CimInstance Win32_Processor).Name
$RAM    = [Math]::Round((Get-CimInstance Win32_PhysicalMemory | Measure-Object Capacity -Sum).Sum / 1GB)
$Drive  = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='C:'"
$HDD    = [Math]::Round($Drive.Size / 1GB)
$BIOS   = (Get-CimInstance Win32_Bios).ReleaseDate
$Age    = if ($BIOS) { $BIOS.ToString().Substring(0,4) } else { "Unknown" }
$Date   = Get-Date -Format "yyyy-MM-dd"
$TaniumInstalled = Test-Path "C:\Program Files (x86)\Tanium\Tanium Client\TaniumClient.exe"

# --- 3. Load Master File ---
$NetOk = Test-Path $NetworkDir
if ($NetOk -and (Test-Path $NetworkRegistry)) {
    $Registry = Get-Content $NetworkRegistry | ConvertFrom-Json | ForEach-Object { [PSCustomObject]$_ }
    Copy-Item $NetworkRegistry $LocalRegistry -Force
} elseif (Test-Path $LocalRegistry) {
    $Registry = Get-Content $LocalRegistry | ConvertFrom-Json | ForEach-Object { [PSCustomObject]$_ }
} else { $Registry = @() }

# --- 4. Find or Create Record ---
$Record = $Registry | Where-Object { $_.UUID -eq $UUID }

if ($null -eq $Record) {
    # Define codes (Keep this updated)
    $CodeMap = @{ "acc"="Accounting"; "adm"="Administration"; "ana"="Anatomy Lab"; "com"="Computing"; "gld"="Goldenberg Lab"; "fcl"="Facilities"; "tea"="Teaching Labs" }
    $FoundUnit = "Unassigned"
    foreach ($code in $CodeMap.Keys) { if ($Host -like "*-$code-*") { $FoundUnit = $CodeMap[$code]; break } }

    $Record = [PSCustomObject]@{
        AssetID          = "SBS-PC-$($Registry.Count + 1001)"
        UUID             = $UUID
        SerialNumber     = $Serial
        Hostname         = $Host
        Model            = $Model
        Processor        = $CPU
        RAM_GB           = $RAM
        Disk_GB          = $HDD
        MfgYear          = $Age
        OwnershipUnit    = $FoundUnit
        LocationBuilding = "TBD"
        LocationRoom     = "TBD"
        LocationVerified = $false
        InTanium         = $TaniumInstalled
        LastSeen         = $Date
        Status           = "Active"
    }
    $Registry += $Record
} else {
    # Update dynamic specs
    $Record.Hostname  = $Host
    $Record.Processor = $CPU
    $Record.RAM_GB    = $RAM
    $Record.Disk_GB   = $HDD
    $Record.InTanium  = $TaniumInstalled
    $Record.LastSeen  = $Date
}

# --- 5. Save & Stamp ---
$Json = $Registry | ConvertTo-Json -Depth 10
if ($NetOk) { 
    if (-not (Test-Path "$NetworkDir\Backups")) { New-Item "$NetworkDir\Backups" -ItemType Directory | Out-Null }
    Set-Content $NetworkRegistry -Value $Json -Force 
    $Json | Set-Content "$NetworkDir\Backups\Registry_$($Date).json" -Force
}
Set-Content $LocalRegistry -Value $Json -Force

# Stamp Local Registry (Tanium reads these)
if (-not (Test-Path $LocalRegPath)) { New-Item $LocalRegPath -Force | Out-Null }
$Record.PSObject.Properties | ForEach-Object {
    $v = if ($null -eq $_.Value) { "" } else { $_.Value.ToString() }
    New-ItemProperty -Path $LocalRegPath -Name $_.Name -Value $v -PropertyType String -Force | Out-Null
}

Write-Host "Inventory Sync Complete for SBS Asset: $($Record.AssetID)" -ForegroundColor Green