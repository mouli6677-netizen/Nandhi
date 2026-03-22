# learning/behavior_tracker.py  ──  Nandhi AI Self-Learning Engine
# Tracks user habits, detects repeated patterns, and proposes automations.

import os, json, time, logging
from collections import defaultdict, Counter
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Optional, Tuple

log = logging.getLogger("nandhi.learning")

STORE_FILE = "data/behavior_store.json"
os.makedirs("data", exist_ok=True)


class BehaviorTracker:
    """
    Records user actions and detects automation opportunities.

    Tracked signals
    ───────────────
    • Commands issued (text)
    • Time-of-day patterns
    • Frequency of specific queries / app opens
    • Sequences (A then B then C)
    """

    def __init__(self, store_path: str = STORE_FILE):
        self.store_path = store_path
        self._data: Dict = self._load()

    # ── Persistence ────────────────────────────────────────
    def _load(self) -> dict:
        if os.path.exists(self.store_path):
            try:
                with open(self.store_path, "r") as f:
                    return json.load(f)
            except Exception as e:
                log.warning(f"Could not load behavior store: {e}")
        return {
            "commands":    [],       # [{text, ts, hour, weekday}]
            "freq_map":    {},       # normalized_text -> count
            "hourly":      {},       # "HH" -> count
            "sequences":   [],       # [(cmd_a, cmd_b)]
            "automations": [],       # suggested {id, text, trigger, confirmed}
            "preferences": {},       # key -> value
        }

    def _save(self):
        try:
            with open(self.store_path, "w") as f:
                json.dump(self._data, f, indent=2)
        except Exception as e:
            log.error(f"Could not save behavior store: {e}")

    # ── Core tracking ──────────────────────────────────────
    def record_command(self, text: str):
        """Record a command/query from the user."""
        now  = datetime.now()
        hour = now.strftime("%H")
        wd   = now.strftime("%A")
        entry = {"text": text, "ts": now.isoformat(), "hour": hour, "weekday": wd}
        self._data["commands"].append(entry)

        # Keep last 1000
        if len(self._data["commands"]) > 1000:
            self._data["commands"] = self._data["commands"][-1000:]

        # Frequency map
        key = self._normalize(text)
        self._data["freq_map"][key] = self._data["freq_map"].get(key, 0) + 1

        # Hourly heatmap
        self._data["hourly"][hour] = self._data["hourly"].get(hour, 0) + 1

        # Sequence tracking (last 2 commands)
        if len(self._data["commands"]) >= 2:
            prev = self._normalize(self._data["commands"][-2]["text"])
            seq  = [prev, key]
            self._data["sequences"].append(seq)
            if len(self._data["sequences"]) > 2000:
                self._data["sequences"] = self._data["sequences"][-2000:]

        self._save()

    # ── Analysis ───────────────────────────────────────────
    def top_commands(self, n: int = 10) -> List[Tuple[str, int]]:
        """Return the n most frequent command keys and their counts."""
        return sorted(self._data["freq_map"].items(), key=lambda x: x[1], reverse=True)[:n]

    def peak_hours(self, n: int = 3) -> List[str]:
        """Return the top-n most active hours."""
        return [h for h, _ in sorted(self._data["hourly"].items(), key=lambda x: x[1], reverse=True)[:n]]

    def top_sequences(self, n: int = 5) -> List[Tuple[Tuple[str,str], int]]:
        """Return most frequent command pairs."""
        counter: Counter = Counter(tuple(s) for s in self._data["sequences"])
        return counter.most_common(n)

    # ── Automation suggestions ──────────────────────────────
    def generate_suggestions(self, threshold: int = 3) -> List[Dict]:
        """
        Propose automations for commands that appear ≥ threshold times.
        Returns list of suggestion dicts.
        """
        suggestions = []

        # High-frequency single commands
        for cmd, count in self.top_commands(20):
            if count >= threshold:
                peak = self.peak_hours(1)
                trigger = f"~{peak[0]}:00 daily" if peak else f"{count}x recorded"
                suggestions.append({
                    "id":      f"auto_{cmd[:20]}",
                    "text":    f"You frequently say: "{cmd}". Automate it?",
                    "trigger": trigger,
                    "count":   count,
                    "cmd":     cmd,
                })

        # High-frequency sequences
        for (a, b), count in self.top_sequences(5):
            if count >= threshold:
                suggestions.append({
                    "id":      f"seq_{a[:12]}_{b[:12]}",
                    "text":    f"You always do "{a}" then "{b}". Create a workflow?",
                    "trigger": f"{count}x in sequence",
                    "count":   count,
                    "cmd":     f"{a} then {b}",
                })

        # Store suggestions for reference
        self._data["automations"] = suggestions[:10]
        self._save()
        return suggestions[:10]

    # ── Preferences ────────────────────────────────────────
    def set_preference(self, key: str, value):
        self._data["preferences"][key] = {"value": value, "ts": datetime.now().isoformat()}
        self._save()

    def get_preference(self, key: str, default=None):
        entry = self._data["preferences"].get(key)
        return entry["value"] if entry else default

    # ── Summary for dashboard ───────────────────────────────
    def summary(self) -> Dict:
        return {
            "total_commands":   len(self._data["commands"]),
            "unique_commands":  len(self._data["freq_map"]),
            "top_commands":     self.top_commands(5),
            "peak_hours":       self.peak_hours(3),
            "suggestions":      self.generate_suggestions(threshold=3),
        }

    @staticmethod
    def _normalize(text: str) -> str:
        return text.lower().strip()[:80]


# ── Scheduler (simple cron-like) ──────────────────────────
import threading

class SimpleScheduler:
    """Runs callables at specified times (HH:MM) daily."""

    def __init__(self):
        self._jobs: List[Dict] = []
        self._thread: Optional[threading.Thread] = None
        self._stop  = threading.Event()

    def add(self, label: str, time_str: str, fn, *args, **kwargs):
        """Add a daily job. time_str format: "HH:MM"."""
        self._jobs.append({"label": label, "time": time_str, "fn": fn, "args": args, "kwargs": kwargs, "last_run": None})
        log.info(f"[Scheduler] Added: {label} at {time_str}")

    def _loop(self):
        while not self._stop.is_set():
            now = datetime.now().strftime("%H:%M")
            today = date.today().isoformat()
            for job in self._jobs:
                if job["time"] == now and job["last_run"] != today:
                    job["last_run"] = today
                    log.info(f"[Scheduler] Running: {job['label']}")
                    try:
                        job["fn"](*job["args"], **job["kwargs"])
                    except Exception as e:
                        log.error(f"[Scheduler] {job['label']} failed: {e}")
            self._stop.wait(30)  # check every 30s

    def start(self):
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()

    def list_jobs(self) -> List[Dict]:
        return [{"label": j["label"], "time": j["time"], "last_run": j["last_run"]} for j in self._jobs]


# Singletons
tracker   = BehaviorTracker()
scheduler = SimpleScheduler()
