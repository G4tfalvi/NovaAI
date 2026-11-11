from ddgs import DDGS


class WebSearch:

    def __init__(self):
        self.available = True

    def search(self, query, max_results=5):

        try:
            results = DDGS().text(
                query,
                region="hu-hu",
                safesearch="moderate",
                max_results=max_results
            )

            if not results:
                return "Nem találtam releváns találatokat."

            formatted = []

            for index, result in enumerate(results, 1):

                title = result.get(
                    "title",
                    "Ismeretlen cím"
                )

                body = result.get(
                    "body",
                    ""
                )

                url = result.get(
                    "href",
                    ""
                )

                formatted.append(
                    f"[{index}] {title}\n"
                    f"{body}\n"
                    f"URL: {url}"
                )

            return "\n\n".join(formatted)

        except Exception as e:

            print(f"❌ Web keresési hiba: {e}")

            return (
                "A webes keresés jelenleg nem sikerült."
            )