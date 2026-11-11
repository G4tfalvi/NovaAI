import os
import time
import subprocess
from pathlib import Path


class FileController:

    def __init__(self):
        self.home = Path.home()

    def open_folder(self, path):

        path = Path(path)

        if not path.exists() or not path.is_dir():
            return f"Nem találom ezt a mappát: {path}"

        try:
            os.startfile(str(path))
            return f"Megnyitottam: {path.name}."

        except Exception as e:
            print(f"❌ Mappa megnyitási hiba: {e}")
            return "Nem sikerült megnyitnom a mappát."

    def open_file(self, path):

        path = Path(path)

        if not path.exists():
            return f"Nem találom ezt a fájlt: {path}"

        try:
            os.startfile(str(path))
            return f"Megnyitottam: {path.name}."

        except Exception as e:
            print(f"❌ Fájl megnyitási hiba: {e}")
            return "Nem sikerült megnyitnom a fájlt."

    def show_in_explorer(self, path):

        path = Path(path)

        if not path.exists():
            return f"Nem találom: {path}"

        try:

            if path.is_dir():
                subprocess.Popen([
                    "explorer",
                    str(path)
                ])

            else:
                subprocess.Popen([
                    "explorer",
                    "/select,",
                    str(path)
                ])

            return f"Megmutattam: {path.name}."

        except Exception as e:
            print(f"❌ Explorer hiba: {e}")
            return "Nem sikerült megnyitnom a fájl helyét."

    def get_search_roots(self):

        roots = [
            self.home / "Desktop",
            self.home / "Documents",
            self.home / "Downloads",
            self.home / "Pictures",
            self.home / "Videos",
            self.home / "Music",
            self.home / "AppData" / "Local",
            self.home / "AppData" / "Roaming",
        ]

        roots = [
            path
            for path in roots
            if path.exists()
        ]

        return roots

    def search(self, query, max_results=20, time_budget=3.0):

        query = query.lower().strip()

        if not query:
            return []

        skip_dirs = {
            "node_modules",
            ".git",
            "__pycache__",
            "venv",
            ".venv",
            "$recycle.bin",
            "system volume information"
        }

        results = []
        roots = self.get_search_roots()

        start = time.monotonic()

        for root in roots:

            if time.monotonic() - start > time_budget:
                break

            try:

                for current_dir, dirnames, filenames in os.walk(root):

                    if time.monotonic() - start > time_budget:
                        break

                    dirnames[:] = [
                        name
                        for name in dirnames
                        if name.lower() not in skip_dirs
                    ]

                    for name in dirnames + filenames:

                        if len(results) >= max_results:
                            return results

                        if query in name.lower():

                            path = Path(current_dir) / name

                            if path not in results:
                                results.append(path)

            except (PermissionError, OSError):
                continue

        return results

    def search_text(self, query):

        results = self.search(query)

        if not results:
            return "Nem találtam ilyen fájlt vagy mappát."

        lines = [
            f"{index}. {path}"
            for index, path in enumerate(
                results,
                start=1
            )
        ]

        return (
            "Találtam néhány találatot:\n"
            + "\n".join(lines)
        )

    def open_search_result(self, query):

        results = self.search(
            query,
            max_results=20
        )

        if not results:
            return "Nem találtam ilyen fájlt vagy mappát."

        folders = [
            path
            for path in results
            if path.is_dir()
        ]

        if folders:
            return self.open_folder(
                folders[0]
            )

        return self.open_file(
            results[0]
        )

    def show_search_result(self, query):

        results = self.search(
            query,
            max_results=20
        )

        if not results:
            return "Nem találtam ilyen fájlt vagy mappát."

        folders = [
            path
            for path in results
            if path.is_dir()
        ]

        if folders:
            return self.show_in_explorer(
                folders[0]
            )

        return self.show_in_explorer(
            results[0]
        )