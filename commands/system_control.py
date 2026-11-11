import ctypes
import subprocess
import time
from ctypes import wintypes

import pyautogui


class SystemController:

    def __init__(self):
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.05

    def volume_up(self):
        for _ in range(5):
            pyautogui.press("volumeup")

        return "Feljebb vettem a hangerőt."

    def volume_down(self):
        for _ in range(5):
            pyautogui.press("volumedown")

        return "Lejjebb vettem a hangerőt."

    def volume_mute(self):
        pyautogui.press("volumemute")
        return "Lenémítottam a hangot."

    def volume_set(self, value):
        try:
            value = max(0, min(100, int(value)))

            from ctypes import POINTER, cast
            import math

            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

            devices = AudioUtilities.GetSpeakers()

            interface = devices.Activate(
                IAudioEndpointVolume._iid_,
                CLSCTX_ALL,
                None
            )

            volume = cast(
                interface,
                POINTER(IAudioEndpointVolume)
            )

            if value == 0:
                volume_db = -65.25
            else:
                volume_db = max(
                    -65.25,
                    20 * math.log10(value / 100)
                )

            volume.SetMasterVolumeLevel(
                volume_db,
                None
            )

            return f"A hangerőt {value} százalékra állítottam."

        except Exception as e:
            print(f"❌ Hangerő beállítási hiba: {e}")
            return "Nem sikerült beállítanom a hangerőt."

    def brightness_up(self):
        try:
            subprocess.run(
                [
                    "powershell",
                    "-Command",
                    "(Get-WmiObject -Namespace root/wmi "
                    "-Class WmiMonitorBrightnessMethods)"
                    ".WmiSetBrightness(1, [math]::Min(100, "
                    "(Get-WmiObject -Namespace root/wmi "
                    "-Class WmiMonitorBrightness)"
                    ".CurrentBrightness + 10))"
                ],
                capture_output=True,
                timeout=5
            )

            return "Feljebb vettem a fényerőt."

        except Exception as e:
            print(f"❌ Fényerő hiba: {e}")
            return "Nem sikerült megváltoztatnom a fényerőt."

    def brightness_down(self):
        try:
            subprocess.run(
                [
                    "powershell",
                    "-Command",
                    "(Get-WmiObject -Namespace root/wmi "
                    "-Class WmiMonitorBrightnessMethods)"
                    ".WmiSetBrightness(1, [math]::Max(0, "
                    "(Get-WmiObject -Namespace root/wmi "
                    "-Class WmiMonitorBrightness)"
                    ".CurrentBrightness - 10))"
                ],
                capture_output=True,
                timeout=5
            )

            return "Lejjebb vettem a fényerőt."

        except Exception as e:
            print(f"❌ Fényerő hiba: {e}")
            return "Nem sikerült megváltoztatnom a fényerőt."

    def close_window(self):
        pyautogui.hotkey("alt", "f4")
        return "Bezártam az ablakot."

    def minimize_window(self):
        pyautogui.hotkey("win", "down")
        return "Minimalizáltam az ablakot."

    def maximize_window(self):
        pyautogui.hotkey("win", "up")
        return "Maximalizáltam az ablakot."

    def full_screen(self):
        pyautogui.press("f11")
        return "Teljes képernyőre váltottam."

    def switch_window(self):
        pyautogui.hotkey("alt", "tab")
        return "Átváltottam a másik ablakra."

    def show_desktop(self):
        pyautogui.hotkey("win", "d")
        return "Megmutattam az asztalt."

    def open_task_manager(self):
        pyautogui.hotkey("ctrl", "shift", "esc")
        return "Megnyitottam a feladatkezelőt."

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

    def _find_window(self, target):
        target = target.lower().strip()

        aliases = {
            "discord": ["discord"],
            "chrome": ["google chrome", "chrome", "google"],
            "google": ["google chrome", "chrome", "google"],
            "youtube": ["youtube"],
            "spotify": ["spotify"],
            "vscode": ["visual studio code", "vs code"],
            "visual studio code": ["visual studio code"],
        }

        search_terms = aliases.get(
            target,
            [target]
        )

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
                return True

            if not user32.IsWindowVisible(hwnd):
                return True

            title = self._get_window_title(hwnd)

            if not title:
                return True

            title_lower = title.lower()

            if any(
                term in title_lower
                for term in search_terms
            ):
                found_window = hwnd
                return False

            return True

        user32.EnumWindows(
            enum_callback,
            0
        )

        return found_window

    def _wait_for_window(
        self,
        target,
        timeout=6.0,
        interval=0.10
    ):
        start_time = time.monotonic()

        while (
            time.monotonic() - start_time
            < timeout
        ):
            hwnd = self._find_window(target)

            if hwnd:
                return hwnd

            time.sleep(interval)

        return None

    def activate_application(self, target):
        hwnd = self._find_window(target)

        if not hwnd:
            return f"Nem találtam meg a(z) {target} alkalmazást."

        user32 = ctypes.windll.user32

        try:
            if user32.IsIconic(hwnd):
                user32.ShowWindow(hwnd, 9)

            user32.ShowWindow(hwnd, 5)

            foreground = user32.GetForegroundWindow()

            if foreground != hwnd:
                user32.SetForegroundWindow(hwnd)

            return f"Átváltottam a(z) {target} alkalmazásra."

        except Exception:
            return f"Nem sikerült átváltanom a(z) {target} alkalmazásra."

    def close_application(self, target):
        hwnd = self._find_window(target)

        if not hwnd:
            return f"Nem találtam meg a(z) {target} alkalmazást."

        user32 = ctypes.windll.user32

        try:
            result = user32.PostMessageW(
                hwnd,
                0x0010,
                0,
                0
            )

            if not result:
                return f"Nem sikerült bezárnom a(z) {target} alkalmazást."

            return f"Bezártam a(z) {target} alkalmazást."

        except Exception:
            return f"Nem sikerült bezárnom a(z) {target} alkalmazást."

    def _get_work_area(self):
        class RECT(ctypes.Structure):
            _fields_ = [
                ("left", wintypes.LONG),
                ("top", wintypes.LONG),
                ("right", wintypes.LONG),
                ("bottom", wintypes.LONG)
            ]

        rect = RECT()

        ctypes.windll.user32.SystemParametersInfoW(
            0x0030,
            0,
            ctypes.byref(rect),
            0
        )

        return (
            rect.left,
            rect.top,
            rect.right,
            rect.bottom
        )

    def _move_window_to_side(self, target, side):
        hwnd = self._wait_for_window(
            target,
            timeout=6.0,
            interval=0.10
        )

        if not hwnd:
            return f"Nem találtam meg a(z) {target} ablakot."

        user32 = ctypes.windll.user32

        user32.ShowWindow(hwnd, 9)

        left, top, right, bottom = self._get_work_area()

        width = right - left
        height = bottom - top
        half_width = width // 2

        if side == "left":
            x = left
            window_width = half_width
        else:
            x = left + half_width
            window_width = width - half_width

        moved = user32.MoveWindow(
            hwnd,
            x,
            top,
            window_width,
            height,
            True
        )

        if not moved:
            return (
                f"Nem sikerült áthelyeznem "
                f"a(z) {target} ablakot."
            )

        user32.SetForegroundWindow(hwnd)

        if side == "left":
            return f"A(z) {target} ablakot a bal oldalra tettem."

        return f"A(z) {target} ablakot a jobb oldalra tettem."

    def move_window_left(self, target):
        return self._move_window_to_side(
            target,
            "left"
        )

    def move_window_right(self, target):
        return self._move_window_to_side(
            target,
            "right"
        )