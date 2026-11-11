import customtkinter as ctk
import datetime


class ChatPanel:
    """
    Jobb oldali "Conversation" panel a referenciakép stílusában:
    fejléc Clear / Extract Conversation gombokkal, görgethető
    buborék-üzenetek (nem sima szövegdoboz), alul beviteli mező
    + küldés gomb.
    """

    def __init__(self, parent, colors, on_send=None):
        self.colors = colors
        self.on_send = on_send

        self.frame = ctk.CTkFrame(
            parent,
            fg_color=colors["panel"],
            corner_radius=18,
            border_width=1,
            border_color=colors["panel_border"],
        )

        self._create_header()
        self._create_messages()
        self._create_input()

    def pack(self, **kwargs):
        self.frame.pack(**kwargs)

    def _create_header(self):
        header = ctk.CTkFrame(self.frame, fg_color="transparent", height=40)
        header.pack(fill="x", padx=16, pady=(14, 6))
        header.pack_propagate(False)

        ctk.CTkLabel(
            header,
            text="Üzenetek",
            font=("Segoe UI", 16, "bold"),
            text_color=self.colors["text"]
        ).pack(side="left")

        button_box = ctk.CTkFrame(header, fg_color="transparent")
        button_box.pack(side="right")

        ctk.CTkButton(
            button_box,
            text="🗑 Törlés",
            width=70,
            height=30,
            corner_radius=13,
            font=("Segoe UI Emoji", 13),
            fg_color=self.colors["inner"],
            hover_color=self.colors["panel_border"],
            text_color=self.colors["subtext"],
            command=self.clear
        ).pack(side="left", padx=3)

        ctk.CTkButton(
            button_box,
            text="⬇ Lementés",
            width=85,
            height=30,
            corner_radius=13,
            font=("Segoe UI Emoji", 13),
            fg_color=self.colors["inner"],
            hover_color=self.colors["panel_border"],
            text_color=self.colors["subtext"],
            command=self.export
        ).pack(side="left", padx=3)

    def _create_messages(self):
        self.scroll = ctk.CTkScrollableFrame(
            self.frame,
            fg_color="transparent"
        )

        self.scroll.pack(fill="both", expand=True, padx=10, pady=6)

        self._messages = []

    def _create_input(self):
        input_box = ctk.CTkFrame(self.frame, fg_color="transparent")
        input_box.pack(fill="x", padx=16, pady=(4, 16))

        self.entry = ctk.CTkEntry(
            input_box,
            placeholder_text="Írj üzenetet...",
            fg_color=self.colors["inner"],
            border_width=1,
            border_color=self.colors["panel_border"],
            corner_radius=14,
            height=45
        )

        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.entry.bind("<Return>", lambda e: self._send())

        ctk.CTkButton(
            input_box,
            text=">>",
            width=38,
            height=45,
            corner_radius=14,
            fg_color=self.colors["accent"],
            text_color=self.colors["bg"],
            hover_color=self.colors["accent"],
            command=self._send
        ).pack(side="right")

    def _send(self):
        text = self.entry.get().strip()

        if not text:
            return

        self.entry.delete(0, "end")
        self.add_message("Te", text)

        if self.on_send:
            self.on_send(text)

    def add_message(self, sender, text):
        is_nova = sender.lower() in ("nova", "jarvis")

        bubble_wrap = ctk.CTkFrame(self.scroll, fg_color="transparent")
        bubble_wrap.pack(
            fill="x",
            anchor="w" if is_nova else "e",
            pady=6
        )

        bubble = ctk.CTkFrame(
            bubble_wrap,
            fg_color=self.colors["inner"] if is_nova else self.colors["accent"],
            corner_radius=14
        )
        bubble.pack(
            anchor="w" if is_nova else "e",
            padx=4
        )

        ctk.CTkLabel(
            bubble,
            text=text,
            font=("Segoe UI", 14),
            text_color=self.colors["text"] if is_nova else self.colors["bg"],
            wraplength=260,
            justify="left"
        ).pack(padx=14, pady=(10, 2), anchor="w")

        self._messages.append(bubble_wrap)

        self.scroll._parent_canvas.yview_moveto(1.0)

    def clear(self):
        for bubble in self._messages:
            bubble.destroy()

        self._messages = []

    def export(self):
        if not self._messages:
            return

        lines = []

        for wrap in self._messages:
            for bubble in wrap.winfo_children():
                labels = [
                    child for child in bubble.winfo_children()
                    if isinstance(child, ctk.CTkLabel)
                ]

                if len(labels) >= 2:
                    lines.append(f"[{labels[1].cget('text')}] {labels[0].cget('text')}")

        if not lines:
            return

        filename = datetime.datetime.now().strftime(
            "nova_beszelgetes_%Y%m%d_%H%M%S.txt"
        )

        try:
            with open(filename, "w", encoding="utf-8") as file:
                file.write("\n".join(lines))

            self.add_message("Nova", f"Elmentve: {filename}")

        except Exception as e:
            print(f"❌ Exportálási hiba: {e}")