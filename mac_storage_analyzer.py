#!/usr/bin/env python3
"""
Mac System Data Storage Analyzer
Usage:
  python3 mac_storage_analyzer.py                 # default 1 GB threshold
  python3 mac_storage_analyzer.py --min-gb 2      # custom threshold
  sudo python3 mac_storage_analyzer.py            # full access (recommended)
"""

import os
import sys
import glob
import shutil
import argparse
import subprocess
from pathlib import Path

# ── ANSI colours ──────────────────────────────────────────────────────────────
R       = "\033[0m"
BOLD    = "\033[1m"
CYAN    = "\033[96m"
YELLOW  = "\033[93m"
GREEN   = "\033[92m"
RED     = "\033[91m"
RED_BG  = "\033[41m"
DIM     = "\033[2m"
MAGENTA = "\033[95m"
BLINK   = "\033[5m"


# ── Helpers ───────────────────────────────────────────────────────────────────

def fmt_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(n) < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


def dir_size(path: str) -> int:
    total = 0
    try:
        for entry in os.scandir(path):
            try:
                if entry.is_symlink():
                    continue
                if entry.is_file(follow_symlinks=False):
                    total += entry.stat(follow_symlinks=False).st_size
                elif entry.is_dir(follow_symlinks=False):
                    total += dir_size(entry.path)
            except (PermissionError, OSError):
                pass
    except (PermissionError, OSError):
        pass
    return total


def bar(used: int, total: int, width: int = 30) -> str:
    if total == 0:
        return "[" + " " * width + "]"
    filled = int(width * used / total)
    return "[" + "█" * filled + "░" * (width - filled) + "]"


def run(cmd: list) -> str:
    try:
        return subprocess.check_output(cmd, stderr=subprocess.DEVNULL, text=True).strip()
    except Exception:
        return ""


def section(title: str) -> None:
    print(f"\n{BOLD}{CYAN}{'─'*60}{R}")
    print(f"{BOLD}{CYAN}  {title}{R}")
    print(f"{BOLD}{CYAN}{'─'*60}{R}")


def row(label: str, size: int, total: int, color: str = "", indent: str = "  ") -> None:
    pct = (size / total * 100) if total else 0
    print(f"{indent}{color}{label:<46}{R}  {fmt_size(size):>10}  {DIM}{pct:5.1f}%{R}")


# ── Sudo check with red flash ─────────────────────────────────────────────────

def sudo_check() -> bool:
    """Returns True if we should continue. Prompts user if not root."""
    if os.geteuid() == 0:
        return True

    # Flash red warning
    print(f"\n{RED_BG}{BOLD}{'─'*60}{R}")
    print(f"{RED_BG}{BOLD}  ⚠  NOT RUNNING AS ROOT                                    {R}")
    print(f"{RED_BG}{BOLD}{'─'*60}{R}")
    print(f"\n{YELLOW}  Many key paths require sudo to read:")
    print(f"  ~/Library/Application Support, /private/var, /Library/Caches ...")
    print(f"\n  Results will be significantly incomplete without sudo.")
    print(f"  Recommended: {BOLD}sudo python3 {sys.argv[0]}{R}{YELLOW}")

    # Append any original args
    extra = " ".join(sys.argv[1:])
    if extra:
        print(f"               with your flags: {extra}")

    print(f"{R}")

    try:
        answer = input(f"  {BOLD}Continue anyway? [y/N]:{R} ").strip().lower()
    except (KeyboardInterrupt, EOFError):
        print()
        return False

    if answer not in ("y", "yes"):
        print(f"\n  {DIM}Aborted. Re-run with sudo for full results.{R}\n")
        return False

    print(f"\n{YELLOW}  ⚠  Continuing without sudo — results may be incomplete.{R}")
    return True


# ── Disk overview ─────────────────────────────────────────────────────────────

def disk_overview() -> int:
    section("💾  Disk Overview")
    total, used, free = shutil.disk_usage("/")
    print(f"  {'Total':<20} {fmt_size(total):>10}")
    print(f"  {GREEN}{'Free':<20}{R} {fmt_size(free):>10}")
    print(f"  {RED}{'Used':<20}{R} {fmt_size(used):>10}")
    print(f"\n  {bar(used, total)}  {used/total*100:.1f}% used")
    return total


# ── Category scan + 2-level drilldown ────────────────────────────────────────

CATEGORIES = {
    "Application Support": [
        "~/Library/Application Support",
    ],
    "Xcode / Dev Tools": [
        "~/Library/Developer/Xcode/DerivedData",
        "~/Library/Developer/Xcode/Archives",
        "~/Library/Developer/Xcode/iOS DeviceSupport",
        "~/Library/Developer/Xcode/watchOS DeviceSupport",
        "~/Library/Developer/CoreSimulator/Devices",
        "/Applications/Xcode.app",
    ],
    "System Caches": [
        "/Library/Caches",
        "~/Library/Caches",
        "/System/Library/Caches",
    ],
    "Log Files": [
        "/var/log",
        "~/Library/Logs",
        "/Library/Logs",
    ],
    "Time Machine Local Snapshots": [
        "/.MobileBackups",
        "/private/var/folders",
    ],
    "iOS / iPhone Backups": [
        "~/Library/Application Support/MobileSync/Backup",
    ],
    "Mail Downloads & Attachments": [
        "~/Library/Mail",
        "~/Library/Containers/com.apple.mail",
    ],
    "Docker / VMs": [
        "~/Library/Containers/com.docker.docker",
        "~/.docker",
        "~/Library/Application Support/VMware Fusion",
        "~/Library/Application Support/Parallels",
        "~/Library/Application Support/com.docker.docker",
        "~/.lima",
    ],
    "Homebrew": [
        "/opt/homebrew",
        "/usr/local/Homebrew",
        "/usr/local/Cellar",
    ],
    "npm / Node": [
        "~/.npm",
        "~/.nvm",
        "~/.pnpm-store",
        "~/node_modules",
    ],
    "Python Packages": [
        "~/.pyenv",
        "~/Library/Python",
        "/Library/Python",
        "~/.virtualenvs",
        "~/miniconda3",
        "~/anaconda3",
    ],
    "Trash": [
        "~/.Trash",
        "/Volumes/*/.Trashes",
    ],
    "Fonts": [
        "~/Library/Fonts",
        "/Library/Fonts",
    ],
    "Crash Reports / Diagnostics": [
        "~/Library/Logs/DiagnosticReports",
        "/Library/Logs/DiagnosticReports",
        "~/Library/Application Support/CrashReporter",
    ],
}


def get_subdir_sizes(path: str, depth: int = 1) -> list:
    """Return (size, full_path) for immediate children of path, sorted desc."""
    results = []
    try:
        for entry in os.scandir(path):
            try:
                if entry.is_symlink():
                    continue
                if entry.is_dir(follow_symlinks=False):
                    sz = dir_size(entry.path)
                    results.append((sz, entry.path))
            except (PermissionError, OSError):
                pass
    except (PermissionError, OSError):
        pass
    results.sort(reverse=True)
    return results


def drilldown(cat_paths: list, disk_total: int, top_n: int = 5) -> None:
    """Print top_n subdirs (2 levels deep) across all paths for a category."""
    # Level 1: immediate children across all category paths
    level1 = []
    for p in cat_paths:
        ep = os.path.expanduser(p)
        if "*" in ep:
            for gp in glob.glob(ep):
                level1 += get_subdir_sizes(gp)
        elif os.path.exists(ep):
            level1 += get_subdir_sizes(ep)

    level1.sort(reverse=True)
    shown_l1 = level1[:top_n]

    for sz1, path1 in shown_l1:
        row(path1, sz1, disk_total, color=DIM + CYAN, indent="      ├─ ")

        # Level 2: top 5 children of this level-1 dir
        level2 = get_subdir_sizes(path1)[:top_n]
        for i, (sz2, path2) in enumerate(level2):
            connector = "└─" if i == len(level2) - 1 else "├─"
            row(path2, sz2, disk_total, color=DIM, indent=f"      │   {connector} ")


def scan_categories(disk_total: int) -> dict:
    section("📂  Storage by Category")
    results = {}
    for cat, paths in CATEGORIES.items():
        total_cat = 0
        for p in paths:
            expanded = os.path.expanduser(p)
            if "*" in expanded:
                for gp in glob.glob(expanded):
                    total_cat += dir_size(gp)
            elif os.path.exists(expanded):
                total_cat += dir_size(expanded)
        results[cat] = total_cat

    sorted_cats = sorted(results.items(), key=lambda x: x[1], reverse=True)

    for cat, size in sorted_cats:
        color = RED if size > 5 * 1024**3 else (YELLOW if size > 1 * 1024**3 else "")
        row(cat, size, disk_total, color)

        # Drilldown for top 5 categories only (non-zero)
        top5 = [c for c, s in sorted_cats if s > 0][:5]
        if cat in top5 and size > 0:
            drilldown(CATEGORIES[cat], disk_total, top_n=5)

    return results


# ── Large files ───────────────────────────────────────────────────────────────

def find_large_files(min_gb: float = 1.0) -> None:
    min_bytes = int(min_gb * 1024**3)
    section(f"🔍  Individual Files ≥ {min_gb:g} GB")
    home = Path.home()
    search_roots = [home, Path("/Library"), Path("/private/var")]
    found = []

    for root in search_roots:
        if not root.exists():
            continue
        try:
            for p in root.rglob("*"):
                try:
                    if p.is_file(follow_symlinks=False):
                        sz = p.stat(follow_symlinks=False).st_size
                        if sz >= min_bytes:
                            found.append((sz, str(p)))
                except (PermissionError, OSError):
                    pass
        except (PermissionError, OSError):
            pass

    found.sort(reverse=True)
    if not found:
        print(f"  {DIM}No files ≥ {min_gb:g} GB found in scanned paths.{R}")
        return
    for sz, path in found[:25]:
        print(f"  {fmt_size(sz):>12}  {DIM}{path}{R}")
    if len(found) > 25:
        print(f"  {DIM}… and {len(found)-25} more{R}")


# ── Time Machine snapshots ────────────────────────────────────────────────────

def time_machine_snapshots() -> None:
    section("📸  Time Machine Local Snapshots")
    out = run(["tmutil", "listlocalsnapshots", "/"])
    if not out:
        print(f"  {DIM}None found (or tmutil not available){R}")
        return
    lines = [l for l in out.splitlines() if l.strip()]
    print(f"  Found {YELLOW}{len(lines)}{R} local snapshot(s):\n")
    for l in lines:
        print(f"  • {l}")
    print(f"\n  {DIM}To delete all: sudo tmutil deletelocalsnapshots /{R}")


# ── Simulator runtimes ────────────────────────────────────────────────────────

def simulator_runtimes() -> None:
    section("📱  iOS/watchOS Simulator Runtimes")
    sim_root = os.path.expanduser("~/Library/Developer/CoreSimulator/Devices")
    if not os.path.exists(sim_root):
        print(f"  {DIM}No simulators found{R}")
        return
    try:
        devices = [d for d in os.listdir(sim_root)
                   if os.path.isdir(os.path.join(sim_root, d))]
    except PermissionError:
        print(f"  {DIM}Permission denied{R}")
        return
    total = dir_size(sim_root)
    print(f"  Simulator devices : {YELLOW}{len(devices)}{R}")
    print(f"  Total size        : {RED}{fmt_size(total)}{R}")
    print(f"\n  {DIM}To clean up: xcrun simctl delete unavailable{R}")


# ── Homebrew cache ────────────────────────────────────────────────────────────

def homebrew_cache() -> None:
    section("🍺  Homebrew Cache")
    cache = os.path.expanduser("~/Library/Caches/Homebrew")
    if not os.path.exists(cache):
        print(f"  {DIM}Homebrew cache not found{R}")
        return
    sz = dir_size(cache)
    print(f"  Cache size: {YELLOW}{fmt_size(sz)}{R}")
    print(f"  {DIM}To clean: brew cleanup --prune=all{R}")


# ── Orphan app support detector ───────────────────────────────────────────────

def _load_vendor_data() -> tuple[dict, set]:
    """
    Load VENDOR_MAP and SYSTEM_APP_SUPPORT_FOLDERS from vendor_map.json
    located next to this script. Falls back to empty dicts/sets if missing.
    """
    import json
    json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor_map.json")
    if not os.path.exists(json_path):
        print(f"{YELLOW}  ⚠  vendor_map.json not found next to script — orphan detection will be less accurate.{R}")
        return {}, set()
    try:
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)
        vendor_map     = {k.lower(): v.lower() for k, v in data.get("vendor_map", {}).items()}
        system_folders = set(s.lower() for s in data.get("system_folders", []))
        return vendor_map, system_folders
    except Exception as e:
        print(f"{YELLOW}  ⚠  Could not parse vendor_map.json: {e}{R}")
        return {}, set()

VENDOR_MAP, SYSTEM_APP_SUPPORT_FOLDERS = _load_vendor_data()


def tokenise(name: str) -> set:
    """Split a folder/app name into lowercase word tokens, strip common suffixes."""
    import re
    name = name.lower()
    # Remove common noise: "software", "inc", "ltd", "mac", "app", "helper"
    name = re.sub(r"(software|inc|ltd|llc|corp|mac|app|helper|agent|daemon|launcher)", "", name)
    tokens = set(re.split(r"[\s\-_.,]", name))
    tokens.discard("")
    return tokens


def find_orphan_app_support(min_mb: int = 100) -> list:
    """
    Compare ~/Library/Application Support subdirs against installed apps.
    Returns (size, folder_name, full_path, status) where status is:
      "orphan"   — no matching app found
      "system"   — macOS/framework folder, always safe to keep
    Only orphans are returned; system folders are silently skipped.

    Match strategy (layered):
      1. System/framework safelist         — never flag
      2. Exact CFBundleIdentifier match    — installed
      3. Vendor map lookup                 — known vendor alias
      4. Token overlap between folder and app name — fuzzy match
      5. Reverse-DNS bundle prefix match   — com.apple.*, com.google.* etc.
    """
    app_support = os.path.expanduser("~/Library/Application Support")
    applications_dirs = ["/Applications", os.path.expanduser("~/Applications")]

    # Gather installed apps: stems, bundle ids, token sets
    installed_names   = set()   # lowercase stems
    installed_bundles = set()   # bundle ids
    installed_tokens  = set()   # all tokens across all app names

    for apps_dir in applications_dirs:
        if not os.path.isdir(apps_dir):
            continue
        try:
            for entry in os.scandir(apps_dir):
                if not entry.name.endswith(".app"):
                    continue
                stem = entry.name[:-4].lower()
                installed_names.add(stem)
                installed_tokens |= tokenise(stem)
                plist = os.path.join(entry.path, "Contents", "Info.plist")
                if os.path.exists(plist):
                    bid = run(["defaults", "read", plist, "CFBundleIdentifier"])
                    if bid:
                        installed_bundles.add(bid.lower())
                        # also add each component of the bundle id as tokens
                        installed_tokens |= set(bid.lower().split("."))
        except (PermissionError, OSError):
            pass

    orphans = []
    try:
        entries = list(os.scandir(app_support))
    except (PermissionError, OSError):
        return []

    for entry in entries:
        if not entry.is_dir(follow_symlinks=False):
            continue
        sz = dir_size(entry.path)
        if sz < min_mb * 1024 * 1024:
            continue

        name       = entry.name
        name_lower = name.lower()

        # ── Check 1: system/framework safelist ───────────────────────────────
        if name_lower in SYSTEM_APP_SUPPORT_FOLDERS:
            continue
        if any(name_lower.startswith(pfx) for pfx in (
            "com.apple.", "sync.", "network", "mobile", "cloud",
        )):
            continue

        # ── Check 2: exact bundle id ──────────────────────────────────────────
        if name_lower in installed_bundles:
            continue

        # ── Check 3: vendor map ───────────────────────────────────────────────
        matched_via_vendor = False
        for vendor_key, app_hint in VENDOR_MAP.items():
            if name_lower.startswith(vendor_key) or vendor_key in name_lower:
                # Check hint exists in installed names
                if any(app_hint in n for n in installed_names):
                    matched_via_vendor = True
                    break
                # Even if not installed, the vendor map tells us it's a known app
                # folder — mark as known (not a mystery orphan), skip silently
                matched_via_vendor = True
                break
        if matched_via_vendor:
            continue

        # ── Check 4: token overlap ────────────────────────────────────────────
        folder_tokens = tokenise(name_lower)
        # Remove very short tokens that cause false matches ("a", "x", "go" etc.)
        folder_tokens = {t for t in folder_tokens if len(t) >= 3}
        if folder_tokens & installed_tokens:
            continue

        # ── Check 5: bundle id prefix in folder name ──────────────────────────
        # e.g. folder "com.google.chrome" → google chrome installed
        parts = name_lower.split(".")
        if len(parts) >= 2:
            vendor = parts[1] if parts[0] in ("com", "org", "io", "net", "app") else parts[0]
            if any(vendor in n for n in installed_names) or vendor in installed_tokens:
                continue

        orphans.append((sz, name, entry.path))

    orphans.sort(reverse=True)
    return orphans


# ── Quick-win recommendations ─────────────────────────────────────────────────

def recommendations(cats: dict) -> None:
    section("💡  Quick-Win Cleanup Recommendations")
    tips = []

    if cats.get("Xcode / Dev Tools", 0) > 2 * 1024**3:
        tips.append((cats["Xcode / Dev Tools"],
                     "Xcode DerivedData / archives",
                     "rm -rf ~/Library/Developer/Xcode/DerivedData\n"
                     "    xcrun simctl delete unavailable"))
    if cats.get("iOS / iPhone Backups", 0) > 1 * 1024**3:
        tips.append((cats["iOS / iPhone Backups"],
                     "iPhone backups",
                     "Finder → [your iPhone] → Manage Backups → delete old ones"))
    if cats.get("System Caches", 0) > 2 * 1024**3:
        tips.append((cats["System Caches"],
                     "System & app caches",
                     "rm -rf ~/Library/Caches/*  (safe; rebuilt automatically)"))
    if cats.get("Log Files", 0) > 500 * 1024**2:
        tips.append((cats["Log Files"],
                     "Log files",
                     "sudo rm -rf /var/log/* ~/Library/Logs/*"))
    if cats.get("Docker / VMs", 0) > 5 * 1024**3:
        tips.append((cats["Docker / VMs"],
                     "Docker / VM images",
                     "docker system prune -a  or remove unused VM snapshots"))
    if cats.get("Homebrew", 0) > 1 * 1024**3:
        tips.append((cats["Homebrew"],
                     "Homebrew",
                     "brew cleanup --prune=all"))
    if cats.get("Trash", 0) > 200 * 1024**2:
        tips.append((cats["Trash"],
                     "Trash",
                     "Empty Trash in Finder"))

    if not tips:
        print(f"  {GREEN}No obvious hotspots detected — you're looking good!{R}")
    else:
        tips.sort(reverse=True)
        for sz, label, cmd in tips:
            print(f"\n  {BOLD}{YELLOW}▶ {label}  ({fmt_size(sz)}){R}")
            for line in cmd.splitlines():
                print(f"    {DIM}{line}{R}")

    # ── Orphan app support analysis ───────────────────────────────────────────
    if cats.get("Application Support", 0) > 0:
        section("🗑   Orphaned App Support Folders")
        print(f"  {DIM}Folders in ~/Library/Application Support with no matching app in /Applications{R}\n")
        orphans = find_orphan_app_support(min_mb=100)
        if not orphans:
            print(f"  {GREEN}No orphans found — every folder matches an installed app.{R}")
        else:
            total_orphan = sum(s for s, _, _ in orphans)
            print(f"  Found {YELLOW}{len(orphans)}{R} likely orphan(s) "
                  f"totalling {RED}{BOLD}{fmt_size(total_orphan)}{R}\n")
            for sz, name, full_path in orphans:
                color = RED if sz > 1 * 1024**3 else (YELLOW if sz > 200 * 1024**2 else DIM)
                print(f"  {color}{fmt_size(sz):>10}{R}  {name}")
                print(f"            {DIM}{full_path}{R}")
            print(f"\n  {YELLOW}⚠  Verify each folder before deleting — some apps store data")
            print(f"     under a different name than the .app bundle.{R}")
            print(f"\n  {BOLD}Always back up before removing:{R}")
            print(f"  {DIM}  # Step 1: move to Desktop as a backup (safe — easy to restore)")
            print(f"     mv \"~/Library/Application Support/<FolderName>\" ~/Desktop/<FolderName>.bak{R}")
            print(f"  {DIM}  # Step 2: test that the relevant app still works correctly")
            print(f"  {DIM}  # Step 3: only then permanently delete the backup")
            print(f"     rm -rf ~/Desktop/<FolderName>.bak{R}")
            print(f"\n  {DIM}  Or use Finder: hold Option and drag the folder to Desktop to copy,")
            print(f"     then delete the original from Application Support.{R}")


# ── Argument parsing ──────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(
        description="Mac System Data Storage Analyzer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  sudo python3 mac_storage_analyzer.py                        # fast scan, no file search
  sudo python3 mac_storage_analyzer.py --scan-files           # include large-file search (slow)
  sudo python3 mac_storage_analyzer.py --scan-files --min-gb 2    # files ≥ 2 GB only
  sudo python3 mac_storage_analyzer.py --scan-files --min-gb 0.5  # files ≥ 500 MB
        """
    )
    p.add_argument(
        "--scan-files",
        action="store_true",
        default=False,
        help="Enable individual large-file scan (slow — disabled by default)"
    )
    p.add_argument(
        "--min-gb",
        type=float,
        default=1.0,
        metavar="N",
        help="Minimum file size in GB for the large-files scan (default: 1.0, requires --scan-files)"
    )
    return p.parse_args()


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    args = parse_args()

    print(f"\n{BOLD}{MAGENTA}{'═'*60}")
    print("    🖥  Mac System Data Storage Analyzer")
    print(f"{'═'*60}{R}")

    if not sudo_check():
        sys.exit(0)

    disk_total = disk_overview()
    cats = scan_categories(disk_total)
    time_machine_snapshots()
    simulator_runtimes()
    homebrew_cache()

    if args.scan_files:
        find_large_files(min_gb=args.min_gb)
    else:
        section("🔍  Individual File Scan")
        print(f"  {DIM}Skipped by default (can take several minutes on large disks).{R}")
        print(f"\n  To enable, re-run with:")
        print(f"  {BOLD}{GREEN}  sudo python3 {sys.argv[0]} --scan-files{R}")
        print(f"  {DIM}  sudo python3 {sys.argv[0]} --scan-files --min-gb 2   {R}{DIM}# only files ≥ 2 GB{R}")
        print(f"  {DIM}  sudo python3 {sys.argv[0]} --scan-files --min-gb 0.5 {R}{DIM}# files ≥ 500 MB{R}")

    recommendations(cats)

    print(f"\n{BOLD}{MAGENTA}{'═'*60}{R}")
    print(f"{DIM}  Scan complete.  Review paths above before deleting anything.{R}")
    if not args.scan_files:
        print(f"\n  {YELLOW}💡 Tip: add {BOLD}--scan-files{R}{YELLOW} to also hunt individual large files.{R}")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n  {YELLOW}⚠  Scan interrupted.{R}")
        print(f"  {DIM}Partial results above may still be useful.{R}\n")
        sys.exit(130)  # standard exit code for Ctrl+C
