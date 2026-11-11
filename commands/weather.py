import requests


class WeatherController:

    # Érd, Magyarország
    LATITUDE = 47.3949
    LONGITUDE = 18.9136

    def __init__(self):

        self.url = (
            "https://api.open-meteo.com/v1/forecast"
        )
        
    def get_weather(self):

        params = {
            "latitude": self.LATITUDE,
            "longitude": self.LONGITUDE,

            "current": (
                "temperature_2m,"
                "apparent_temperature,"
                "relative_humidity_2m,"
                "precipitation,"
                "weather_code,"
                "wind_speed_10m"
            ),

            "daily": (
                "temperature_2m_max,"
                "temperature_2m_min,"
                "precipitation_probability_max,"
                "weather_code"
            ),

            "timezone": "Europe/Budapest",

            "forecast_days": 3,

            "temperature_unit": "celsius",

            "wind_speed_unit": "kmh",
        }

        try:

            response = requests.get(
                self.url,
                params=params,
                timeout=5
            )

            response.raise_for_status()

            data = response.json()

            current = data["current"]

            temperature = current[
                "temperature_2m"
            ]

            feels_like = current[
                "apparent_temperature"
            ]

            humidity = current[
                "relative_humidity_2m"
            ]

            precipitation = current[
                "precipitation"
            ]

            weather_code = current[
                "weather_code"
            ]

            wind = current[
                "wind_speed_10m"
            ]

            description = self.weather_code_to_text(
                weather_code
            )

            return {
                "location": "Érd",
                "temperature": temperature,
                "feels_like": feels_like,
                "humidity": humidity,
                "precipitation": precipitation,
                "wind": wind,
                "description": description,
            }

        except Exception as e:

            print(
                f"❌ Időjárás hiba: {e}"
            )

            return None

    # =========================================================
    # IDŐJÁRÁS LEÍRÁSA
    # =========================================================

    def weather_code_to_text(self, code):

        codes = {

            0: "derült",

            1: "többnyire derült",
            2: "részben felhős",
            3: "borult",

            45: "ködös",
            48: "zúzmarás köd",

            51: "enyhe szitálás",
            53: "szitálás",
            55: "erős szitálás",

            56: "enyhe ónos szitálás",
            57: "erős ónos szitálás",

            61: "enyhe eső",
            63: "eső",
            65: "erős eső",

            66: "enyhe ónos eső",
            67: "erős ónos eső",

            71: "enyhe havazás",
            73: "havazás",
            75: "erős havazás",

            77: "hódara",

            80: "enyhe zápor",
            81: "zápor",
            82: "erős zápor",

            85: "enyhe hózápor",
            86: "erős hózápor",

            95: "zivatar",

            96: "zivatar jégesővel",
            99: "erős zivatar jégesővel",
        }

        return codes.get(
            code,
            "ismeretlen időjárás"
        )

    # =========================================================
    # NOVA SZÁMÁRA SZÖVEGES VÁLASZ
    # =========================================================

    def get_weather_text(self):

        weather = self.get_weather()

        if not weather:

            return (
                "Most nem tudtam lekérni "
                "az időjárási adatokat."
            )

        return (
            f"Érden jelenleg "
            f"{weather['temperature']} fok van, "
            f"{weather['description']}. "
            f"A hőérzet {weather['feels_like']} fok. "
            f"A páratartalom "
            f"{weather['humidity']} százalék, "
            f"a szél pedig "
            f"{weather['wind']} kilométer per óra."
        )