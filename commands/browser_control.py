import webbrowser
import urllib.parse
import pyautogui


class BrowserController:

    def __init__(self):
        self.browser_name = "böngésző"

    def open_url(self, url):
        try:
            webbrowser.open(url)
            return True
        except Exception as e:
            print(f"❌ Böngésző megnyitási hiba: {e}")
            return False

    def search_google(self, query):
        query = query.strip()

        if not query:
            return False

        url = (
            "https://www.google.com/search?q="
            + urllib.parse.quote_plus(query)
        )

        return self.open_url(url)

    def back(self):
        try:
            pyautogui.hotkey("alt", "left")
            return True
        except Exception as e:
            print(f"❌ Vissza hiba: {e}")
            return False

    def forward(self):
        try:
            pyautogui.hotkey("alt", "right")
            return True
        except Exception as e:
            print(f"❌ Előre hiba: {e}")
            return False

    def refresh(self):
        try:
            pyautogui.press("f5")
            return True
        except Exception as e:
            print(f"❌ Frissítés hiba: {e}")
            return False

    def new_tab(self):
        try:
            pyautogui.hotkey("ctrl", "t")
            return True
        except Exception as e:
            print(f"❌ Új lap hiba: {e}")
            return False

    def close_tab(self):
        try:
            pyautogui.hotkey("ctrl", "w")
            return True
        except Exception as e:
            print(f"❌ Lap bezárási hiba: {e}")
            return False

    def reopen_closed_tab(self):
        try:
            pyautogui.hotkey("ctrl", "shift", "t")
            return True
        except Exception as e:
            print(f"❌ Bezárt lap visszaállítási hiba: {e}")
            return False

    def focus_address_bar(self):
        try:
            pyautogui.hotkey("ctrl", "l")
            return True
        except Exception as e:
            print(f"❌ Címsor hiba: {e}")
            return False