import asyncio
import os
import tempfile
import uuid
import threading

import edge_tts
import pygame
import numpy as np
import sounddevice as sd


class TextToSpeech:

    def __init__(self):
        self.voice = "hu-HU-TamasNeural"
        self.rate = "+20%"
        self.volume = "+0%"
        self.pitch = "-10Hz"

        self.interrupted = False
        self._speaking = False
        self._interrupt_event = None
        self._interrupt_thread = None

        pygame.mixer.init()

    async def _generate(self, text, filename):

        communicate = edge_tts.Communicate(
            text=text,
            voice=self.voice,
            rate=self.rate,
            volume=self.volume,
            pitch=self.pitch
        )

        await communicate.save(filename)

    def _calculate_rms(self, audio):
        return float(
            np.sqrt(
                np.mean(
                    audio * audio
                )
            )
        )

    def _listen_for_interrupt(self, event):

        sample_rate = 16000
        block_duration = 0.04
        block_size = int(
            sample_rate * block_duration
        )

        calibration_time = 0.4
        calibration_blocks = int(
            calibration_time / block_duration
        )

        try:

            with sd.InputStream(
                samplerate=sample_rate,
                channels=1,
                dtype="float32",
                blocksize=block_size
            ) as stream:

                levels = []

                for _ in range(calibration_blocks):

                    if event.is_set():
                        return

                    audio, _ = stream.read(
                        block_size
                    )

                    audio = audio[:, 0].copy()

                    rms = self._calculate_rms(
                        audio
                    )

                    levels.append(rms)

                if not levels:
                    return

                noise_floor = float(
                    np.median(levels)
                )

                noise_max = float(
                    np.percentile(
                        levels,
                        90
                    )
                )

                threshold = max(
                    noise_floor * 2.5,
                    noise_max * 1.8,
                    0.008
                )

                speech_blocks = 0

                while not event.is_set():

                    audio, _ = stream.read(
                        block_size
                    )

                    audio = audio[:, 0].copy()

                    rms = self._calculate_rms(
                        audio
                    )

                    if rms >= threshold:

                        speech_blocks += 1

                    else:

                        speech_blocks = max(
                            0,
                            speech_blocks - 1
                        )

                    if speech_blocks >= 2:

                        self.interrupted = True
                        event.set()

                        try:
                            pygame.mixer.music.stop()
                        except Exception:
                            pass

                        return

        except Exception:
            return

    def speak(self, text):

        self.interrupted = False

        if not text:
            return False

        text = str(text).strip()

        if not text:
            return False

        filename = os.path.join(
            tempfile.gettempdir(),
            f"nova_tts_{uuid.uuid4().hex}.mp3"
        )

        interrupt_event = threading.Event()

        self._interrupt_event = interrupt_event
        self._interrupt_thread = None
        self._speaking = False

        try:

            asyncio.run(
                self._generate(
                    text,
                    filename
                )
            )

            if interrupt_event.is_set():
                return False

            pygame.mixer.music.load(
                filename
            )

            pygame.mixer.music.play()

            self._speaking = True

            self._interrupt_thread = threading.Thread(
                target=self._listen_for_interrupt,
                args=(interrupt_event,),
                daemon=True
            )

            self._interrupt_thread.start()

            clock = pygame.time.Clock()

            while pygame.mixer.music.get_busy():

                if interrupt_event.is_set():
                    try:
                        pygame.mixer.music.stop()
                    except Exception:
                        pass

                    break

                clock.tick(40)

        except Exception as e:

            print(
                f"❌ TTS hiba: {e}"
            )

        finally:

            self._speaking = False

            interrupt_event.set()

            if self._interrupt_thread:
                self._interrupt_thread.join(
                    timeout=0.3
                )

            try:
                pygame.mixer.music.stop()
            except Exception:
                pass

            try:
                pygame.mixer.music.unload()
            except Exception:
                pass

            try:
                if os.path.exists(filename):
                    os.remove(filename)
            except Exception:
                pass

            self._interrupt_event = None
            self._interrupt_thread = None

        return self.interrupted

    def was_interrupted(self):
        return self.interrupted

    def is_speaking(self):
        return self._speaking

    def say(self, text):
        return self.speak(text)