# 🖥 Mac Storage Analyzer

A fast, dependency-free Python CLI that tells you exactly where your macOS **System Data** storage is going — with orphaned app detection, 2-level category drilldowns, and actionable cleanup commands.

> No third-party packages. Pure Python 3 stdlib. Works on Apple Silicon and Intel.

---

## Install via Homebrew

```bash
brew tap mp9sit/mac_system_data_storage_analyzer
brew install mac-storage-analyzer
```

Then run:

```bash
sudo mac-storage-analyzer
```

> **Why sudo?** Many key paths — `~/Library/Application Support`, `/private/var`, `/Library/Caches` — are protected and return 0 bytes without root. The script will warn you with a red banner and ask before continuing if you forget.

---

## Or run directly with Python

```bash
git clone https://github.com/mp9sit/mac_system_data_storage_analyzer.git
cd mac_system_data_storage_analyzer
sudo python3 mac_storage_analyzer.py
```

---

## Usage

```bash
# Default — fast scan, no individual file search
sudo mac-storage-analyzer

# Include large-file hunt (slow on big disks — opt-in)
sudo mac-storage-analyzer --scan-files

# Custom file size threshold (default: 1 GB)
sudo mac-storage-analyzer --scan-files --min-gb 2
sudo mac-storage-analyzer --scan-files --min-gb 0.5
```

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--scan-files` | off | Scan for individual large files (slow, disabled by default) |
| `--min-gb N` | `1.0` | Minimum file size in GB for `--scan-files` |

---

## What It Reports

### 💾 Disk Overview
Total / used / free with a visual usage bar.

### 📂 Storage by Category
14 categories scanned and ranked by size:

| Category | Paths scanned |
|----------|--------------|
| Application Support | `~/Library/Application Support` |
| Xcode / Dev Tools | DerivedData, Archives, iOS Device Support, Simulators |
| System Caches | `/Library/Caches`, `~/Library/Caches` |
| Log Files | `/var/log`, `~/Library/Logs`, `/Library/Logs` |
| Time Machine Snapshots | `/.MobileBackups`, `/private/var/folders` |
| iOS / iPhone Backups | `~/Library/Application Support/MobileSync` |
| Mail & Attachments | `~/Library/Mail`, Mail container |
| Docker / VMs | Docker, Lima, VMware, Parallels |
| Homebrew | `/opt/homebrew`, `/usr/local` |
| npm / Node | `~/.npm`, `~/.nvm`, `~/.pnpm-store` |
| Python Packages | pyenv, miniconda, anaconda, virtualenvs |
| Trash | `~/.Trash` |
| Fonts | `~/Library/Fonts`, `/Library/Fonts` |
| Crash Reports | DiagnosticReports, CrashReporter |

**Top 5 categories auto-expand** with a 2-level directory drilldown showing full paths and sizes, so you can pinpoint the exact subfolder causing bloat without manual digging.

### 📸 Time Machine Local Snapshots
Lists all local snapshots with the command to delete them.

### 📱 Simulator Runtimes
Device count and total size, with cleanup command.

### 🍺 Homebrew Cache
Cache size and cleanup command.

### 🔍 Individual File Scan *(opt-in)*
Finds files above your size threshold. Disabled by default because it can take several minutes on large disks — enable with `--scan-files`.

### 🗑 Orphaned App Support Folders
The most actionable section. Compares every folder in `~/Library/Application Support` (≥ 100 MB) against your installed apps in `/Applications` using a 5-layer matching pipeline:

1. **System safelist** — macOS framework folders (`coreMLCache`, `CrashReporter`, etc.) are never flagged
2. **Exact bundle ID** — reads `CFBundleIdentifier` from each `.app`'s `Info.plist`
3. **Vendor map** — 60+ known mismatches (`BraveSoftware` → Brave Browser, `AgileBits` → 1Password, etc.)
4. **Token overlap** — fuzzy word-level matching handles compound names
5. **Bundle prefix** — `com.google.*` matches any Google app present

Only folders that pass through all 5 layers without a match are flagged as orphans.

### 💡 Cleanup Recommendations
Prioritised list of actionable tips based on what was actually found — only shown when thresholds are exceeded.

---

## Safe Removal Workflow

The script always reminds you to back up before deleting anything:

```bash
# Step 1: move to Desktop (safe — easy to restore if something breaks)
mv "~/Library/Application Support/<FolderName>" ~/Desktop/<FolderName>.bak

# Step 2: launch the relevant app and verify everything still works

# Step 3: only then permanently delete
rm -rf ~/Desktop/<FolderName>.bak
```

---

## Requirements

- macOS 13 Ventura or later (Apple Silicon + Intel)
- Python 3.9+ *(pre-installed on all modern Macs)*
- No pip installs, no virtual environments

---

## Contributing

Pull requests welcome. The easiest contribution is adding vendor mappings — **no Python knowledge required**, just edit `vendor_map.json`:

### Adding a vendor mapping

`vendor_map.json` has two sections:

**`vendor_map`** — for when a folder name doesn't match its `.app` name:
```json
{
  "vendor_map": {
    "bravesoftware": "brave",
    "yourappfolder": "your app name stem"
  }
}
```
Key = lowercase folder name in `~/Library/Application Support`
Value = substring of the `.app` name in `/Applications`

**`system_folders`** — for macOS/framework folders that should never be flagged:
```json
{
  "system_folders": [
    "coremlcache",
    "yoursystemfolder"
  ]
}
```

Other areas to improve:
- Support for additional package managers (Cargo, Go modules, rbenv, etc.)
- Additional category paths for niche tools

---

## Disclaimer

This tool only **reads** your filesystem — it never deletes anything automatically. All cleanup commands shown are suggestions you must run manually. Always verify a folder before removing it; some apps store data under a name that doesn't obviously match their `.app` bundle.

---

## License

MIT
