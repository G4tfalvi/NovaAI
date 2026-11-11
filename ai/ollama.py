import re
import time
import ollama

from memory.memory import Memory
from web.search import WebSearch
from datetime import datetime


class OllamaAI:

    def __init__(self, model="qwen3:latest"):
        self.model = model
        self.available = False
        self.memory = Memory()
        self.web = WebSearch()

        try:
            result = ollama.list()
            model_names = []

            for item in result.models:
                name = getattr(item, "model", None)
                if name:
                    model_names.append(name)

            if self.model in model_names:
                self.available = True
                print(f"✅ Qwen3 elérhető: {self.model}")
            else:
                print(f"❌ A modell nem található: {self.model}")

        except Exception as e:
            print(f"❌ Ollama kapcsolat hiba: {e}")

    def _get_memory_context(self, limit=10):
        memories = self.memory.get_all()[:limit]

        if not memories:
            return "Nincs elmentett memória."

        return "\n".join(
            f"{item['key']}: {item['value']}"
            for item in memories
        )

    def _get_last_open_question(self, limit=14):
        messages = self.memory.get_recent_messages(limit)

        if not messages:
            return None

        last = messages[-1]

        if last["role"] != "assistant":
            return None

        content = str(last["content"]).strip()

        if content.endswith("?"):
            return content

        return None

    def _get_conversation_context(self, limit=30):
        messages = self.memory.get_recent_messages(limit)

        if not messages:
            return "Nincs korábbi beszélgetés."

        lines = []

        for index, message in enumerate(messages, start=1):
            role_name = (
                "Felhasználó"
                if message["role"] == "user"
                else "Nova"
            )
            lines.append(
                f"{index}. {role_name}: {message['content']}"
            )

        return "\n".join(lines)

    def _save_conversation(self, role, content):
        self.memory.save_message(role, content)

    def _web_search(self, query):
        return self.web.search(query, max_results=5)

    def _remember(self, key, value):
        self.memory.remember(key, value)
        print(f"Memória mentve: {key} = {value}")
        return f"Elmentettem a memóriába: {key} = {value}"

    def _recall(self, key):
        value = self.memory.recall(key)

        if value is None:
            return "Erről nincs információm a memóriában."

        return value

    def _forget(self, key):
        value = self.memory.recall(key)

        if value is None:
            return "Ilyen információ nincs a memóriában."

        self.memory.forget(key)
        print(f"Memória törölve: {key}")
        return f"Elfelejtettem a memóriából: {key}"

    def _normalize_name(self, name):
        name = name.strip().strip(".,!?;:")

        special_names = {
            "regű": "Regő",
            "regö": "Regő",
            "regő": "Regő",
            "regu": "Regő",
            "rego": "Regő",
        }

        return special_names.get(name.lower(), name)

    def _detect_name(self, text):
        patterns = [
            r"\b(?:a\s+)?nevem\s+([A-Za-zÁÉÍÓÖŐÚÜŰáéíóöőúüű]+)",
            r"\b(?:úgy\s+hívnak|hívnak)\s+([A-Za-zÁÉÍÓÖŐÚÜŰáéíóöőúüű]+)",
            r"\b([A-Za-zÁÉÍÓÖŐÚÜŰáéíóöőúüű]+)\s+a\s+nevem",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)

            if match:
                name = self._normalize_name(match.group(1))

                if len(name) >= 2:
                    return name

        return None

    def _is_name_question(self, text):
        normalized = text.lower()

        questions = [
            "hogy hívnak",
            "hogy hivnak",
            "mi a nevem",
            "tudod a nevem",
            "emlékszel a nevemre",
            "emlekszel a nevemre",
        ]

        return any(
            question in normalized
            for question in questions
        )

    def _clean_answer(self, text):
        if not text:
            return ""

        emoji_pattern = re.compile(
            "["
            "\U0001F300-\U0001FAFF"
            "\U00002700-\U000027BF"
            "\U0001F1E6-\U0001F1FF"
            "\U00002600-\U000026FF"
            "\U0001F900-\U0001F9FF"
            "\U0001FA70-\U0001FAFF"
            "\u200d"
            "\ufe0f"
            "\u20e3"
            "]+",
            flags=re.UNICODE
        )

        text = emoji_pattern.sub("", text)
        text = re.sub(r"\s+", " ", text).strip()

        return text

    def _build_tools(self):
        return [
            {
                "type": "function",
                "function": {
                    "name": "web_search",
                    "description": "Nyilvános internetes keresést végez aktuális, friss vagy bizonytalan információkhoz.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "A keresendő kérdés vagy kifejezés."
                            }
                        },
                        "required": ["query"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "remember",
                    "description": "Információt ment Nova hosszú távú memóriájába.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "key": {"type": "string"},
                            "value": {"type": "string"},
                        },
                        "required": ["key", "value"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "recall",
                    "description": "Információt keres Nova hosszú távú memóriájában.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "key": {"type": "string"}
                        },
                        "required": ["key"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "forget",
                    "description": "Információt töröl Nova hosszú távú memóriájából.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "key": {"type": "string"}
                        },
                        "required": ["key"],
                    },
                },
            },
        ]

    def _chat(self, messages, tools):
        return ollama.chat(
            model=self.model,
            messages=messages,
            tools=tools,
            options={
                "temperature": 0.55,
                "num_predict": 500,
                "top_p": 0.9,
            },
            think=False,
            keep_alive="30m",
        )

    def ask(self, text):
        current_date = datetime.now().strftime("%Y. %m. %d.")
        current_year = datetime.now().year

        if not self.available:
            return "Az AI jelenleg nem érhető el."

        if not text or not str(text).strip():
            return None

        text = str(text).strip()

        try:
            detected_name = self._detect_name(text)

            if detected_name:
                self._remember(
                    "felhasználó_neve",
                    detected_name
                )

                answer = (
                    f"Rendben, megjegyeztem. "
                    f"Téged {detected_name} néven hívlak."
                )

                self._save_conversation("user", text)
                self._save_conversation("assistant", answer)

                return answer

            if self._is_name_question(text):
                name = self.memory.recall("felhasználó_neve")

                if name:
                    answer = f"Téged {name} néven hívlak."
                else:
                    answer = "Még nem tudom a neved."

                self._save_conversation("user", text)
                self._save_conversation("assistant", answer)

                return answer

            t_ctx = time.time()
            memory_context = self._get_memory_context()
            conversation_context = self._get_conversation_context(14)
            last_question = self._get_last_open_question(14)
            print(f"⏱️ [Ollama] Kontextus összeállítás (memória+beszélgetés): {time.time() - t_ctx:.2f} mp")

            system_prompt = (
                f"Az aktuális dátum: {current_date}. Az aktuális év: {current_year}. "
                "Nova-nak hívnak téged, egy magyar személyi AI-asszisztens vagy. "
                "A felhasználóval természetesen, közvetlenül és emberien beszélgetsz. "
                "Mindig magyarul válaszolj, kivéve ha a felhasználó más nyelven kér választ. "
                "Beszédre válaszolsz, ezért a válaszaid legyenek könnyen felolvashatók. "
                "A beszélgetést folytonos párbeszédként kezeld, ne különálló kérdések sorozataként. "
                "Minden válasz előtt vedd figyelembe az aktuális üzenetet és a legutóbbi beszélgetés teljes releváns kontextusát. "
                "Ha a felhasználó röviden utal egy korábbi témára, az előzményekből azonosítsd a témát. "
                "Ha azt mondja például, hogy igen, persze, mondd, folytasd, fejtsd ki, erre gondoltam, vagy ehhez hasonlóan reagál, mindig az előző Nova-válaszhoz kapcsolódva folytasd. "
                "Ha Nova az előző válaszában felajánlott egy magyarázatot, részletezést, példát vagy további segítséget, és a felhasználó erre igennel vagy hasonlóan reagál, pontosan azt folytasd, amit felajánlottál. "
                "Ne válts másik témára ilyen folytató válasz esetén. "
                "Ne kérd meg a felhasználót, hogy ismételje el, miről beszéltünk, ha az információ megtalálható a kontextusban. "
                "Ne korlátozd magad mereven két mondatra, de alapértelmezetten legyél tömör: törekedj rá, hogy a válaszod 1-3 mondatban elférjen. "
                "Csak akkor válaszolj hosszabban és részletesebben, ha ezt a téma egyértelműen megkívánja — például ha a felhasználó kifejezetten részletet, magyarázatot vagy listát kér, vagy egy lépésről lépésre elmagyarázandó folyamatról van szó. "
                "Ha több lehetőség közül ajánlanál (például filmek, éttermek, könyvek), alapból ne sorolj fel sokat: mondj 1-2 jó javaslatot rövid indoklással, és ha van értelme, kérdezd meg, kér-e a felhasználó további ötleteket. "
                "A beszélgetést élő, emberi párbeszédként kezeld: nem minden Nova-válasznak kell lezárnia a témát. "
                "Ha egy témában természetesen adódik folytatás — például a felhasználó válasza felvet valami újat, vagy több irányba is mehetne a beszélgetés —, tegyél fel egy rövid, kapcsolódó visszakérdezést, ami továbbviszi a beszélgetést, ahogy egy élő társalgásban tennéd. "
                "Ezt viszont ne minden válasz végén tedd meg gépiesen: csak akkor kérdezz vissza, ha az tényleg természetes és indokolt, különben egyszerűen zárd le a gondolatot. "
                "Ha korábban te tettél fel egy kérdést, és a felhasználó mostani üzenete arra válaszol — akár nagyon röviden, egy-két szóban is —, azt mindig az adott kérdésre adott válaszként kezeld, és onnan folytasd a beszélgetést; ne kérdezz vissza ugyanarra, és ne kezdj új témát. "
                "A korábbi beszélgetés sorai sorszámozva vannak: a szám az időbeli sorrendet jelzi, kisebb szám = korábban hangzott el. "
                "Ha a felhasználó arra kérdez rá, hogy mi volt az 'első', 'legelső', 'korábban' vagy 'előbb' említett dolog (pl. film, hely, név), mindig a legkisebb sorszámú, releváns sorból indulj ki, ne a legutóbb (legnagyobb sorszámú) említettből — ez gyakori hibaforrás, légy rá különösen figyelmes. "
                "Ha a felhasználó véleményt vagy személyesebb választ kér, nyugodtan reagálj közvetlenül. "
                "Ne gondolkodj hangosan. "
                "Ne írd le a belső gondolatmenetedet. "
                "Ne találj ki tényeket. "
                "Ha valamiben bizonytalan vagy, jelezd. "
                "Aktuális, friss vagy bizonytalan információ esetén használd a webes kereső eszközt. "
                "A felhasználó nevét és más elmentett információkat a memóriából használhatod. "
                "Ha a felhasználó információt szeretne elmenteni, használd a remember eszközt. "
                "Ha egy korábban elmentett információra van szükséged, használd a recall eszközt. "
                "Ha a felhasználó azt kéri, hogy felejts el valamit, használd a forget eszközt. "
                "Ne használj emojikat. "
                "A válasz kizárólag természetes, felolvasható szöveg legyen. "
                "A Whisper néha félrehallhat magyar szavakat. "
                "A mondat jelentése alapján próbáld megérteni és javítani a nyilvánvaló félrehallásokat. "
                "Regő alkotott. Ha róla kérdeznek, a rendelkezésedre álló információk alapján válaszolj."
                f"\n\nElmentett memória:\n{memory_context}"
                f"\n\nKorábbi beszélgetés:\n{conversation_context}"
            )

            if last_question:
                system_prompt += (
                    f"\n\nFontos: a legutóbbi válaszodat ezzel a kérdéssel zártad: "
                    f"\"{last_question}\" "
                    "A felhasználó mostani üzenete valószínűleg erre válaszol, "
                    "akár nagyon röviden is — kezeld ennek a kérdésnek a "
                    "válaszaként, és onnan folytasd, ne kérdezz vissza újra "
                    "ugyanarra."
                )

            system_prompt += (
                "\n\nFONTOS SZABÁLY A VÁLASZ HOSSZÁRA: "
                "alapból a válaszod legyen maximum 2-3 mondat, "
                "nagyjából 40-60 szó. "
                "Csak akkor lépd túl ezt, ha a felhasználó kifejezetten "
                "hosszabb, részletesebb választ, listát vagy lépésenkénti "
                "magyarázatot kér. "
                "Javaslatoknál (film, hely, könyv, stb.) alapból csak "
                "1 dolgot ajánlj rövid indoklással, ne sorolj fel többet."
            )

            messages = [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": text,
                },
            ]

            tools = self._build_tools()

            t0 = time.time()
            response = self._chat(messages, tools)
            print(f"⏱️ [Ollama] 1. chat hívás: {time.time() - t0:.2f} mp")

            tool_calls = getattr(
                response.message,
                "tool_calls",
                None
            )

            if tool_calls:
                messages.append({
                    "role": "assistant",
                    "content": response.message.content or "",
                    "tool_calls": tool_calls,
                })

                for tool_call in tool_calls:
                    function = tool_call.function
                    name = function.name
                    arguments = function.arguments

                    print(f"🔧 [Ollama] Tool hívás: {name}({arguments})")
                    t_tool = time.time()

                    if name == "web_search":
                        result = self._web_search(arguments["query"])
                    elif name == "remember":
                        result = self._remember(
                            arguments["key"],
                            arguments["value"]
                        )
                    elif name == "recall":
                        result = self._recall(arguments["key"])
                    elif name == "forget":
                        result = self._forget(arguments["key"])
                    else:
                        result = "Ismeretlen eszköz."

                    print(f"⏱️ [Ollama] Tool '{name}' végrehajtás: {time.time() - t_tool:.2f} mp")

                    messages.append({
                        "role": "tool",
                        "content": result,
                    })

                t1 = time.time()
                response = self._chat(messages, tools)
                print(f"⏱️ [Ollama] 2. chat hívás: {time.time() - t1:.2f} mp")

            answer = response.message.content or ""
            answer = self._clean_answer(answer)

            if not answer:
                return "Most nem tudtam értelmes választ adni."

            self._save_conversation("user", text)
            self._save_conversation("assistant", answer)

            return answer

        except Exception as e:
            print(f"Ollama AI hiba: {e}")
            return "Sajnos most nem tudok válaszolni."