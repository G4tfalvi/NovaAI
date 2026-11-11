import time

from config.settings import SETTINGS
from core.wakeword import WakeWordListener
from speech.stt import SpeechToText
from speech.tts import TextToSpeech
from commands.router import CommandRouter
from ai.assistant import AIAssistant


def main():

    print("=" * 60)
    print("NOVA ASSISTANT")
    print("=" * 60)

    tts = TextToSpeech()

    stt = SpeechToText(
        SETTINGS.stt_model,
        SETTINGS.stt_language
    )

    wake = WakeWordListener(
        SETTINGS.wakeword_model,
        threshold=SETTINGS.wakeword_threshold
    )

    ai = AIAssistant()

    router = CommandRouter(ai, tts)

    print("Nova elindult.")

    try:

        while True:

            wake.wait_for_wakeword()

            print()
            print("Nova felébredt!")

            tts.speak("Hallgatlak.")

            while True:

                text = stt.listen_and_transcribe()

                if not text:
                    tts.speak("Nem hallottam semmit.")
                    continue

                normalized = text.lower().strip()

                exit_words = [
                    "aludj",
                    "aluj",
                    "alulj",
                    "alugyjál",
                    "alúgyjál",
                    "alújj",
                    "alulj el",
                    "alúgyál",
                    "alúdjál",
                    "aluj el",
                    "aludj el",
                    "alugy el",
                    "alúgy el",
                    "kapcs off",
                    "kapcs ki",
                    "állj le",
                    "állj le nova",
                    "kapcsold ki magad",
                    "viszlát",
                    "visszlát",
                    "annyi volt",
                    "köszönöm ennyi",
                    "ennyi volt",
                    "viszlat nova"
                ]

                if any(
                    word in normalized
                    for word in exit_words
                ):
                    print()
                    print("💤 Nova alvó módba lépett.")
                    print()
                    break

                start = time.time()

                answer = router.handle(text)

                print(
                    f"⏱️ Router válaszidő: "
                    f"{time.time() - start:.2f} mp"
                )

                if answer:

                    tts_start = time.time()

                    interrupted = tts.speak(answer)

                    if interrupted:
                        print("🛑 Nova beszédét megszakítottad.")

                    tts_time = time.time() - tts_start

                    print(
                        f"⏱️ TTS idő: "
                        f"{tts_time:.2f} mp"
                    )

    except KeyboardInterrupt:
        print()
        print("Nova leállt.")


if __name__ == "__main__":
    main()