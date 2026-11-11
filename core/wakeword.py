import time

import numpy as np
import sounddevice as sd
from openwakeword.model import Model


class WakeWordListener:

    def __init__(
        self,
        model_path,
        threshold=0.55
    ):
        if not model_path:
            raise FileNotFoundError(
                "Nincs .onnx wake word modell "
                "a models mappában."
            )

        self.threshold = threshold

        self.model = Model(
            wakeword_models=[model_path],
            inference_framework="onnx"
        )

        self.model_name = next(
            iter(
                self.model.models.keys()
            )
        )

        self.blocksize = 1280
        self.required_hits = 2
        self.hit_timeout = 0.45
        self.cooldown = 0.7

    def wait_for_wakeword(self):
        self.model.reset()

        consecutive_hits = 0
        first_hit_time = None

        with sd.RawInputStream(
            samplerate=16000,
            blocksize=self.blocksize,
            dtype="int16",
            channels=1
        ) as stream:

            while True:
                data, overflowed = stream.read(
                    self.blocksize
                )

                audio = np.frombuffer(
                    data,
                    dtype=np.int16
                )

                if audio.size == 0:
                    continue

                prediction = self.model.predict(
                    audio
                )

                score = float(
                    prediction.get(
                        self.model_name,
                        0.0
                    )
                )

                current_time = time.monotonic()

                if score >= self.threshold:

                    if consecutive_hits == 0:
                        first_hit_time = (
                            current_time
                        )

                    if (
                        first_hit_time is not None
                        and (
                            current_time
                            - first_hit_time
                        ) <= self.hit_timeout
                    ):
                        consecutive_hits += 1
                    else:
                        consecutive_hits = 1
                        first_hit_time = (
                            current_time
                        )

                else:
                    if (
                        first_hit_time is not None
                        and (
                            current_time
                            - first_hit_time
                        ) > self.hit_timeout
                    ):
                        consecutive_hits = 0
                        first_hit_time = None

                if (
                    consecutive_hits
                    >= self.required_hits
                ):
                    time.sleep(
                        self.cooldown
                    )

                    self.model.reset()

                    return