# NovaAI

A modular, AI-powered desktop voice assistant inspired by the idea of a personal computer assistant.

**Repository:** [G4tfalvi/NovaAI](https://github.com/G4tfalvi/NovaAI)

## Overview

NovaAI is a personal desktop assistant designed to interact with the user through voice commands and AI-powered conversations.

The project combines speech recognition, text-to-speech, wake-word detection, local AI integration, and system automation into a modular Python application.

The goal is to create an assistant that can understand spoken commands, respond naturally, interact with the computer, and provide an extensible foundation for additional capabilities.

## Features

- **Wake Word Detection** – Activate the assistant using a custom wake word.
- **Speech Recognition** – Convert spoken Hungarian commands into text.
- **Text-to-Speech** – Generate spoken responses.
- **AI Integration** – Use a local language model through Ollama.
- **Command Routing** – Process commands and direct them to the appropriate modules.
- **Application Control** – Open and manage applications.
- **System Control** – Interact with Windows system functions.
- **File Management** – Perform file-related operations.
- **Weather Information** – Retrieve weather information.
- **Browser Integration** – Browser-related automation and control.

## Technologies

- Python
- OpenWakeWord
- Faster-Whisper
- Edge TTS
- Ollama
- Pygame

## Architecture

NovaAI uses a modular structure to keep different responsibilities separated.

| Module | Responsibility |
|---|---|
| `Ai/` | AI assistant and model integration |
| `Commands/` | Application, system, browser, and file commands |
| `Config/` | Configuration and settings |
| `Core/` | Core assistant functionality and wake-word detection |
| `Memory/` | Memory-related functionality |
| `Speech/` | Speech recognition and text-to-speech |
| `Web/` | Web-related functionality |

## Design Goals

- Modular and maintainable architecture
- Voice-first interaction
- Hungarian language support
- Local AI model integration
- Extensible command system
- Continuous background operation

## Development

NovaAI is an ongoing personal development project. Its architecture and capabilities are being expanded over time.

The project explores how speech technologies, local AI models, and desktop automation can work together in a single assistant.

---

Developed by [G4tfalvi](https://github.com/G4tfalvi).
