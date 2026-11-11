from ai.ollama import OllamaAI


class AIAssistant:

    def __init__(self):
        self.ai = OllamaAI("qwen3:latest")
        self.available = self.ai.available

        if self.available:
            print("✅ Nova AI készen áll.")
        else:
            print("❌ Nova AI nem érhető el.")

    def ask(self, text):
        if not self.available:
            return "Az AI jelenleg nem érhető el."

        return self.ai.ask(text)