import tkinter as tk
import math
import random
from PIL import Image, ImageDraw, ImageFilter, ImageTk, ImageFont


try:
    font = ImageFont.truetype(
        "C:/Windows/Fonts/segoeuib.ttf",
        28
    )
except:
    font = ImageFont.load_default()


class OrbWidget:

    def __init__(self, parent, bg, size=420, accent="#00D9FF"):

        self.size = size
        self.bg = bg
        self.accent = accent

        self.status = "sleeping"
        self.time = 0

        self.stars = []

        for _ in range(90):
            self.stars.append(
                (
                    random.randint(0, size),
                    random.randint(0, size),
                    random.choice([1, 1, 1, 2])
                )
            )

        self.canvas = tk.Canvas(
            parent,
            width=size,
            height=size,
            bg="#030712",
            highlightthickness=0
        )

        self.image_label = self.canvas.create_image(
            size // 2,
            size // 2
        )

        self.cache = []
        self.cache_size = 40

        self._create_cache()

        self._animate()


    def pack(self, **kwargs):
        self.canvas.pack(**kwargs)


    def set_status(self, status):
        self.status = status

    def _create_cache(self):
        for i in range(self.cache_size):

            phase = math.sin(
                (i / self.cache_size) * math.pi * 2
            )

            img = self.create_orb(phase)

            self.cache.append(
                ImageTk.PhotoImage(img)
            )

    def create_orb(self, phase=None, cache_mode=False):

        size = self.size

        if phase is None:
            pulse = math.sin(self.time / 35)
        else:
            pulse = phase

        img = Image.new(
            "RGBA",
            (size, size),
            (3, 7, 18, 255)
        )

        center = size // 2

        draw = ImageDraw.Draw(img)

        for x, y, r in self.stars:
            draw.ellipse(
                (
                    x-r,
                    y-r,
                    x+r,
                    y+r
                ),
                fill=(150, 190, 240, 90)
            )

        outer_radius = 125 + (pulse * 5)
        inner_radius = 92 - (pulse * 2)


        blue_glow = Image.new(
            "RGBA",
            (size, size),
            (0,0,0,0)
        )

        glow_draw = ImageDraw.Draw(blue_glow)

        glow_draw.ellipse(
            (
                center-outer_radius,
                center-outer_radius,
                center+outer_radius,
                center+outer_radius
            ),
            outline=(0,220,255,170),
            width=12
        )

        blue_glow = blue_glow.filter(
            ImageFilter.GaussianBlur(7)
        )

        img.alpha_composite(blue_glow)


        draw = ImageDraw.Draw(img)

        draw.ellipse(
            (
                center-outer_radius,
                center-outer_radius,
                center+outer_radius,
                center+outer_radius
            ),
            outline=(0,220,255,255),
            width=3
        )


        draw.ellipse(
            (
                center-inner_radius,
                center-inner_radius,
                center+inner_radius,
                center+inner_radius
            ),
            outline=(245,250,255,255),
            width=3
        )


        draw.text(
            (
                center,
                center
            ),
            "N.O.V.A",
            fill=(245,250,255,255),
            anchor="mm",
            font=font
        )


        return img



    def _animate(self):
        index = int(
            self.time / 6
        ) % self.cache_size

        self.canvas.itemconfig( 
            self.image_label,
            image=self.cache[index]
        )

        self.time += 1
        self.canvas.after(
            50,
            self._animate
        )