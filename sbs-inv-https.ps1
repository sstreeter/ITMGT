<#
.SYNOPSIS
    SBS Inventory Agent - HTTPS
.DESCRIPTION
    Collects hardware/OS info and posts it to the central inventory server.
    Requires:
    - Administrator Privileges (for CimInstance/Registry access)
    - Valid API Key for the server.
#>

# --- 1. Configuration ---
$AgentVersion = "2.0.0"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ConfigFile = Join-Path $ScriptDir "config.json"

if (-not (Test-Path $ConfigFile)) {
    Write-Error "CRITICAL: config.json not found in script directory."
    exit 1
}

try {
    $Config = Get-Content -Raw $ConfigFile | ConvertFrom-Json
} catch {
    Write-Error "CRITICAL: Failed to parse config.json. $_"
    exit 1
}

# Validate required keys
if ([string]::IsNullOrWhiteSpace($Config.ApiKey) -or $Config.ApiKey -eq "CHANGE_ME_TO_YOUR_SECRET_KEY") {
    Write-Error "CRITICAL: ApiKey is not configured in config.json."
    exit 1
}


# --- 2. Admin Check ---
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Error "CRITICAL: Must run as Admin."
    exit 1
}

# Ensure directory exists
if (-not (Test-Path $Config.LocalDir)) { 
    New-Item $Config.LocalDir -ItemType Directory -Force | Out-Null 
}

# --- 2.5 Cleanup Legacy Implementations ---
# The old "SMB" version stored the entire registry (Array) in SBS_PC_Master_Registry.json.
# We want to remove this to prevent confusion and save space.
$LegacyFile = Join-Path $Config.LocalDir "SBS_PC_Master_Registry.json"
if (Test-Path $LegacyFile) {
    try {
        Write-Host "Detected legacy registry file. Removing..." -ForegroundColor Yellow
        Remove-Item $LegacyFile -Force -ErrorAction Stop
        Write-Host "Legacy cleanup successful." -ForegroundColor Green
    } catch {
        Write-Warning "Could not remove legacy file: $_"
    }
}

# --- 1. Configuration ---
$AgentVersion = "2.0.0"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# ... (omitted config loading for brevity, assuming it's retained) ... 
# actually I need to be careful with replace_file_content to not wipe the config loading I just added.
# I will use a targeted replacement for the gathering section to inject the version.

# ... 

# --- 3. Gather Intelligence ---
try {
    # ... (other getters) ...
    $Tanium = Test-Path "C:\Program Files (x86)\Tanium\Tanium Client\TaniumClient.exe"

    $Record = [PSCustomObject]@{
        AssetID          = "SBS-PC-NEW" # Placeholder
        UUID             = $UUID
        SerialNumber     = $Bios.SerialNumber.Trim()
        Hostname         = $env:COMPUTERNAME
        Model            = $ComputerSystem.Model
        Processor        = $Processor.Name
        RAM_GB           = $RAM_GB
        Disk_GB          = $HDD_GB
        MfgYear          = $MfgYear
        OwnershipUnit    = "TBD"
        LocationBuilding = "TBD"
        LocationRoom     = "TBD"
        LocationVerified = $false
        InTanium         = $InTanium
        LastSeen         = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        Status           = "Active"
        AgentVersion     = $AgentVersion
    }
} catch {
# ...
    Write-Error "Failed to gather system information: $_"
    exit 1
}

# --- 4. Sync to Server ---
try {
    $JsonPayload = $Record | ConvertTo-Json -Depth 2
    
    $Headers = @{
        "X-API-Key"    = $Config.ApiKey
        "Content-Type" = "application/json"
    }

    # Note: If using self-signed certs, you must install the CA on the client.
    # We are NOT using the unsafe validation callback anymore.
    
    $Response = Invoke-RestMethod -Uri $Config.ServerUrl -Method Post -Body $JsonPayload -Headers $Headers -ErrorAction Stop
    
    if ($Response.status -eq "success") {
        Write-Host "Success: $($Response.message)" -ForegroundColor Green
    }
    
} catch {
    Write-Warning "Server unreachable or returned error: $($_.Exception.Message)"
    Write-Host "Saving to local cache only."
}

# --- 5. Save Cache & Stamp Registry ---
try {
    # File Cache
    $Record | ConvertTo-Json | Set-Content -Path $Config.CacheFile -Force

    # Registry Stamp
    if (-not (Test-Path $Config.LocalRegistry)) { New-Item $Config.LocalRegistry -Force | Out-Null }
    
    $Record.PSObject.Properties | ForEach-Object {
        $Val = if ($null -eq $_.Value) { "" } else { $_.Value.ToString() }
        New-ItemProperty -Path $Config.LocalRegistry -Name $_.Name -Value $Val -PropertyType String -Force | Out-Null
    }
} catch {
    Write-Error "Failed to save local cache/registry: $_"
}