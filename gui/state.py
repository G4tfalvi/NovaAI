import threading


class NovaState:
    """
    Nova asszisztens aktuális állapotát tárolja.

    Fontos: ezt az objektumot a háttérszál (hangfelismerés, AI, TTS)
    ÍRJA, a GUI szál (Tkinter) pedig OLVASSA. A lock ezt védi, de
    a tényleges GUI-frissítést mindig a GuiBridge queue-n keresztül
    kell végezni, nem közvetlenül innen (lásd bridge.py).
    """

    def __init__(self):
        self._lock = threading.Lock()

        # sleeping | listening | thinking | speaking
        self.status = "sleeping"

        self.last_command = ""
        self.last_response = ""

        self.session_count = 1
        self.command_count = 0

        self.cpu_usage = 0
        self.ram_usage = 0
        self.disk_used_gb = 0
        self.disk_total_gb = 0

        self.temperature = None
        self.weather_description = None
        self.humidity = None
        self.wind = None
        self.feels_like = None
        self.location = "Érd"

        self.camera_active = False

    def set_status(self, status):
        with self._lock:
            self.status = status

    def update_command(self, command):
        with self._lock:
            self.last_command = command
            self.command_count += 1

    def update_response(self, response):
        with self._lock:
            self.last_response = response

    def update_system_info(
        self,
        cpu=None,
        ram=None,
        disk_used=None,
        disk_total=None
    ):
        with self._lock:
            if cpu is not None:
                self.cpu_usage = cpu

            if ram is not None:
                self.ram_usage = ram

            if disk_used is not None:
                self.disk_used_gb = disk_used

            if disk_total is not None:
                self.disk_total_gb = disk_total

    def update_weather(
        self,
        temperature=None,
        description=None,
        humidity=None,
        wind=None,
        feels_like=None
    ):
        with self._lock:
            if temperature is not None:
                self.temperature = temperature

            if description is not None:
                self.weather_description = description

            if humidity is not None:
                self.humidity = humidity

            if wind is not None:
                self.wind = wind

            if feels_like is not None:
                self.feels_like = feels_like

    def snapshot(self):
        """Biztonságos, lezárt másolat a jelenlegi állapotról."""
        with self._lock:
            return {
                key: value
                for key, value in self.__dict__.items()
                if not key.startswith("_")
            }