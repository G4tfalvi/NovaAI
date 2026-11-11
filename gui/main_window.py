import datetime
import time

import customtkinter as ctk
import psutil

from gui.state import NovaState
from gui.bridge import GuiBridge
from gui.orb_widget import OrbWidget
from gui.chat_panel import ChatPanel

try:
    from pynvml import (
        nvmlInit,
        nvmlDeviceGetHandleByIndex,
        nvmlDeviceGetUtilizationRates,
    )
    nvmlInit()
    GPU_AVAILABLE = True
except Exception:
    GPU_AVAILABLE = False


class NovaMainWindow:
    """
    Teljes képernyős Nova vezérlőpult, a referenciakép (J.A.R.V.I.S
    stílusú dashboard) alapján felépítve: keret nélküli kártyák
    vékony szegéllyel, mini statisztika-dobozok, progress barok,
    monospace technikai betűtípus a címeknél/számoknál.
    """

    def __init__(self, state: NovaState = None, bridge: GuiBridge = None, on_send=None):
        self.state = state or NovaState()
        self.bridge = bridge or GuiBridge()
        self.on_send = on_send

        self.start_time = time.time()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.root = ctk.CTk()
        self.root.overrideredirect(True)
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        taskbar_space = 40
        self.root.geometry(
            f"{screen_width}x{screen_height - taskbar_space}+0+0"
        )
        self.root.bind("<Escape>", lambda e: self.root.destroy())

        # --- Jeges színpaletta ---
        self.bg = "#0B1118"
        self.panel = "#182535"
        self.panel_border = "#5B7894"
        self.inner = "#22364A"
        self.text = "#EAF6FF"
        self.subtext = "#9FB6C9"
        self.accent = "#8EDBFF"
        self.online = "#A8FFE6"
        self.warning = "#D9EEFF"

        # --- Betűtípusok ---
        self.font_title = ("Consolas", 22, "bold")
        self.font_card_title = ("Segoe UI Emoji", 15, "bold")
        self.font_label = ("Segoe UI Emoji", 15)
        self.font_value = ("Consolas", 14, "bold")
        self.font_big_value = ("Consolas", 26, "bold")

        self.colors = {
            "bg": self.bg,
            "panel": self.panel,
            "panel_border": self.panel_border,
            "inner": self.inner,
            "text": self.text,
            "subtext": self.subtext,
            "accent": self.accent,
            "font_label": self.font_label,
            "font_value": self.font_value,
            "header": "#1B6FA8"
        }

        self.root.configure(fg_color=self.bg)

        self._create_layout()

        self._update_info()
        self._poll_bridge()

    # ------------------------------------------------------------
    # ÁLTALÁNOS ÉPÍTŐELEMEK
    # ------------------------------------------------------------

    def _create_card(self, parent, height=260):
        card = ctk.CTkFrame(
            parent,
            fg_color=self.panel,
            corner_radius=18,
            height=height,
            border_width=1,
            border_color=self.panel_border
        )

        if height:
            card.pack_propagate(False)

        return card

    def _create_card_header(self, parent, icon, text, on_refresh=None):
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(14, 6))

        left = ctk.CTkLabel(
            header,
            text=f"{icon}  {text}",
            font=self.font_card_title,
            text_color=self.text,
            anchor="w"
        )
        left.pack(side="left")

        if on_refresh:
            refresh = ctk.CTkLabel(
                header,
                text="⟳",
                font=("Segoe UI Emoji", 15),
                text_color=self.subtext,
                cursor="hand2"
            )
            refresh.pack(side="right")
            refresh.bind("<Button-1>", lambda e: on_refresh())

    def _mini_stat_box(self, parent, label, value):
        box = ctk.CTkFrame(
            parent,
            fg_color=self.inner,
            corner_radius=12,
            border_width=1,
            border_color=self.panel_border,
            height=65
        )
        box.pack_propagate(False)

        ctk.CTkLabel(
            box,
            text=label,
            font=self.font_label,
            text_color=self.subtext
        ).pack(pady=(10, 2))

        value_label = ctk.CTkLabel(
            box,
            text=value,
            font=self.font_value,
            text_color=self.text
        )
        value_label.pack(pady=(0, 10))

        return box, value_label

    def _progress_row(self, parent, label, value_text):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=(4, 0))

        top = ctk.CTkFrame(row, fg_color="transparent")
        top.pack(fill="x")

        ctk.CTkLabel(
            top,
            text=label,
            font=self.font_label,
            text_color=self.subtext
        ).pack(side="left")

        value_label = ctk.CTkLabel(
            top,
            text=value_text,
            font=self.font_label,
            text_color=self.text
        )
        value_label.pack(side="right")

        bar = ctk.CTkProgressBar(
            row,
            height=6,
            corner_radius=3,
            fg_color=self.inner,
            progress_color=self.accent
        )
        bar.pack(fill="x", pady=(4, 8))
        bar.set(0)

        return bar, value_label

    # ------------------------------------------------------------
    # LAYOUT
    # ------------------------------------------------------------

    def _create_layout(self):
        self._create_top_bar()

        self.main = ctk.CTkFrame(self.root, fg_color=self.bg)
        self.main.pack(fill="both", expand=True, padx=28, pady=(0, 15))

        self.main.grid_columnconfigure(0, weight=1)
        self.main.grid_columnconfigure(1, weight=2)
        self.main.grid_columnconfigure(2, weight=1)
        self.main.grid_rowconfigure(0, weight=1)

        self._create_left_column()
        self._create_center_column()
        self._create_right_column()

    def _create_top_bar(self):
        bar = ctk.CTkFrame(self.root, fg_color=self.bg, height=50)
        bar.pack(fill="x", padx=28, pady=(0, 10))
        bar.pack_propagate(False)

        left = ctk.CTkFrame(bar, fg_color="transparent")
        left.pack(side="left", fill="y")

        ctk.CTkLabel(
            left,
            text="N.O.V.A",
            font=self.font_title,
            text_color=self.text
        ).pack(side="left")

        status_box = ctk.CTkFrame(
            left,
            fg_color=self.panel,
            corner_radius=14,
            border_width=1,
            border_color=self.panel_border,
            width=130,
            height=30
        )
        status_box.pack(side="left", padx=14)
        status_box.pack_propagate(False)

        self.online_dot = ctk.CTkLabel(
            status_box,
            text="●  Elérhető",
            font=("Segoe UI Emoji", 14),
            text_color=self.online,
        )
        self.online_dot.pack(padx=12, pady=2)

        # közép: óra + dátum, dobozban
        clock_box = ctk.CTkFrame(
            bar,
            fg_color=self.panel,
            corner_radius=14,
            border_width=1,
            border_color=self.panel_border,
            height=32
        )
        clock_box.place(relx=0.488, rely=0.5, anchor="center")

        self.clock_label = ctk.CTkLabel(
            clock_box,
            text="",
            font=("Segoe UI Emoji", 15),
            text_color=self.text
        )
        self.clock_label.pack(padx=20, pady=4)

        # jobb: időjárás
        right = ctk.CTkFrame(bar, fg_color="transparent")
        right.pack(side="right", fill="y")

        weather_box = ctk.CTkFrame(
            right,
            fg_color=self.panel,
            corner_radius=14,
            border_width=1,
            border_color=self.panel_border,
            height=32
        )
        weather_box.pack(side="right")
        weather_box.pack_propagate(False)

        self.topbar_weather = ctk.CTkLabel(
            weather_box,
            text="☁️  --°C  |  Pest, Érd",
            font=("Segoe UI Emoji", 16),
            text_color=self.text
        )
        self.topbar_weather.pack(padx=14, pady=4)

    def _create_left_column(self):
        left = ctk.CTkFrame(self.main, fg_color=self.bg)
        left.grid(row=0, column=0, sticky="nsew", padx=10)

        # --- System Stats ---
        system_box = self._create_card(left)
        system_box.pack(fill="x", pady=7)
        self._create_card_header(system_box, "🖥", "Rendszer infó")

        self.cpu_bar, self.cpu_value_label = self._progress_row(
            system_box, "CPU Használat", "0%"
        )
        self.ram_bar, self.ram_value_label = self._progress_row(
            system_box, "RAM Használat", "0 GB"
        )

        mini_row = ctk.CTkFrame(system_box, fg_color="transparent")
        mini_row.pack(fill="x", padx=16, pady=(6, 16))
        mini_row.grid_columnconfigure((0, 1, 2), weight=1)

        cpu_box, self.cpu_mini_value = self._mini_stat_box(mini_row, "CPU", "0%")
        cpu_box.grid(row=0, column=0, sticky="nsew", padx=3)

        mem_box, self.mem_mini_value = self._mini_stat_box(mini_row, "Memória", "0%")
        mem_box.grid(row=0, column=1, sticky="nsew", padx=3)

        disk_box, self.disk_mini_value = self._mini_stat_box(mini_row, "Lemez C:", "-- GB")
        disk_box.grid(row=0, column=2, sticky="nsew", padx=3)

        # --- Weather ---
        weather_box = self._create_card(left)
        weather_box.pack(fill="x", pady=7)
        self._create_card_header(weather_box, "☁", "Időjárás")

        weather_top = ctk.CTkFrame(weather_box, fg_color="transparent")
        weather_top.pack(fill="x", padx=16, pady=(0, 10))

        weather_left = ctk.CTkFrame(weather_top, fg_color="transparent")
        weather_left.pack(side="left")

        self.weather_temp_label = ctk.CTkLabel(
            weather_left,
            text="--°C",
            font=self.font_big_value,
            text_color=self.text,
            anchor="w"
        )
        self.weather_temp_label.pack(anchor="w")

        self.weather_location_label = ctk.CTkLabel(
            weather_left,
            text="Nincs adat",
            font=self.font_label,
            text_color=self.subtext,
            anchor="w"
        )
        self.weather_location_label.pack(anchor="w")

        self.weather_desc_label = ctk.CTkLabel(
            weather_left,
            text="",
            font=self.font_label,
            text_color=self.subtext,
            anchor="w"
        )
        self.weather_desc_label.pack(anchor="w")

        ctk.CTkLabel(
            weather_top,
            text="☁",
            font=("Segoe UI Emoji", 32),
            text_color=self.accent
        ).pack(side="right")

        weather_mini_row = ctk.CTkFrame(weather_box, fg_color="transparent")
        weather_mini_row.pack(fill="x", padx=16, pady=(0, 16))
        weather_mini_row.grid_columnconfigure((0, 1, 2), weight=1)

        hum_box, self.humidity_value = self._mini_stat_box(weather_mini_row, "Páratartalom", "--%")
        hum_box.grid(row=0, column=0, sticky="nsew", padx=3)

        wind_box, self.wind_value = self._mini_stat_box(weather_mini_row, "Szél", "-- km/h")
        wind_box.grid(row=0, column=1, sticky="nsew", padx=3)

        feels_box, self.feels_value = self._mini_stat_box(weather_mini_row, "Érezhető", "--°C")
        feels_box.grid(row=0, column=2, sticky="nsew", padx=3)

        # --- Uptime ---
        uptime_box = self._create_card(left, height=140)
        uptime_box.pack(fill="x", pady=7)
        self._create_card_header(uptime_box, "🕐", "Rendszer Üzemidő")

        running_row = ctk.CTkFrame(uptime_box, fg_color="transparent")
        running_row.pack(fill="x", padx=16, pady=(0, 0))

        ctk.CTkLabel(
            running_row,
            text="Rendszer:",
            font=self.font_label,
            text_color=self.subtext
        ).pack(side="left")

        self.system_uptime_label = ctk.CTkLabel(
            running_row,
            text="0d 00:00:00",
            font=self.font_value,
            text_color=self.text
        )
        self.system_uptime_label.pack(side="right")

        nova_row = ctk.CTkFrame(uptime_box, fg_color="transparent")
        nova_row.pack(fill="x", padx=16, pady=(0, 0))

        ctk.CTkLabel(
            nova_row,
            text="Nova:",
            font=self.font_label,
            text_color=self.subtext
        ).pack(side="left")

        self.nova_uptime_label = ctk.CTkLabel(
            nova_row,
            text="00:00:00",
            font=self.font_value,
            text_color=self.text
        )
        self.nova_uptime_label.pack(side="right")

        uptime_mini_row = ctk.CTkFrame(uptime_box, fg_color="transparent")
        uptime_mini_row.pack(fill="x", padx=16, pady=(0, 10))
        uptime_mini_row.grid_columnconfigure((0, 1), weight=1)

        load_row = ctk.CTkFrame(uptime_box, fg_color="transparent")
        load_row.pack(fill="x", padx=16, pady=(4, 16))

        load_top = ctk.CTkFrame(load_row, fg_color="transparent")
        load_top.pack(fill="x")

        self.load_label = ctk.CTkLabel(
            load_top,
            text="Rendszer betöltés",
            font=self.font_label,
            text_color=self.subtext
        )
        self.load_label.pack(side="left")

        self.load_state_label = ctk.CTkLabel(
            load_top,
            text="Moderate",
            font=("Segoe UI", 11, "bold"),
            text_color=self.warning
        )
        self.load_state_label.pack(side="left", padx=8)

        self.load_percent_label = ctk.CTkLabel(
            load_top,
            text="0%",
            font=self.font_label,
            text_color=self.text
        )
        self.load_percent_label.pack(side="right")

        self.load_bar = ctk.CTkProgressBar(
            load_row,
            height=6,
            corner_radius=3,
            fg_color=self.inner,
            progress_color=self.warning
        )
        self.load_bar.pack(fill="x", pady=(4, 0))
        self.load_bar.set(0)

    def _create_center_column(self):
        center = ctk.CTkFrame(self.main, fg_color=self.bg)
        center.grid(row=0, column=1, sticky="nsew", padx=20)

        spacer = ctk.CTkFrame(center, fg_color=self.bg, height=40)
        spacer.pack()

        self.orb = OrbWidget(center, bg=self.bg, size=420, accent=self.accent)
        self.orb.pack(pady=10)

        ctk.CTkLabel(
            center,
            text="",
            font=("Segoe UI", 30, "bold"),
            text_color=self.text
        ).pack(pady=(10, 0))

        self.status_pill = ctk.CTkLabel(
            center,
            text="●  Alszik",
            font=("Segoe UI Emoji", 15),
            text_color=self.online,
            fg_color=self.panel,
            corner_radius=14,
            width=160,
            height=32
        )
        self.status_pill.pack(pady=15)

    def _create_right_column(self):
        right = ctk.CTkFrame(self.main, fg_color=self.bg)
        right.grid(row=0, column=2, sticky="nsew", padx=10)

        self.chat_panel = ChatPanel(
            right,
            self.colors,
            on_send=self._handle_text_input
        )
        self.chat_panel.pack(fill="both", expand=True, pady=(7, 15))

    def _icon_button(self, parent, symbol, command, active=False):
        button = ctk.CTkButton(
            parent,
            text=symbol,
            width=52,
            height=52,
            corner_radius=26,
            font=("Segoe UI", 18),
            fg_color=self.accent if active else self.panel,
            text_color=self.bg if active else self.text,
            hover_color=self.accent,
            border_width=1,
            border_color=self.panel_border,
            command=command
        )
        button.pack(side="left", padx=10)
        return button

    # ------------------------------------------------------------
    # ESEMÉNYEK / INTERAKCIÓ
    # ------------------------------------------------------------

    def _focus_chat_input(self):
        self.chat_panel.entry.focus_set()

    def _handle_text_input(self, text):
        if self.on_send:
            self.on_send(text)

    # ------------------------------------------------------------
    # ÁLLAPOTFRISSÍTÉS (bridge-en keresztül, biztonságosan)
    # ------------------------------------------------------------

    def _poll_bridge(self):
        for event_type, payload in self.bridge.poll():
            self._handle_event(event_type, payload)

        self.root.after(100, self._poll_bridge)

    def _handle_event(self, event_type, payload):
        if event_type == "status":
            self._set_status(payload)
        elif event_type == "user_message":
            self.chat_panel.add_message("Te", payload)
        elif event_type == "nova_message":
            self.chat_panel.add_message("Nova", payload)
        elif event_type == "weather":
            self._apply_weather(payload)

    def _set_status(self, status):
        self.orb.set_status(status)

        pill_colors = {
            "sleeping": self.online,
            "listening": self.accent,
            "thinking": self.warning,
            "speaking": self.accent,
        }

        pill_texts = {
            "sleeping": "●  Alszik",
            "listening": "●  Hallgatlak...",
            "thinking": "●  Gondolkodom...",
            "speaking": "●  Beszélek...",
        }

        self.status_pill.configure(
            text=pill_texts.get(status, "●  Alszik"),
            text_color=pill_colors.get(status, self.online)
        )

    def _apply_weather(self, payload):
        if not payload:
            return

        temperature = payload.get("temperature")
        description = payload.get("description")
        humidity = payload.get("humidity")
        wind = payload.get("wind")
        feels_like = payload.get("feels_like")
        location = payload.get("location", self.state.location)

        if temperature is not None:
            self.topbar_weather.configure(text=f"☁  {temperature}°C  |  {location}")
            self.weather_temp_label.configure(text=f"{temperature}°C")

        self.weather_location_label.configure(text=location)
        self.weather_desc_label.configure(text=description or "")

        if humidity is not None:
            self.humidity_value.configure(text=f"{humidity}%")

        if wind is not None:
            self.wind_value.configure(text=f"{wind} km/h")

        if feels_like is not None:
            self.feels_value.configure(text=f"{feels_like}°C")

    # ------------------------------------------------------------
    # IDŐZÍTETT FRISSÍTÉSEK (CPU/RAM, óra, uptime)
    # ------------------------------------------------------------

    def _gpu_usage(self):
        if not GPU_AVAILABLE:
            return "N/A"

        try:
            gpu = nvmlDeviceGetUtilizationRates(nvmlDeviceGetHandleByIndex(0))
            return f"{gpu.gpu}%"
        except Exception:
            return "N/A"

    def _update_info(self):
        cpu = psutil.cpu_percent()
        ram_percent = psutil.virtual_memory().percent
        ram_used_gb = psutil.virtual_memory().used / (1024 ** 3)
        disk = psutil.disk_usage("/")

        self.state.update_system_info(cpu=cpu, ram=ram_percent)

        self.cpu_bar.set(cpu / 100)
        self.cpu_value_label.configure(text=f"{cpu:.0f}%")
        self.cpu_mini_value.configure(text=f"{cpu:.0f}%")

        self.ram_bar.set(ram_percent / 100)
        self.ram_value_label.configure(text=f"{ram_used_gb:.0f} GB")
        self.mem_mini_value.configure(text=f"{ram_percent:.0f}%")

        disk_used_gb = disk.used / (1024 ** 3)
        disk_total_gb = disk.total / (1024 ** 3)
        self.disk_mini_value.configure(
            text=f"{disk_used_gb:.0f}/{disk_total_gb:.0f} GB"
        )

        system_load = int((cpu + ram_percent) / 2)
        self.load_bar.set(system_load / 100)
        self.load_percent_label.configure(text=f"{system_load}%")

        if system_load < 35:
            load_state, load_color = "Low", self.online
        elif system_load < 70:
            load_state, load_color = "Moderate", self.warning
        else:
            load_state, load_color = "High", "#FF6B6B"

        self.load_state_label.configure(text=load_state, text_color=load_color)
        self.load_bar.configure(progress_color=load_color)

        uptime = int(time.time() - psutil.boot_time())
        days, remainder = divmod(uptime, 86400)
        h, remainder = divmod(remainder, 3600)
        m, s = divmod(remainder, 60)

        self.system_uptime_label.configure(
            text=f"{days}d {h:02}:{m:02}:{s:02}"
        )

        nova_uptime = int(time.time() - self.start_time)

        nh, remainder = divmod(nova_uptime, 3600)
        nm, ns = divmod(remainder, 60)

        self.nova_uptime_label.configure(
            text=f"{nh:02}:{nm:02}:{ns:02}"
        )

        now = datetime.datetime.now()
        self.clock_label.configure(
            text=now.strftime("%H:%M:%S  |  %Y.%m.%d")
        )

        self.root.after(1000, self._update_info)

    # ------------------------------------------------------------

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    window = NovaMainWindow()
    window.run()