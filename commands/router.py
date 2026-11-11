import re
import webbrowser
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from urllib.parse import quote_plus
from zoneinfo import ZoneInfo
import time
import ctypes

from commands.spotify_control import SpotifyController
from commands.apps import AppController
from commands.system_control import SystemController
from commands.weather import WeatherController
from commands.file_control import FileController


class CommandRouter:

    def __init__(self, ai=None, tts=None):
        self.ai = ai
        self.tts = tts
        self.apps = AppController()
        self.system = SystemController()
        self.weather = WeatherController()
        self.files = FileController()
        self.spotify = SpotifyController(
			self.apps,
			self.system
		)

        self.websites = {
            "youtube": "https://www.youtube.com",
            "github": "https://github.com",
            "instagram": "https://www.instagram.com",
            "facebook": "https://www.facebook.com",
            "gmail": "https://mail.google.com",
            "messenger": "https://www.messenger.com",
            "chatgpt": "https://chatgpt.com",
            "tiktok": "https://www.tiktok.com",
            "twitch": "https://www.twitch.tv",
            "netflix": "https://www.netflix.com"
        }

        self.app_aliases = {
            "discord": "discord",
            "spotify": "spotify",
            "google": "chrome",
            "chrome": "chrome",
            "google chrome": "chrome",
            "visual studio code": "vscode",
            "vs code": "vscode",
            "vscode": "vscode",
            "minecraft": "minecraft",
            "firefox": "firefox",
            "edge": "edge"
        }

        self.window_aliases = {
            "discord": "discord",
            "spotify": "spotify",
            "google": "chrome",
            "chrome": "chrome",
            "google chrome": "chrome",
            "visual studio code": "vscode",
            "vs code": "vscode",
            "vscode": "vscode",
            "minecraft": "minecraft",
            "firefox": "firefox",
            "edge": "edge"
        }

    def normalize(self, text):
        if not text:
            return ""

        text = str(text).lower().strip()
        text = text.replace("-", " ")
        text = re.sub(r"[.!?,;:]+", " ", text)
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    def similar(self, a, b, threshold=0.78):
        if not a or not b:
            return False

        return SequenceMatcher(
            None,
            a,
            b
        ).ratio() >= threshold

    def contains_similar_word(self, text, words, threshold=0.78):
        current_words = self.normalize(text).split()

        for current in current_words:
            for target in words:
                if current == target:
                    return True

                if self.similar(
                    current,
                    target,
                    threshold
                ):
                    return True

        return False

    def contains_any_phrase(self, text, phrases):
        text = self.normalize(text)

        return any(
            phrase in text
            for phrase in phrases
        )

    def interrupt_speech(self):
        if not self.tts:
            return False

        try:
            if hasattr(self.tts, "stop"):
                self.tts.stop()
                return True

            if hasattr(self.tts, "interrupt"):
                self.tts.interrupt()
                return True

        except Exception:
            return False

        return False

    def is_interrupt_command(self, text):
        t = self.normalize(text)

        phrases = {
            "állj",
            "allj",
            "állj meg",
            "allj meg",
            "hagyd abba",
            "hagyd már abba",
            "elég",
            "elég már",
            "elég volt",
            "várj",
            "varj",
            "stop",
            "csend",
            "csend legyen",
            "hallgass",
            "hallgass el",
            "ne beszélj",
            "ne beszélj tovább",
            "fejezd be",
            "fejezd már be",
            "állítsd le",
            "állítsd le a beszédet",
            "állitsd le",
            "állitsd le a beszédet"
        }

        if t in phrases:
            return True

        return self.contains_any_phrase(
            t,
            phrases
        )

    def fix_speech_errors(self, text):
        t = self.normalize(text)

        corrections = {
            "nézd": "nyisd",
            "nezd": "nyisd",
            "néz": "nyisd",
            "nez": "nyisd",
            "nyersd": "nyisd",
            "nyerst": "nyisd",
            "nyist": "nyisd",
            "nyíst": "nyisd",
            "nyizd": "nyisd",
            "nyízd": "nyisd",
            "nízd": "nyisd",
            "nyis": "nyisd",
            "nyissd": "nyisd",
            "nyíjd": "nyisd",
            "nincsd": "nyisd",

            "időjánás": "időjárás",
            "idojanas": "időjárás",
            "időjarás": "időjárás",
            "idojarás": "időjárás",

            "keres": "keress",
            "keresdmeg": "keresd meg",

            "íg": "ég",
            "eg": "ég",

            "discordot": "discord",
            "diskord": "discord",
            "diskordot": "discord",
            "discort": "discord",
            "discortot": "discord",
            "diszkord": "discord",
            "diszkordot": "discord",
            "diszkort": "discord",

            "youtubeot": "youtube",
            "youtubot": "youtube",
            "youtubeon": "youtube",
            "youtubeen": "youtube",
            "youtubeön": "youtube",
            "jutub": "youtube",
            "jutubot": "youtube",
            "jutubon": "youtube",
            "jútub": "youtube",
            "jútubot": "youtube",

            "googleot": "google",
            "googlet": "google",
            "googleon": "google",
            "googleben": "google",
            "googleban": "google",

            "minecraftot": "minecraft",
            "minecraf": "minecraft",
            "májkraft": "minecraft",
            "májnkráft": "minecraft",

            "spotifyt": "spotify",
            "spotifáj": "spotify",
            "spotifajt": "spotify",

            "állítsdot": "állítsd",
            "állitsd": "állítsd",
            "álítsd": "állítsd",
            "álitsd": "állítsd",
            "állits": "állíts",
            "álíts": "állíts",

            "hangositsd": "hangosítsd",
            "hangosits": "hangosíts",
            "hangosit": "hangosíts",

            "halkitsd": "halkítsd",
            "halkits": "halkíts",
            "halkit": "halkíts",

            "némitsd": "némítsd",
            "nemitsd": "némítsd",
            "némits": "némíts",
            "nemits": "némíts",

            "magpad": "mappa",
            "magpan": "mappa",
            "magpa": "mappa",
            "magpát": "mappa",
            "mappát": "mappa",
            "mappat": "mappa",
            "moppa": "mappa",
            "moppát": "mappa",
            "moppat": "mappa",
            "mopát": "mappa",
            "mapa": "mappa",
            "mokpad": "mappa",
            "moppad": "mappa",
            "ma pat": "mappa",
            "ma pa": "mappa",

            "valts": "válts",
            "valtsd": "váltsd",
            "válcs": "válts",

            "vadj": "vagy",
            "vadja": "vagy",

            "feladatkezelo": "feladatkezelő",
            "feladatkezelot": "feladatkezelő",

            "minimalizald": "minimalizáld",
            "maximalizald": "maximalizáld",

            "mutajd": "mutasd",
            "mutarjt": "mutasd",
            "mutaj": "mutasd",
            "mutáljt": "mutasd",
            "mutáliszt": "mutasd",

            "hújt": "hogy",
            "hódj": "hogy",
            "vadj": "vagy",
            "vódj": "vagy",
            "húdj": "hogy",
            "vodj": "vagy",
            "hodj": "hogy",
            "vajd": "vagy",
            "vojd": "vagy",

            "litre": "létre",
            "magyarász": "magyarázd",

            "teljeskepernyo": "teljes képernyő",
            "képernyű": "képernyő",
            "letoltesek": "letöltések",
            "letoltes": "letöltés",
            "letőltések": "letöltések",
            "letőtések": "letöltések",
            "letoltések": "letöltések",
            "osztal": "asztal",
            "osztalt": "asztal",
            "aztalt": "asztal",
            "oztolt": "asztal",
            "ostalt": "asztal",
            "ostal": "asztal",
            "kepek": "képek",
            "kep": "kép",
            "kípek": "képek",
            "kípet": "képet",

            "dokumentum": "dokumentumok",

            "wikipédia": "wikipedia",
            "wikipedija": "wikipedia",

            "baloldalra": "balra",
            "baloldal": "balra",
            "baloldára": "balra",
            "balodóra": "balra",
            "balodora": "balra",
            "baloldara": "balra",
            "bal oldalra": "balra",
            "bal oldalára": "balra",
            "bal oldalara": "balra",
            "balúldora": "balra",
            "bal-oldora": "balra",

            "jobboldalra": "jobbra",
            "jobboldal": "jobbra",
            "jobboldára": "jobbra",
            "jobodóra": "jobbra",
            "jobodora": "jobbra",
            "jobboldara": "jobbra",
            "jobb oldalra": "jobbra",
            "jobb oldalára": "jobbra",
            "jobb oldalara": "jobbra",

            "úldára": "oldalra",
            "uldarra": "oldalra",
            "uldajra": "oldalra",
            "uldolra": "oldalra",

            "helyeszt": "helyezd",
            "helyesd": "helyezd",
            "helyez": "helyezd",

            "menni": "mennyi",
            "megni": "mennyi",
            "magynyi": "mennyi",
            "mani": "mennyi",

            "te helyezd": "helyezd",
            "és te helyezd": "és helyezd",

            "fenyerő": "fényerő",
            "fenyero": "fényerő",
            "fényerot": "fényerőt",
            "fenyerot": "fényerőt",

            "hangerot": "hangerőt",
            "hangerőre": "hangerőt",
            "hangero": "hangerő",
            "hangero t": "hangerőt"
        }

        words = t.split()
        result = []

        i = 0

        while i < len(words):
            if i + 1 < len(words):
                pair = f"{words[i]} {words[i + 1]}"

                if pair in corrections:
                    result.append(corrections[pair])
                    i += 2
                    continue

            result.append(
                corrections.get(
                    words[i],
                    words[i]
                )
            )

            i += 1

        return " ".join(result)

    def split_multi_commands(self, text):
        t = self.fix_speech_errors(text)

        if not t:
            return []

        command_starters = (
            r"nyisd|nyit|nyitd|nyiss|"
            r"indítsd|inditsd|indíts|indits|"
            r"megnyit|keress|keresd|keres|"
            r"nézz|nezz|nézd|nezd|"
            r"zárd|zarad|"
            r"minimalizáld|minimalizald|"
            r"maximalizáld|maximalizald|"
            r"válts|valts|"
            r"némítsd|nemitsd|"
            r"hangosítsd|hangositsd|"
            r"halkítsd|halkitsd|"
            r"mutasd|"
            r"állítsd|allitsd|"
            r"tedd|rakd|vidd|"
            r"helyezd|helyeszt|mozgasd|"
            r"növeld|noveld|"
            r"csökkentsd|csokkentsd"
        )

        parts = re.split(
            r"\s+(?:aztán|aztan|majd|utána|utana)\s+",
            t
        )

        result = []

        for part in parts:
            part = part.strip()

            if not part:
                continue

            subparts = re.split(
                rf"\s+és\s+(?="
                rf"(?:te|azt|utána|utana)?\s*"
                rf"(?:{command_starters})\b"
                rf")",
                part
            )

            for subpart in subparts:
                subpart = subpart.strip()

                if not subpart:
                    continue

                subpart = re.sub(
                    rf"^(?:te|azt|utána|utana)\s+"
                    rf"(?=(?:{command_starters})\b)",
                    "",
                    subpart
                ).strip()

                if subpart:
                    result.append(subpart)

        return result

    def clean_search_query(self, query):
        if not query:
            return None

        query = self.normalize(query)

        remove_words = {
            "bon",
            "bón",
            "google",
            "youtube",
            "youtubeon",
            "jutub",
            "jutubon",
            "benne",
            "ben",
            "ban",
            "rajta",
            "keress",
            "keresd",
            "keres",
            "keresés",
            "keresésre",
            "keresésben",
            "rá",
            "ra",
            "re",
            "meg",
            "ki",
            "a",
            "az",
            "egy",
            "erre",
            "ezt",
            "ezen",
            "nézz",
            "nezz",
            "utána",
            "utana",
            "on",
            "en",
            "ön"
        }

        result = []

        for word in query.split():
            if word in remove_words:
                continue

            if len(word) > 5:
                suffixes = (
                    "akra",
                    "ekre",
                    "okra",
                    "ekat",
                    "akat",
                    "okat",
                    "eket"
                )

                if word.endswith(suffixes):
                    word = word[:-2]
                elif word.endswith(
                    ("ot", "et", "öt", "at", "ra", "re")
                ):
                    word = word[:-2]

            result.append(word)

        cleaned = " ".join(result).strip()

        return cleaned if cleaned else None

    def get_current_time(self):
        now = datetime.now(
            ZoneInfo("Europe/Budapest")
        )

        return (
            f"Most {now.hour} óra "
            f"{now.minute:02d} perc van."
        )

    def is_time_command(self, text):
        t = self.normalize(text)

        phrases = [
            "mennyi az idő",
            "mennyi idő van",
            "hány óra van",
            "hány óra",
            "mi az idő",
            "pontos idő",
            "mennyi az ido",
            "mennyi ido van",
            "hany ora van",
            "hany ora"
        ]

        if self.contains_any_phrase(t, phrases):
            return True

        return (
            self.contains_similar_word(
                t,
                ["idő", "ido", "óra", "ora"],
                0.84
            )
            and (
                "mennyi" in t
                or "hány" in t
                or "hany" in t
            )
        )

    def is_weather_command(self, text):
        t = self.normalize(text)

        phrases = [
            "milyen idő van",
            "milyen az idő",
            "milyen idő",
            "időjárás",
            "időjárás most",
            "hány fok van",
            "hány fok",
            "esik",
            "esik az eső",
            "fog esni",
            "esni fog",
            "eső lesz",
            "milyen idő lesz",
            "meleg van",
            "hideg van",
            "kell esernyő"
        ]

        if self.contains_any_phrase(t, phrases):
            return True

        return self.contains_similar_word(
            t,
            ["időjárás", "idojaras"],
            0.72
        )

    def is_search_command(self, text):
        t = self.normalize(text)

        phrases = [
            "keress rá",
            "keress ra",
            "keress rá erre",
            "keress ra erre",
            "keresd meg",
            "keresd ki",
            "keress meg",
            "nézz utána",
            "nezz utana",
            "nézz rá",
            "nezz ra",
            "google keresés",
            "google keresésre"
        ]

        if self.contains_any_phrase(t, phrases):
            return True

        return bool(
            set(t.split()) & {
                "keress",
                "keresd",
                "keresés"
            }
        )

    def is_youtube_search_command(self, text):
        t = self.normalize(text)

        youtube_words = {
            "youtube",
            "youtubeon",
            "jutub",
            "jutubon"
        }

        search_words = {
            "keress",
            "keresd",
            "keres",
            "nézz",
            "nezz",
            "kutass"
        }

        words = set(t.split())

        return (
            bool(words & youtube_words)
            and bool(words & search_words)
        ) or self.contains_any_phrase(
            t,
            [
                "youtube keresés",
                "youtubeon keress",
                "youtubeon keresd",
                "keress youtubeon",
                "keress a youtubeon",
                "keresd youtubeon",
                "keresd a youtubeon",
                "nézz youtubeon",
                "nezz youtubeon"
            ]
        )

    def get_youtube_search_query(self, text):
        t = self.fix_speech_errors(text)

        patterns = [
            r"keress(?: rá| ra)?(?: az)?(?: a)? youtubeon (?:erre )?(.*)",
            r"keress(?: rá| ra)?(?: az)?(?: a)? youtube (?:erre )?(.*)",
            r"keresd(?: meg)?(?: az)?(?: a)? youtubeon (?:erre )?(.*)",
            r"keresd(?: meg)?(?: az)?(?: a)? youtube (?:erre )?(.*)",
            r"youtubeon keress(?: rá| ra)?(?: erre)? (.*)",
            r"youtube keresés(?: erre)? (.*)",
            r"youtubeon keresd(?: meg)? (.*)"
        ]

        for pattern in patterns:
            match = re.search(pattern, t)

            if match:
                query = self.clean_search_query(
                    match.group(1).strip()
                )

                if query:
                    return query

        return self.clean_search_query(
            " ".join(
                word
                for word in t.split()
                if word not in {
                    "bon",
                    "bón",
                    "youtube",
                    "youtubeon",
                    "jutub",
                    "jutubon",
                    "keress",
                    "keresd",
                    "keres",
                    "rá",
                    "ra",
                    "a",
                    "az",
                    "on",
                    "nézz",
                    "nezz",
                    "meg",
                    "erre"
                }
            )
        )

    def search_youtube(self, text):
        query = self.get_youtube_search_query(text)

        if not query:
            return "Mit keressek a YouTube-on?"

        search_url = (
            "https://www.youtube.com/results?search_query="
            + quote_plus(query)
        )

        try:
            webbrowser.open(search_url)
            return f"Rákerestem YouTube-on erre: {query}."
        except Exception:
            return "Nem sikerült megnyitnom a YouTube keresést."

    def is_google_search_command(self, text):
        t = self.normalize(text)

        if self.is_youtube_search_command(t):
            return False

        if "google" in t and any(
            word in t
            for word in (
                "keress",
                "keresd",
                "keres",
                "nézz",
                "nezz"
            )
        ):
            return True

        return self.is_search_command(t)

    def get_search_query(self, text):
        t = self.fix_speech_errors(text)

        patterns = [
            r"keress(?: rá| ra)?(?: erre)?(?: az)? (.*)",
            r"keress(?: rá| ra)? (.*)",
            r"keresd meg (?:az )?(.*)",
            r"keresd ki (?:az )?(.*)",
            r"keress meg (?:az )?(.*)",
            r"nézz utána (?:az )?(.*)",
            r"nezz utana (?:az )?(.*)",
            r"nézz rá (?:az )?(.*)",
            r"nezz ra (?:az )?(.*)",
            r"google keresés(?: erre)? (.*)",
            r"google keresésre (.*)"
        ]

        for pattern in patterns:
            match = re.search(pattern, t)

            if match:
                query = self.clean_search_query(
                    match.group(1).strip()
                )

                if query:
                    return query

        return self.clean_search_query(
            " ".join(
                word
                for word in t.split()
                if word not in {
                    "bon",
                    "bón",
                    "google",
                    "keress",
                    "keresd",
                    "keres",
                    "keresés",
                    "rá",
                    "ra",
                    "meg",
                    "ki",
                    "a",
                    "az",
                    "erre",
                    "nézz",
                    "nezz",
                    "utána",
                    "utana",
                    "benne"
                }
            )
        )

    def search_google(self, text):
        query = self.get_search_query(text)

        if not query:
            return "Mit keressek Google-ben?"

        search_url = (
            "https://www.google.com/search?q="
            + quote_plus(query)
        )

        try:
            webbrowser.open(search_url)
            return f"Rákerestem Google-ben erre: {query}."
        except Exception:
            return "Nem sikerült megnyitnom a Google keresést."

    def is_open_command(self, text):
        t = self.normalize(text)

        exact_words = {
            "nyisd",
            "nyit",
            "nyitd",
            "nyiss",
            "indítsd",
            "indíts",
            "megnyit",
            "megnyitás",
            "megnyitása"
        }

        for word in t.split():
            if word in exact_words:
                return True

            if self.similar(word, "nyisd", 0.82):
                return True

            if self.similar(word, "indítsd", 0.80):
                return True

        return False

    def is_folder_command(self, text):
        words = set(
            self.normalize(text).split()
        )

        return bool(
            words & {
                "mappa",
                "mappát",
                "mappak",
                "mappák",
                "könyvtár",
                "könyvtárat",
                "folder"
            }
        )

    def is_file_command(self, text):
        words = set(
            self.normalize(text).split()
        )

        return bool(
            words & {
                "fájl",
                "fájlt",
                "fájlok",
                "fájlokat",
                "dokumentum",
                "dokumentumot",
                "dokumentumok",
                "kép",
                "képet",
                "képek",
                "fotó",
                "fotót",
                "fotók"
            }
        )

    def is_file_search_command(self, text):
        t = self.normalize(text)
        words = set(t.split())

        search_words = {
            "keresd",
            "keress",
            "keres",
            "találd",
            "talald",
            "találdmeg",
            "talaldmeg",
            "kutass",
            "keresés"
        }

        file_words = {
            "fájl",
            "fájlt",
            "fájlok",
            "fájlokat",
            "dokumentum",
            "dokumentumot",
            "dokumentumok",
            "kép",
            "képet",
            "képek",
            "fotó",
            "fotót",
            "fotók"
        }

        if words & file_words:
            return True

        search_phrases = [
            "keresd meg",
            "keress meg",
            "keresd ki",
            "keress ki",
            "találd meg",
            "talald meg",
            "keresd meg a gépen",
            "keress a gépen",
            "keress a gépemen",
            "fájl keresése",
            "dokumentum keresése"
        ]

        return (
            bool(words & search_words)
            and (
                bool(words & file_words)
                or self.contains_any_phrase(
                    t,
                    search_phrases
                )
            )
        )

    def is_window_move_command(self, text):
        t = self.normalize(text)

        move_words = {
            "tedd",
            "rakd",
            "vidd",
            "helyezd",
            "helyeszt",
            "mozgasd"
        }

        words = set(t.split())

        if not words & move_words:
            return False

        side = self.get_window_move_side(t)

        return side is not None

    def get_window_move_target(self, text):
        t = self.normalize(text)

        for name, target in sorted(
            self.window_aliases.items(),
            key=lambda item: len(item[0]),
            reverse=True
        ):
            if name in t:
                return target

        return None

    def get_window_move_side(self, text):
        t = self.normalize(text)

        left_words = {
            "balra",
            "baloldalra",
            "baloldára",
            "baloldara",
            "balodóra",
            "balodora",
            "bal oldalra",
            "bal oldalára",
            "bal oldalara",
            "balúldora"
        }

        right_words = {
            "jobbra",
            "jobboldalra",
            "jobboldára",
            "jobboldara",
            "jobodóra",
            "jobodora",
            "jobb oldalra",
            "jobb oldalára",
            "jobb oldalara"
        }

        if any(word in t for word in left_words):
            return "left"

        if any(word in t for word in right_words):
            return "right"

        return None

    def move_window(self, text, fallback_target=None):
        target = self.get_window_move_target(text)
        side = self.get_window_move_side(text)

        if not target:
            target = fallback_target

        if not side:
            return "Mondd meg, hogy balra vagy jobbra tegyem az ablakot."

        if not target:
            return "Nem tudom, melyik ablakot tegyem át."

        if side == "left":
            return self.system.move_window_left(target)

        return self.system.move_window_right(target)

    def get_app_query(self, text):
        remove_words = {
            "nyisd",
            "nyit",
            "nyitd",
            "nyiss",
            "indítsd",
            "indíts",
            "megnyit",
            "megnyitás",
            "megnyitása",
            "meg",
            "ki",
            "a",
            "az",
            "egy",
            "nekem",
            "kérlek",
            "légy",
            "szíves"
        }

        words = self.normalize(text).split()

        result = []

        for word in words:
            if word in remove_words:
                continue

            if self.similar(word, "nyisd", 0.82):
                continue

            result.append(word)

        return " ".join(result).strip()

    def get_target_word(self, text, targets):
        words = self.normalize(text).split()

        for target in targets:
            if target in words:
                return target

        for word in words:
            for target in targets:
                if self.similar(
                    word,
                    target,
                    0.82
                ):
                    return target

        return None

    def open_application(self, text):
        query = self.get_app_query(text)

        if not query:
            return None

        normalized_query = self.normalize(query)

        for name, alias in sorted(
            self.app_aliases.items(),
            key=lambda item: len(item[0]),
            reverse=True
        ):
            if name in normalized_query:
                app = self.apps.find_app(alias)

                if app:
                    if self.apps.open_app(alias):
                        return f"Megnyitottam a {app['name']}."

                    return (
                        f"Megtaláltam a(z) {app['name']} alkalmazást, "
                        f"de nem sikerült elindítani."
                    )

        if len(query.split()) > 2:
            return None

        app = self.apps.find_app(query)

        if not app:
            return None

        if self.apps.open_app(query):
            return f"Megnyitottam a {app['name']}."

        return (
            f"Megtaláltam a(z) {app['name']} alkalmazást, "
            f"de nem sikerült elindítani."
        )

    def get_folder_query(self, text):
        remove_words = {
            "nyisd",
            "nyit",
            "nyitd",
            "nyiss",
            "indítsd",
            "indíts",
            "megnyit",
            "megnyitás",
            "megnyitása",
            "meg",
            "ki",
            "a",
            "az",
            "egy",
            "nekem",
            "kérlek",
            "légy",
            "szíves",
            "mappa",
            "mappát",
            "mappak",
            "mappák",
            "könyvtár",
            "könyvtárat",
            "folder"
        }

        return " ".join(
            word
            for word in self.normalize(text).split()
            if word not in remove_words
        ).strip()

    def find_folder_directly(self, query, time_budget=2.5):
        query = self.normalize(query)

        if not query:
            return None

        home = Path.home()

        common_paths = [
            home,
            home / "Desktop",
            home / "Downloads",
            home / "Documents",
            home / "Pictures",
            home / "Music",
            home / "Videos",
            home / "AppData" / "Local",
            home / "AppData" / "Roaming"
        ]

        for base in common_paths:
            if not base.exists():
                continue

            try:
                if self.normalize(base.name) == query:
                    return base

                for path in base.iterdir():
                    if (
                        path.is_dir()
                        and self.normalize(path.name) == query
                    ):
                        return path

            except (PermissionError, OSError):
                continue

        # Utolsó, lassabb próbálkozásként végigmegyünk a teljes
        # home mappán, de:
        # - kihagyjuk az AppData-t és más nehéz/irreleváns
        #   mappákat (rengeteg fájl, ritkán keresünk itt hangból)
        # - időkorláttal védekezünk, hogy ez soha ne fusson
        #   sok másodpercig egy nagy mappastruktúránál
        skip_dirs = {
            "appdata",
            "node_modules",
            ".git",
            "__pycache__",
            "venv",
            ".venv",
            "$recycle.bin",
            "system volume information"
        }

        start = time.monotonic()

        try:
            import os

            for root, dirnames, _ in os.walk(home):
                if time.monotonic() - start > time_budget:
                    break

                dirnames[:] = [
                    name
                    for name in dirnames
                    if name.lower() not in skip_dirs
                ]

                for name in dirnames:
                    if self.normalize(name) == query:
                        return Path(root) / name

        except (PermissionError, OSError):
            pass

        return None

    def open_folder(self, text):
        query = self.get_folder_query(text)
        home = Path.home()

        known_folders = {
            "asztal": home / "Desktop",
            "desktop": home / "Desktop",
            "letöltések": home / "Downloads",
            "letoltesek": home / "Downloads",
            "downloads": home / "Downloads",
            "dokumentumok": home / "Documents",
            "documents": home / "Documents",
            "képek": home / "Pictures",
            "kepek": home / "Pictures",
            "pictures": home / "Pictures",
            "zene": home / "Music",
            "zenék": home / "Music",
            "music": home / "Music",
            "videók": home / "Videos",
            "videok": home / "Videos",
            "videos": home / "Videos"
        }

        normalized_query = self.normalize(query)

        if normalized_query in known_folders:
            path = known_folders[normalized_query]

            if path.exists():
                return self.files.open_folder(path)

        if not query:
            return "Meg kell adnod, melyik mappát nyissam meg."

        path = self.find_folder_directly(query)

        if path:
            return self.files.open_folder(path)

        return f"Nem találtam ilyen mappát: {query}."

    def get_file_query(self, text):
        remove_words = {
            "keresd",
            "keress",
            "keres",
            "találd",
            "talald",
            "találdmeg",
            "talaldmeg",
            "meg",
            "ki",
            "rá",
            "ra",
            "a",
            "az",
            "egy",
            "nekem",
            "kérlek",
            "légy",
            "szíves",
            "gépen",
            "gépemen",
            "számítógépen",
            "számítógépemen",
            "fájl",
            "fájlt",
            "fájlok",
            "fájlokat",
            "dokumentum",
            "dokumentumot",
            "dokumentumok",
            "kép",
            "képet",
            "képek",
            "fotó",
            "fotót",
            "fotók",
            "hol",
            "van",
            "mutasd",
            "helyét"
        }

        return " ".join(
            word
            for word in self.normalize(text).split()
            if word not in remove_words
        ).strip()

    def search_files(self, text):
        query = self.get_file_query(text)

        if not query:
            return None

        results = self.files.search(
            query,
            max_results=10
        )

        if not results:
            return (
                f"Nem találtam ilyen fájlt vagy mappát: "
                f"{query}."
            )

        if len(results) == 1:
            path = Path(results[0])
            return f"Találtam egy találatot: {path.name}."

        names = [
            Path(path).name
            for path in results[:5]
        ]

        return (
            f"Találtam {len(results)} találatot: "
            + ", ".join(names)
            + "."
        )

    def open_file_search_result(self, text):
        query = self.get_file_query(text)

        if not query:
            return None

        results = self.files.search(
            query,
            max_results=20
        )

        if not results:
            return f"Nem találtam ilyet: {query}."

        normalized_query = self.normalize(query)

        exact = [
            path
            for path in results
            if self.normalize(Path(path).name)
            == normalized_query
        ]

        if exact:
            return self.files.open_file(exact[0])

        return self.files.open_file(results[0])

    def get_website_query(self, text):
        remove_words = {
            "nyisd",
            "nyit",
            "nyitd",
            "nyiss",
            "indítsd",
            "indíts",
            "megnyit",
            "megnyitás",
            "megnyitása",
            "meg",
            "ki",
            "a",
            "az",
            "egy",
            "nekem",
            "kérlek",
            "légy",
            "szíves",
            "oldalt",
            "oldal",
            "weboldalt",
            "weboldal",
            "honlapot",
            "honlap",
            "weblapot",
            "weblap",
            "webhelyet",
            "webhely"
        }

        return " ".join(
            word
            for word in self.normalize(text).split()
            if word not in remove_words
        ).strip()

    def open_website(self, text):
        lower_text = self.normalize(text)

        domain_pattern = re.search(
            r"(https?://[^\s]+|"
            r"(?:www\.)?[a-zA-Z0-9-]+\."
            r"[a-zA-Z]{2,}(?:/[^\s]*)?)",
            lower_text
        )

        if domain_pattern:
            url = domain_pattern.group(1)

            if not url.startswith("http"):
                url = "https://" + url

            try:
                webbrowser.open(url)
                return f"Megnyitottam: {url}."
            except Exception:
                return "Nem sikerült megnyitnom a megadott linket."

        target = self.get_target_word(
            lower_text,
            list(self.websites.keys())
        )

        if target:
            try:
                webbrowser.open(
                    self.websites[target]
                )
                return f"Megnyitottam a {target} oldalt."
            except Exception:
                return (
                    f"Nem sikerült megnyitnom "
                    f"a {target} oldalt."
                )

        query = self.get_website_query(text)

        if not query:
            return None

        search_url = (
            "https://www.google.com/search?q="
            + quote_plus(query)
        )

        try:
            webbrowser.open(search_url)
            return f"Rákerestem erre: {query}."
        except Exception:
            return "Nem sikerült megnyitnom a keresést."

    def get_window_target(self, text):
        t = self.normalize(text)

        for name, target in sorted(
            self.window_aliases.items(),
            key=lambda item: len(item[0]),
            reverse=True
        ):
            if name in t:
                return target

        return None

    def focus_window(self, target):
        hwnd = self.system._wait_for_window(
            target,
            timeout=3.0,
            interval=0.10
        )

        if not hwnd:
            return None

        try:
            user32 = ctypes.windll.user32
            user32.ShowWindow(hwnd, 9)
            user32.SetForegroundWindow(hwnd)
            return hwnd
        except Exception:
            return None

    def close_target_window(self, text):
        target = self.get_window_target(text)

        if not target:
            return None

        hwnd = self.focus_window(target)

        if not hwnd:
            return f"Nem találtam meg a(z) {target} ablakot."

        time.sleep(0.05)

        return self.system.close_window()

    def minimize_target_window(self, text):
        target = self.get_window_target(text)

        if not target:
            return None

        hwnd = self.focus_window(target)

        if not hwnd:
            return f"Nem találtam meg a(z) {target} ablakot."

        time.sleep(0.05)

        return self.system.minimize_window()

    def maximize_target_window(self, text):
        target = self.get_window_target(text)

        if not target:
            return None

        hwnd = self.focus_window(target)

        if not hwnd:
            return f"Nem találtam meg a(z) {target} ablakot."

        time.sleep(0.05)

        return self.system.maximize_window()

    def switch_to_target_window(self, text):
        target = self.get_window_target(text)

        if not target:
            return None

        hwnd = self.focus_window(target)

        if not hwnd:
            return f"Nem találtam meg a(z) {target} ablakot."

        return f"Átváltottam a(z) {target} ablakra."

    def is_close_window_command(self, text):
        t = self.normalize(text)

        return self.contains_any_phrase(
            t,
            [
                "zárd be",
                "zarad be",
                "zárd le",
                "zarad le",
                "csukd be",
                "csukd le"
            ]
        )

    def is_minimize_command(self, text):
        t = self.normalize(text)

        if self.contains_any_phrase(
            t,
            [
                "minimalizáld",
                "minimalizald",
                "minimalizáld le",
                "minimalizald le",
                "kicsinyítsd le",
                "kicsinyitsd le"
            ]
        ):
            return True

        # A Whisper gyakran elcsúszik ezeken a szavakon
        # (pl. "normalizáld", "minimalizáld"-hoz hasonló
        # torzult alakok), ezért fuzzy egyezést is nézünk.
        return self.contains_similar_word(
            t,
            [
                "minimalizáld",
                "minimalizald",
                "kicsinyítsd",
                "kicsinyitsd"
            ],
            0.78
        )

    def is_maximize_command(self, text):
        t = self.normalize(text)

        if self.contains_any_phrase(
            t,
            [
                "maximalizáld",
                "maximalizald",
                "maximalizáld fel",
                "maximalizald fel",
                "nagyítsd ki",
                "nagyitsd ki"
            ]
        ):
            return True

        return self.contains_similar_word(
            t,
            [
                "maximalizáld",
                "maximalizald",
                "nagyítsd",
                "nagyitsd"
            ],
            0.78
        )

    def is_switch_target_command(self, text):
        t = self.normalize(text)

        return self.contains_any_phrase(
            t,
            [
                "válts a",
                "valts a",
                "válts át a",
                "valts at a",
                "válts erre",
                "valts erre",
                "kapcsold előtérbe",
                "kapcsold eloterbe"
            ]
        )

    def get_volume_value(self, text):
        t = self.normalize(text)

        patterns = [
            r"hangerőt\s+(\d{1,3})",
            r"hangerő\s+(\d{1,3})",
            r"hangero[t]?\s+(\d{1,3})",
            r"(\d{1,3})\s*százalékra",
            r"(\d{1,3})\s*szazalekra",
            r"(\d{1,3})\s*percentre",
            r"(\d{1,3})\s*%",
            r"állítsd\s+(\d{1,3})",
            r"allitsd\s+(\d{1,3})"
        ]

        for pattern in patterns:
            match = re.search(pattern, t)

            if match:
                try:
                    return max(
                        0,
                        min(
                            100,
                            int(match.group(1))
                        )
                    )
                except ValueError:
                    return None

        return None

    def is_volume_set_command(self, text):
        t = self.normalize(text)

        if self.get_volume_value(t) is not None:
            return True

        return (
            ("hangerő" in t or "hangero" in t)
            and any(
                word in t
                for word in (
                    "állítsd",
                    "allitsd",
                    "állíts",
                    "allits"
                )
            )
        )

    def get_brightness_action(self, text):
        t = self.normalize(text)

        if not any(
            word in t
            for word in (
                "fényerő",
                "fenyero"
            )
        ):
            return None

        if any(
            word in t
            for word in (
                "fel",
                "feljebb",
                "növeld",
                "noveld",
                "emeld",
                "világosabb",
                "vilagosabb"
            )
        ):
            return "up"

        if any(
            word in t
            for word in (
                "le",
                "lejjebb",
                "csökkentsd",
                "csokkentsd",
                "vedd le",
                "sötétebb",
                "sotetebb"
            )
        ):
            return "down"

        return None

    def is_spotify_command(self, text):
        t = self.normalize(text)

        return (
			"spotify" in t
			or "spotifáj" in t
		)

    def handle_spotify_command(self, text):
        t = self.fix_speech_errors(text)

        if not self.is_spotify_command(t):
            return None

        if self.contains_any_phrase(
			t,
			[
				"következő",
				"következőt",
				"kövi",
				"kovetkezo"
			]
		):
            return self.spotify.next_track()

        if self.contains_any_phrase(
			t,
			[
				"előző",
				"elozo",
				"előző szám",
				"elozo szam"
			]
		): 
            return self.spotify.previous_track()

        if self.contains_any_phrase(
            t,
            [
                "szünet",
                "szunet",
                "állítsd meg",
                "allitst meg",
                "játszd le",
                "jatszd le"
            ]
        ):
            return self.spotify.play_pause()

        playlist = re.search(
            r"(\d+)\s*(playlist|lejátszási lista|lejatszasi lista)",
            t
        )

        if playlist:
            return self.spotify.open_playlist(
                playlist.group(1)
            )

        if self.contains_any_phrase(
            t,
            [
                "nyisd meg a spotifyt",
                "nyisd meg spotifyt",
                "indítsd el a spotifyt",
                "inditsd el spotifyt",
                "nyisd a spotifyt"
            ]
        ):
            if self.spotify.open_spotify():
                return "Megnyitottam a Spotifyt."

            return "Nem sikerült megnyitnom a Spotifyt."

        return None

    def handle_system_command(self, text):
        t = self.fix_speech_errors(text)

        if self.is_volume_set_command(t):
            value = self.get_volume_value(t)

            if value is None:
                return "Mondd meg, hány százalékra állítsam a hangerőt."

            return self.system.volume_set(value)

        brightness_action = self.get_brightness_action(t)

        if brightness_action == "up":
            return self.system.brightness_up()

        if brightness_action == "down":
            return self.system.brightness_down()

        if self.contains_any_phrase(
            t,
            [
                "hangosítsd fel",
                "hangosíts fel",
                "hangosíts",
                "hangosabb"
            ]
        ):
            return self.system.volume_up()

        if self.contains_any_phrase(
            t,
            [
                "halkítsd le",
                "halkíts le",
                "halkíts",
                "halkabb"
            ]
        ):
            return self.system.volume_down()

        if self.contains_any_phrase(
            t,
            [
                "némítsd el",
                "némítsd le",
                "némíts",
                "némítás"
            ]
        ):
            return self.system.volume_mute()

        if self.is_close_window_command(t):
            target = self.get_window_target(t)

            if target:
                return self.close_target_window(t)

            return self.system.close_window()

        if self.is_minimize_command(t):
            target = self.get_window_target(t)

            if target:
                return self.minimize_target_window(t)

            return self.system.minimize_window()

        if self.is_maximize_command(t):
            target = self.get_window_target(t)

            if target:
                return self.maximize_target_window(t)

            return self.system.maximize_window()

        if (
            "teljes képernyő" in t
            or "teljes képernyős" in t
            or "teljeskepernyo" in t
        ):
            return self.system.full_screen()

        if (
            "válts ablakot" in t
            or "válts ablak" in t
            or "ablakot válts" in t
        ):
            return self.system.switch_window()

        if self.is_switch_target_command(t):
            target = self.get_window_target(t)

            if target:
                return self.switch_to_target_window(t)

            return self.system.switch_window()

        if (
            "mutasd az asztalt" in t
            or "mutasd az asztal" in t
            or "asztal mutasd" in t
        ):
            return self.system.show_desktop()

        if self.contains_similar_word(
            t,
            [
                "feladatkezelő",
                "feladatkezelo"
            ],
            0.80
        ):
            return self.system.open_task_manager()

        return None

    def handle_local_command(self, text):
        t = self.fix_speech_errors(text)
        spotify_result = self.handle_spotify_command(t)

        if spotify_result:
            return spotify_result

        if self.is_youtube_search_command(t):
            return self.search_youtube(t)

        if self.is_file_search_command(t):
            if self.is_open_command(t):
                result = self.open_file_search_result(t)

                if result:
                    return result

            result = self.search_files(t)

            if result:
                return result

        if self.is_google_search_command(t):
            result = self.search_google(t)

            if result:
                return result

        if self.is_window_move_command(t):
            return self.move_window(t)

        if self.is_time_command(t):
            return self.get_current_time()

        if self.is_weather_command(t):
            return self.weather.get_weather_text()

        system_result = self.handle_system_command(t)

        if system_result:
            return system_result

        if self.is_folder_command(t):
            result = self.open_folder(t)

            if result:
                return result

        website_target = self.get_target_word(
            t,
            list(self.websites.keys())
        )

        app_target = self.get_target_word(
            t,
            list(self.app_aliases.keys())
        )

        if website_target:
            if self.is_open_command(t):
                return self.open_website(t)

            if (
                website_target in {
                    "youtube",
                    "google"
                }
                and (
                    "nyisd" in t
                    or "nyitd" in t
                    or "nyiss" in t
                    or "megnyit" in t
                )
            ):
                return self.open_website(t)

        if app_target:
            if self.is_open_command(t):
                return self.open_application(t)

        if self.is_open_command(t):
            app_result = self.open_application(t)

            if app_result:
                return app_result

            website_result = self.open_website(t)

            if website_result:
                return website_result

        return None

    def ask_ai(self, text):
        if not self.ai or not self.ai.available:
            return None

        try:
            result = self.ai.ask(text)

            if result:
                return str(result).strip()

        except Exception:
            return None

        return None

    def handle(self, text):
        if not text:
            return None

        original_text = str(text).strip()

        normalized = self.normalize(original_text)

        if not normalized:
            return None

        if self.is_interrupt_command(normalized):
            self.interrupt_speech()
            return None

        if self.tts:
            self.interrupt_speech()

        commands = self.split_multi_commands(
            normalized
        )

        if not commands:
            return self.ask_ai(original_text)

        results = []
        last_target = None

        for command in commands:
            original_command = command.strip()

            command = self.fix_speech_errors(
                command
            ).strip()

            if not command:
                continue

            current_target = (
                self.get_window_move_target(command)
                or self.get_window_target(command)
            )

            if current_target:
                last_target = current_target

            if self.is_window_move_command(command):
                result = self.move_window(
                    command,
                    fallback_target=last_target
                )

                if result:
                    results.append(result)

                continue

            local_result = self.handle_local_command(
                command
            )

            if local_result:
                results.append(local_result)

                command_target = self.get_target_word(
                    command,
                    [
                        "discord",
                        "minecraft",
                        "spotify",
                        "chrome",
                        "firefox",
                        "edge",
                        "vscode"
                    ]
                )

                if command_target:
                    if command_target == "chrome":
                        last_target = "chrome"
                    else:
                        last_target = command_target

                continue

            ai_result = self.ask_ai(original_command)

            if ai_result:
                results.append(ai_result)

        if not results:
            return self.ask_ai(original_text)

        return " ".join(results)