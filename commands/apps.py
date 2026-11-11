import os
import re
import unicodedata
import subprocess
from pathlib import Path
from difflib import SequenceMatcher


class AppController:

    def __init__(self):
        self.apps = {}
        self.refresh()

    def normalize(self, text):
        text = text.lower().strip()

        text = unicodedata.normalize(
            "NFD",
            text
        )

        text = "".join(
            char
            for char in text
            if unicodedata.category(char) != "Mn"
        )

        text = re.sub(
            r"[^a-z0-9 ]",
            " ",
            text
        )

        text = re.sub(
            r"\s+",
            " ",
            text
        )

        return text.strip()

    def add_app(self, name, path):
        if not name or not path:
            return

        path = str(path)

        if not os.path.exists(path):
            return

        key = self.normalize(name)

        if not key:
            return

        if key not in self.apps:
            self.apps[key] = {
                "name": name,
                "path": path
            }

    def get_start_menu_paths(self):
        paths = []

        appdata = os.environ.get("APPDATA", "")
        programdata = os.environ.get("PROGRAMDATA", "")

        user_start = (
            Path(appdata)
            / "Microsoft"
            / "Windows"
            / "Start Menu"
            / "Programs"
        )

        common_start = (
            Path(programdata)
            / "Microsoft"
            / "Windows"
            / "Start Menu"
            / "Programs"
        )

        if user_start.exists():
            paths.append(user_start)

        if common_start.exists():
            paths.append(common_start)

        return paths

    def refresh(self):
        self.apps.clear()

        for start_path in self.get_start_menu_paths():
            try:
                for file in start_path.rglob("*"):
                    if not file.is_file():
                        continue

                    suffix = file.suffix.lower()

                    if suffix == ".lnk":
                        self.add_app(
                            file.stem.strip(),
                            file
                        )

                    elif suffix == ".exe":
                        self.add_app(
                            file.stem.strip(),
                            file
                        )

            except (PermissionError, OSError):
                continue

        self._find_installed_executables()

    def _find_installed_executables(self):
        locations = []

        program_files = os.environ.get("PROGRAMFILES")
        program_files_x86 = os.environ.get("PROGRAMFILES(X86)")
        local_appdata = os.environ.get("LOCALAPPDATA")

        if program_files:
            locations.append(Path(program_files))

        if program_files_x86:
            locations.append(Path(program_files_x86))

        if local_appdata:
            locations.append(Path(local_appdata))

        for base_path in locations:
            if not base_path.exists():
                continue

            try:
                for file in base_path.rglob("*.exe"):
                    if not file.is_file():
                        continue

                    name = file.stem.strip()

                    if name:
                        self.add_app(
                            name,
                            file
                        )

            except (PermissionError, OSError):
                continue

    def similarity(self, a, b):
        return SequenceMatcher(
            None,
            self.normalize(a),
            self.normalize(b)
        ).ratio()

    def find_app(self, query):
        query = self.normalize(query)

        if not query:
            return None

        if query in self.apps:
            return self.apps[query]

        best_app = None
        best_score = 0.0

        for key, app in self.apps.items():
            score = self.similarity(
                query,
                key
            )

            if query == key:
                score = 1.0

            elif query in key:
                score = max(
                    score,
                    0.90
                )

            if score > best_score:
                best_score = score
                best_app = app

        if best_app:
            print(
                f"🔎 Találat: "
                f"{best_app['name']} "
                f"({best_score:.2f})"
            )

        if best_score >= 0.65:
            return best_app

        return None

    def open_app(self, query):
        app = self.find_app(query)

        if not app:
            print(
                f"❌ Nem találom: {query}"
            )
            return False

        path = app["path"]

        try:
            detached = (
                subprocess.DETACHED_PROCESS |
                subprocess.CREATE_NEW_PROCESS_GROUP |
                subprocess.CREATE_BREAKAWAY_FROM_JOB
            )

            if path.lower().endswith(".lnk"):
                subprocess.Popen(
                    [
                        "cmd",
                        "/c",
                        "start",
                        "",
                        path
                    ],
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=detached
                )

            elif path.lower().endswith(".exe"):
                subprocess.Popen(
                    [path],
                    cwd=os.path.dirname(path),
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=detached
                )

            else:
                subprocess.Popen(
                    [
                        "cmd",
                        "/c",
                        "start",
                        "",
                        path
                    ],
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=detached
                )

            print(
                f"🚀 Elindítva: "
                f"{app['name']} -> {path}"
            )

            return True

        except Exception as e:
            print(
                f"❌ Megnyitási hiba: {e}"
            )

            return False