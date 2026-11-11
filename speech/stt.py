import time
from collections import deque

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel


class SpeechToText:

    def __init__(
        self,
        model_name="medium",
        language="hu"
    ):
        print(
            f"STT modell betöltése: {model_name}"
        )

        self.model = WhisperModel(
            model_name,
            device="cpu",
            compute_type="int8"
        )

        self.language = language

        self.initial_prompt = (
            "Magyar nyelvű beszéd. "
            "Számítógépes hangvezérlés. "
            "Gyakori parancsok: nyisd meg, "
            "indítsd el, zárd be, tedd balra, "
            "tedd jobbra, helyezd balra, "
            "helyezd jobbra, válts ablakot, "
            "minimalizáld, maximalizáld, "
            "hangosítsd fel, halkítsd le, "
            "némítsd el. "
            "Gyakori alkalmazások: Spotify, "
            "Discord, Chrome, YouTube, Minecraft."
        )

        self.minimum_audio_seconds = 0.25
        self.minimum_speech_seconds = 0.15
        self.minimum_rms = 0.0007
        self.minimum_peak = 0.010

    def _calculate_rms(self, audio):
        if audio is None or len(audio) == 0:
            return 0.0

        return float(
            np.sqrt(
                np.mean(
                    audio * audio
                )
            )
        )

    def _calculate_peak(self, audio):
        if audio is None or len(audio) == 0:
            return 0.0

        return float(
            np.max(
                np.abs(audio)
            )
        )

    def _is_hallucination(self, text):
        if not text:
            return True

        normalized = " ".join(
            text.lower().strip().split()
        )

        if not normalized:
            return True

        suspicious_phrases = {
            "milyen idő",
            "milyen idő milyen idő",
            "mennyi az idő",
            "mennyi az idő mennyi az idő",
            "hogy vagy",
            "hogy vagy hogy vagy",
            "jó",
            "jó jó",
            "halló",
            "halló halló",
            "igen",
            "igen igen",
            "köszönöm",
            "köszönöm köszönöm"
        }

        if normalized in suspicious_phrases:
            return True

        words = normalized.split()

        if len(words) >= 2:
            half = len(words) // 2

            if (
                len(words) % 2 == 0
                and words[:half] == words[half:]
            ):
                return True

        return False

    def listen_and_transcribe(
        self,
        max_seconds=15,
        silence_seconds=0.9,
        sample_rate=16000
    ):
        print()
        print("Hallgatlak...")

        block_duration = 0.05
        block_size = int(
            sample_rate * block_duration
        )

        calibration_seconds = 0.7

        calibration_blocks = int(
            calibration_seconds
            / block_duration
        )

        calibration = []

        try:
            with sd.InputStream(
                samplerate=sample_rate,
                channels=1,
                dtype="float32",
                blocksize=block_size
            ) as stream:

                for _ in range(calibration_blocks):
                    audio, _ = stream.read(
                        block_size
                    )

                    audio = audio[:, 0].copy()

                    rms = self._calculate_rms(
                        audio
                    )

                    calibration.append(rms)

                if not calibration:
                    return ""

                noise_floor = float(
                    np.median(calibration)
                )

                noise_max = float(
                    np.percentile(
                        calibration,
                        90
                    )
                )

                start_threshold = max(
                    noise_floor * 2.2,
                    noise_max * 1.45,
                    0.00065
                )

                end_threshold = max(
                    noise_floor * 1.20,
                    noise_max * 1.08,
                    0.00020
                )

                pre_buffer_seconds = 0.50

                pre_buffer_blocks = max(
                    1,
                    int(
                        pre_buffer_seconds
                        / block_duration
                    )
                )

                pre_buffer = deque(
                    maxlen=pre_buffer_blocks
                )

                chunks = []

                started = False
                speech_blocks = 0
                silent_for = 0.0

                wait_started = time.monotonic()
                speech_started = None

                speech_peak = 0.0
                speech_average = 0.0
                speech_count = 0

                while True:
                    audio, _ = stream.read(
                        block_size
                    )

                    audio = audio[:, 0].copy()

                    rms = self._calculate_rms(
                        audio
                    )

                    pre_buffer.append(audio)

                    if not started:

                        if (
                            time.monotonic()
                            - wait_started
                            >= 10
                        ):
                            return ""

                        if rms >= start_threshold:
                            speech_blocks += 1
                        else:
                            speech_blocks = max(
                                0,
                                speech_blocks - 1
                            )

                        if speech_blocks >= 2:
                            started = True
                            speech_started = (
                                time.monotonic()
                            )

                            chunks.extend(
                                list(pre_buffer)
                            )

                            speech_peak = rms
                            speech_average = rms
                            speech_count = 1
                            silent_for = 0.0

                            print(
                                "Beszéd érzékelve"
                            )

                    else:
                        chunks.append(audio)

                        speech_count += 1

                        speech_average += (
                            rms - speech_average
                        ) / speech_count

                        speech_peak = max(
                            speech_peak,
                            rms
                        )

                        relative_end = max(
                            end_threshold,
                            speech_peak * 0.020,
                            speech_average * 0.06
                        )

                        if rms <= relative_end:
                            silent_for += (
                                block_duration
                            )
                        else:
                            silent_for = 0.0

                        if (
                            silent_for
                            >= silence_seconds
                        ):
                            break

                        if (
                            time.monotonic()
                            - speech_started
                            >= max_seconds
                        ):
                            break

        except Exception as e:
            print(
                f"Mikrofon hiba: {e}"
            )
            return ""

        if not started or not chunks:
            return ""

        audio = np.concatenate(chunks)

        if len(audio) == 0:
            return ""

        audio = audio.astype(
            np.float32
        )

        duration = (
            len(audio)
            / sample_rate
        )

        if duration < self.minimum_audio_seconds:
            return ""

        rms = self._calculate_rms(audio)
        peak = self._calculate_peak(audio)

        if rms < self.minimum_rms:
            return ""

        if peak < self.minimum_peak:
            return ""

        speech_energy = max(
            speech_peak,
            speech_average
        )

        if speech_energy < start_threshold:
            return ""

        if peak > 0.95:
            audio = (
                audio
                / peak
                * 0.85
            )

        try:
            segments, info = (
                self.model.transcribe(
                    audio,
                    language=self.language,
                    task="transcribe",
                    beam_size=5,
                    best_of=5,
                    temperature=0,
                    vad_filter=True,
                    vad_parameters={
                        "min_silence_duration_ms": 500,
                        "speech_pad_ms": 180
                    },
                    condition_on_previous_text=False,
                    no_speech_threshold=0.65,
                    log_prob_threshold=-1.2,
                    compression_ratio_threshold=2.4,
                    initial_prompt=self.initial_prompt
                )
            )

            segments = list(segments)

            valid_segments = []

            for segment in segments:
                segment_text = (
                    segment.text.strip()
                )

                if not segment_text:
                    continue

                if (
                    segment.end
                    - segment.start
                    < 0.08
                ):
                    continue

                valid_segments.append(
                    segment_text
                )

            text = " ".join(
                valid_segments
            ).strip()

        except Exception as e:
            print(
                f"Whisper hiba: {e}"
            )
            return ""

        if not text:
            return ""

        text = " ".join(
            text.split()
        )

        if self._is_hallucination(text):
            return ""

        print(
            f"Felismert szöveg: {text}"
        )

        return text

    def listen(self):
        return self.listen_and_transcribe()