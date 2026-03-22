# automation/os_automator.py  ──  Nandhi AI OS Automation Module
# Safe, cross-platform OS task automation.
# All destructive operations require explicit confirmation.

import os
import sys
import shutil
import logging
import platform
import subprocess
import threading
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Tuple, Optional, List, Dict

log = logging.getLogger("nandhi.automation")
OS = platform.system()  # "Windows" | "Darwin" | "Linux"

# ── Optional deps ──────────────────────────────────────
try:
    import psutil; HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

try:
    import pyautogui; HAS_PYAUTO = True
except ImportError:
    HAS_PYAUTO = False


class OsAutomator:
    """
    Executes OS-level automation tasks.
    All actions return (success: bool, message: str).
    Destructive actions are marked needs_confirm=True and must be
    confirmed by the caller before execute() is called.
    """

    # ── Action registry ─────────────────────────────────
    ACTIONS: Dict[str, dict] = {
        # Info / read-only
        "system_info":        {"needs_confirm": False, "label": "System Info"},
        "list_processes":     {"needs_confirm": False, "label": "List Processes"},
        "disk_usage":         {"needs_confirm": False, "label": "Disk Usage"},
        "wifi_status":        {"needs_confirm": False, "label": "WiFi Status"},
        "screenshot":         {"needs_confirm": False, "label": "Take Screenshot"},
        "list_downloads":     {"needs_confirm": False, "label": "List Downloads"},

        # Launchers
        "open_browser":       {"needs_confirm": False, "label": "Open Browser"},
        "open_vscode":        {"needs_confirm": False, "label": "Open VS Code"},
        "open_terminal":      {"needs_confirm": False, "label": "Open Terminal"},
        "open_explorer":      {"needs_confirm": False, "label": "Open File Explorer"},

        # Moderately destructive — confirm
        "organize_downloads": {"needs_confirm": True,  "label": "Organize Downloads",
                               "desc": "Sort ~/Downloads into subfolders by file type (Images, Documents, Video…)"},
        "empty_trash":        {"needs_confirm": True,  "label": "Empty Trash",
                               "desc": "Permanently delete all files in the system Trash / Recycle Bin"},
        "kill_process":       {"needs_confirm": True,  "label": "Kill Process",
                               "desc": "Force-terminate a running process by name or PID"},
        "delete_file":        {"needs_confirm": True,  "label": "Delete File",
                               "desc": "Permanently delete a specific file"},

        # System commands
        "run_shell":          {"needs_confirm": True,  "label": "Run Shell Command",
                               "desc": "Execute an arbitrary shell/terminal command"},
    }

    def needs_confirm(self, action: str) -> Tuple[bool, str]:
        """Return (needs_confirm, description) for an action."""
        cfg = self.ACTIONS.get(action, {})
        return cfg.get("needs_confirm", True), cfg.get("desc", "")

    def execute(self, action: str, **kwargs) -> Tuple[bool, str]:
        """Run an automation action. Returns (success, message)."""
        fn = getattr(self, f"_act_{action}", None)
        if fn is None:
            return False, f"Unknown action: {action}"
        try:
            result = fn(**kwargs)
            log.info(f"[Automation] {action}: {result}")
            return True, result
        except Exception as e:
            log.error(f"[Automation] {action} failed: {e}")
            return False, f"Error: {e}"

    # ══════════════════════════════════════════════════════
    #  READ-ONLY ACTIONS
    # ══════════════════════════════════════════════════════

    def _act_system_info(self) -> str:
        if HAS_PSUTIL:
            cpu  = psutil.cpu_percent(interval=0.5)
            mem  = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            boot = datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M")
            return (f"OS: {OS} | CPU: {cpu}% | "
                    f"RAM: {mem.percent}% ({mem.used//1_073_741_824}GB / {mem.total//1_073_741_824}GB) | "
                    f"Disk: {disk.percent}% used | Boot: {boot}")
        return f"OS: {OS} | Python: {sys.version.split()[0]} | psutil not installed for detailed stats"

    def _act_list_processes(self, top: int = 10) -> str:
        if HAS_PSUTIL:
            procs = []
            for p in psutil.process_iter(["pid","name","cpu_percent","memory_percent"]):
                try:
                    procs.append(p.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            procs.sort(key=lambda x: x.get("cpu_percent") or 0, reverse=True)
            lines = [f"PID:{p['pid']:6} CPU:{p['cpu_percent']:5.1f}%  {p['name']}" for p in procs[:top]]
            return "\n".join(lines)
        out = subprocess.check_output(
            ["ps","aux","--sort=-pcpu"] if OS != "Windows" else ["tasklist"],
            timeout=5, text=True, errors="replace"
        )
        return "\n".join(out.splitlines()[:top+2])

    def _act_disk_usage(self) -> str:
        parts = []
        if HAS_PSUTIL:
            for part in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    parts.append(f"{part.device}: {usage.percent}% ({usage.used//1_073_741_824}GB/{usage.total//1_073_741_824}GB)")
                except Exception:
                    pass
            return "\n".join(parts) or "No partitions found"
        return shutil.disk_usage("/").__str__()

    def _act_wifi_status(self) -> str:
        try:
            if OS == "Windows":
                out = subprocess.check_output(["netsh","wlan","show","interfaces"], timeout=5, text=True, errors="replace")
                lines = [l.strip() for l in out.splitlines() if any(k in l for k in ("SSID","State","Signal","Speed"))]
            elif OS == "Darwin":
                out = subprocess.check_output(
                    ["/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport","-I"],
                    timeout=5, text=True, errors="replace"
                )
                lines = [l.strip() for l in out.splitlines() if l.strip()][:8]
            else:
                out = subprocess.check_output(["nmcli","-t","-f","DEVICE,TYPE,STATE,CONNECTION","dev"], timeout=5, text=True, errors="replace")
                lines = [l.strip() for l in out.splitlines() if l.strip()]
            return "\n".join(lines[:8])
        except FileNotFoundError:
            return "WiFi tools not available on this system"

    def _act_screenshot(self, save_dir: Optional[str] = None) -> str:
        if not HAS_PYAUTO:
            return "pyautogui not installed. Run: pip install pyautogui"
        save_dir = save_dir or os.path.expanduser("~/Desktop")
        os.makedirs(save_dir, exist_ok=True)
        ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(save_dir, f"nandhi_{ts}.png")
        pyautogui.screenshot(path)
        return f"Screenshot saved: {path}"

    def _act_list_downloads(self) -> str:
        dl = os.path.expanduser("~/Downloads")
        files = sorted(Path(dl).iterdir(), key=lambda f: f.stat().st_mtime, reverse=True)[:15]
        lines = [f"{f.name} ({f.stat().st_size//1024}KB)" for f in files if f.is_file()]
        return f"Recent files in ~/Downloads:\n" + "\n".join(lines) if lines else "Downloads folder is empty."

    # ══════════════════════════════════════════════════════
    #  LAUNCHERS
    # ══════════════════════════════════════════════════════

    def _act_open_browser(self, url: str = "https://www.google.com") -> str:
        webbrowser.open(url)
        return f"Browser opened: {url}"

    def _act_open_vscode(self, path: str = ".") -> str:
        subprocess.Popen(["code", path], shell=(OS == "Windows"))
        return f"VS Code launched in: {os.path.abspath(path)}"

    def _act_open_terminal(self) -> str:
        if OS == "Darwin":
            subprocess.Popen(["open", "-a", "Terminal"])
        elif OS == "Windows":
            subprocess.Popen("start cmd", shell=True)
        else:
            for term in ("gnome-terminal","xterm","konsole","x-terminal-emulator"):
                try: subprocess.Popen([term]); break
                except FileNotFoundError: continue
        return "Terminal window opened"

    def _act_open_explorer(self, path: str = "~") -> str:
        path = os.path.expanduser(path)
        if OS == "Windows":    subprocess.Popen(["explorer", path])
        elif OS == "Darwin":   subprocess.Popen(["open", path])
        else:                  subprocess.Popen(["xdg-open", path])
        return f"File explorer opened: {path}"

    # ══════════════════════════════════════════════════════
    #  DESTRUCTIVE (requires caller confirmation)
    # ══════════════════════════════════════════════════════

    def _act_organize_downloads(self) -> str:
        dl = os.path.expanduser("~/Downloads")
        type_map = {
            "Images":    (".png",".jpg",".jpeg",".gif",".webp",".svg",".bmp",".ico"),
            "Documents": (".pdf",".docx",".doc",".txt",".xlsx",".csv",".pptx",".odt",".rtf"),
            "Videos":    (".mp4",".mov",".avi",".mkv",".wmv",".flv",".webm"),
            "Audio":     (".mp3",".wav",".flac",".m4a",".aac",".ogg"),
            "Archives":  (".zip",".tar",".gz",".rar",".7z",".bz2"),
            "Code":      (".py",".js",".ts",".html",".css",".json",".sh",".yaml",".toml"),
            "Executables":(".exe",".dmg",".pkg",".deb",".rpm",".msi"),
        }
        moved, skipped = 0, 0
        for fname in os.listdir(dl):
            fpath = os.path.join(dl, fname)
            if not os.path.isfile(fpath): continue
            ext = Path(fname).suffix.lower()
            folder_name = next((k for k, exts in type_map.items() if ext in exts), "Other")
            dest_dir  = os.path.join(dl, folder_name)
            os.makedirs(dest_dir, exist_ok=True)
            dest_path = os.path.join(dest_dir, fname)
            if os.path.exists(dest_path):
                skipped += 1
            else:
                shutil.move(fpath, dest_path)
                moved += 1
        return f"Organized {moved} files into folders ({skipped} skipped — already existed)"

    def _act_empty_trash(self) -> str:
        if OS == "Darwin":
            subprocess.run(["osascript","-e",'tell app "Finder" to empty trash'], timeout=15)
            return "Trash emptied"
        elif OS == "Windows":
            try:
                import winshell
                winshell.recycle_bin().empty(confirm=False, show_progress=False, sound=False)
                return "Recycle Bin emptied"
            except ImportError:
                return "winshell not installed. Run: pip install winshell"
        else:
            trash = os.path.expanduser("~/.local/share/Trash/files")
            count = len(os.listdir(trash)) if os.path.exists(trash) else 0
            shutil.rmtree(trash, ignore_errors=True)
            os.makedirs(trash, exist_ok=True)
            return f"Trash emptied ({count} items removed)"

    def _act_kill_process(self, name: str = "", pid: int = 0) -> str:
        if not HAS_PSUTIL:
            return "psutil not installed — cannot kill processes"
        killed = []
        for p in psutil.process_iter(["pid","name"]):
            try:
                if (name and name.lower() in p.info["name"].lower()) or (pid and p.info["pid"] == pid):
                    p.kill()
                    killed.append(f"{p.info['name']}({p.info['pid']})")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return f"Killed: {', '.join(killed)}" if killed else "No matching process found"

    def _act_delete_file(self, path: str) -> str:
        path = os.path.expanduser(path)
        if not os.path.exists(path):
            return f"File not found: {path}"
        if os.path.isdir(path):
            shutil.rmtree(path)
            return f"Directory deleted: {path}"
        os.remove(path)
        return f"File deleted: {path}"

    def _act_run_shell(self, command: str, timeout: int = 30) -> str:
        """Run an arbitrary shell command — always requires confirmation."""
        result = subprocess.run(
            command, shell=True, timeout=timeout,
            capture_output=True, text=True, errors="replace"
        )
        out = (result.stdout + result.stderr).strip()
        return out[:1000] if out else f"Exit code: {result.returncode}"


# Singleton
automator = OsAutomator()
