import queue


class GuiBridge:
    """
    Szálbiztos "postaláda" a Nova háttérszál (mikrofon, AI, TTS)
    és a Tkinter GUI szál között.

    A Tkinter widgetek KIZÁRÓLAG a főszálról módosíthatók biztonságosan.
    A háttérszál ide (send) teszi be az eseményeket, a GUI pedig
    rendszeres időzítéssel (root.after) kiolvassa (poll) és
    alkalmazza őket a saját szálán.

    Használat a háttérszálból (pl. nova.py-ban):
        bridge.send("status", "listening")
        bridge.send("user_message", "Hány óra van?")
        bridge.send("nova_message", "Most 14:32 van.")

    Használat a GUI-ban (main_window.py már megcsinálja ezt):
        for event_type, payload in bridge.poll():
            ...
    """

    def __init__(self):
        self._queue = queue.Queue()

    def send(self, event_type, payload=None):
        self._queue.put((event_type, payload))

    def poll(self):
        events = []

        while True:
            try:
                events.append(self._queue.get_nowait())
            except queue.Empty:
                break

        return events