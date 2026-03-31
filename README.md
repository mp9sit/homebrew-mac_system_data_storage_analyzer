# 🖥 Mac Storage Analyzer

A fast, dependency-free Python CLI that tells you exactly where your macOS **System Data** storage is going — with orphaned app detection, 2-level category drilldowns, and actionable cleanup commands.

> No third-party packages. No Homebrew required to run. Pure Python 3 stdlib.

---

## Why

macOS reports a large "System Data" bucket in Storage settings but gives you no breakdown. This tool scans the real directories behind that number, ranks them by size, drills into the top culprits, and identifies leftover folders from apps you've already uninstalled.

---

## Quick Start

```bash
# Clone
git clone https://github.com/YOUR_USERNAME/mac-storage-analyzer.git
cd mac-storage-analyzer

# Run (sudo recommended for full access)
sudo python3 mac_storage_analyzer.py
```

> **Why sudo?** Many key paths — `~/Library/Application Support`, `/private/var`, `/Library/Caches` — are protected and return 0 bytes without root. The script will warn you and ask before continuing if you forget.

---

## Usage

```bash
# Default — fast scan, no individual file search
sudo python3 mac_storage_analyzer.py

# Include large-file hunt (slow on big disks)
sudo python3 mac_storage_analyzer.py --scan-files

# Custom file size threshold (default: 1 GB)
sudo python3 mac_storage_analyzer.py --scan-files --min-gb 2
sudo python3 mac_storage_analyzer.py --scan-files --min-gb 0.5
```

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--scan-files` | off | Scan for individual large files (slow) |
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
Finds files above your size threshold across home directory, `/Library`, and `/private/var`. Disabled by default because it can take several minutes on large disks — enable with `--scan-files`.

### 🗑 Orphaned App Support Folders
The most actionable section. Compares every folder in `~/Library/Application Support` (≥ 100 MB) against your installed apps in `/Applications` using a 5-layer matching pipeline:

1. **System safelist** — macOS framework folders (`coreMLCache`, `CrashReporter`, etc.) are never flagged
2. **Exact bundle ID** — reads `CFBundleIdentifier` from each `.app`'s `Info.plist`
3. **Vendor map** — 60+ known mismatches (`BraveSoftware` → Brave Browser, `AgileBits` → 1Password, etc.)
4. **Token overlap** — fuzzy word-level matching handles compound names
5. **Bundle prefix** — `com.google.*` matches any Google app present

Flags folders where no installed app could be matched across all 5 checks.

### 💡 Cleanup Recommendations
Prioritised list of actionable tips based on what was actually found — only shown when thresholds are exceeded.

---

## Safe Removal Workflow

The script always reminds you to back up before deleting anything:

```bash
# Step 1: move to Desktop (easy to restore if something breaks)
mv "~/Library/Application Support/<FolderName>" ~/Desktop/<FolderName>.bak

# Step 2: launch the relevant app and verify everything still works

# Step 3: only then permanently delete
rm -rf ~/Desktop/<FolderName>.bak
```

---

## Requirements

- macOS (tested on macOS 13 Ventura and later, Apple Silicon + Intel)
- Python 3.9+  *(pre-installed on all modern Macs)*
- No pip installs, no virtual environments, no Homebrew

---

## Installing via Homebrew *(coming soon)*

```bash
brew tap YOUR_USERNAME/mac-storage-analyzer
brew install mac-storage-analyzer

# Then run:
sudo mac-storage-analyzer
```

---

## Contributing

Pull requests welcome. Common areas to improve:

- Additional vendor mappings in `vendor_map.json` for apps not yet covered
- Additional system-folder entries in `vendor_map.json`
- Support for additional package managers (Cargo, Go modules, etc.)

### Adding a vendor mapping

Edit `vendor_map.json` — no Python knowledge required:

```json
{
  "vendor_map": {
    "bravesoftware": "brave",
    "yourappfolder": "your app name"
  },
  "system_folders": [
    "coremlcache",
    "yoursystemfolder"
  ]
}
```

| Field | Key | Value |
|-------|-----|-------|
| `vendor_map` | Lowercase folder name in `~/Library/Application Support` | Substring of the `.app` name in `/Applications` |
| `system_folders` | Lowercase folder name | *(no value — presence means "always safe, never flag")* |

The script loads `vendor_map.json` from the same directory as `mac_storage_analyzer.py` at runtime. If the file is missing, a warning is shown and orphan detection falls back to bundle ID + token matching only.

---

## Disclaimer

This tool only **reads** your filesystem — it never deletes anything automatically. All cleanup commands shown are suggestions you must run manually. Always verify a folder before removing it; some apps store data under a name that doesn't obviously match their `.app` bundle.

---

## License

MIT
