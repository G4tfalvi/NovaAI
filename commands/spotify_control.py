import time
import ctypes
from ctypes import wintypes

import pyautogui


class SpotifyController:

    def __init__(self, apps=None, system=None):
        self.apps = apps
        self.system = system

        pyautogui.PAUSE = 0.05
        pyautogui.FAILSAFE = True

    def _get_window_title(self, hwnd):
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)

        if length <= 0:
            return ""

        buffer = ctypes.create_unicode_buffer(length + 1)

        ctypes.windll.user32.GetWindowTextW(
            hwnd,
            buffer,
            length + 1
        )

        return buffer.value

    def _find_spotify_window(self):
        user32 = ctypes.windll.user32
        found_window = None

        @ctypes.WINFUNCTYPE(
            wintypes.BOOL,
            wintypes.HWND,
            wintypes.LPARAM
        )
        def enum_callback(hwnd, lparam):
            nonlocal found_window

            if found_window:
                return False

            if not user32.IsWindowVisible(hwnd):
                return True

            title = self._get_window_title(hwnd)

            if not title:
                return True

            if "spotify" in title.lower():
                found_window = hwnd
                return False

            return True

        user32.EnumWindows(
            enum_callback,
            0
        )

        return found_window

    def _wait_for_spotify(self, timeout=10.0):
        start = time.monotonic()

        while time.monotonic() - start < timeout:
            hwnd = self._find_spotify_window()

            if hwnd:
                return hwnd

            time.sleep(0.15)

        return None

    def focus_spotify(self):
        hwnd = self._find_spotify_window()

        if not hwnd:
            return False

        user32 = ctypes.windll.user32

        try:
            if user32.IsIconic(hwnd):
                user32.ShowWindow(hwnd, 9)

            user32.ShowWindow(hwnd, 5)
            user32.SetForegroundWindow(hwnd)

            time.sleep(0.25)

            return True

        except Exception as e:
            print(
                f"❌ Spotify fókusz hiba: {e}"
            )

            return False

    def open_spotify(self):
        hwnd = self._find_spotify_window()

        if hwnd:
            return self.focus_spotify()

        if not self.apps:
            return False

        try:
            app = self.apps.find_app("spotify")

            if not app:
                print("❌ Nem találom a Spotify alkalmazást.")
                return False

            if not self.apps.open_app("spotify"):
                return False

        except Exception as e:
            print(
                f"❌ Spotify indítási hiba: {e}"
            )

            return False

        hwnd = self._wait_for_spotify(
            timeout=10.0
        )

        if not hwnd:
            print(
                "❌ A Spotify ablak nem jelent meg."
            )

            return False

        return self.focus_spotify()

    def prepare_spotify(self):
        hwnd = self._find_spotify_window()

        if not hwnd:
            if not self.open_spotify():
                return False

        else:
            if not self.focus_spotify():
                return False

        time.sleep(1.0)

        return True

    def open_playlist(self, index=1):
        try:
            index = int(index)
        except (TypeError, ValueError):
            return "Nem érvényes playlist sorszámot adtál meg."

        if index < 1:
            return "A playlist sorszáma legalább 1 kell legyen."

        if not self.prepare_spotify():
            return "Nem sikerült megnyitnom a Spotifyt."

        print(
            f"🎵 Spotify playlist navigáció: {index}. playlist"
        )

        pyautogui.press("home")

        time.sleep(0.2)

        for _ in range(3):
            pyautogui.press("tab")
            time.sleep(0.08)

        pyautogui.press("down")

        time.sleep(0.15)

        for _ in range(index - 1):
            pyautogui.press("down")
            time.sleep(0.08)

        pyautogui.press("enter")

        time.sleep(0.8)

        return (
            f"Megnyitottam a Spotify "
            f"{index}. playlistjét."
        )

    def play_pause(self):
        if not self.prepare_spotify():
            return "Nem sikerült elérnem a Spotifyt."

        time.sleep(1)

        pyautogui.press(
            "playpause"
        )

        return "Lejátszás/szünet."

    def next_track(self):
        if not self.prepare_spotify():
            return "Nem sikerült elérnem a Spotifyt."

        time.sleep(1)

        pyautogui.press(
            "nexttrack"
        )

        return "Következő szám."

    def previous_track(self):
        if not self.prepare_spotify():
            return "Nem sikerült elérnem a Spotifyt."

        time.sleep(1)

        pyautogui.press(
            "prevtrack"
        )

        return "Előző szám."