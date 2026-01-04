An autonomous AI-powered Twitch streamer built using free and open-source tools.
The system listens to live Twitch chat, generates AI responses, converts them to speech, animates a VTuber avatar, and streams everything live via OBS — with zero paid APIs.

✨ Features

Real-time Twitch chat integration

AI-generated responses using free LLM inference

Open-source text-to-speech pipeline

VTuber avatar with audio-based lip sync

OBS-based streaming workflow

Modular, upgrade-ready architecture

Designed to run 24/7 on free cloud tiers

🏗️ High-Level Architecture
Twitch Chat
   ↓
Twitch Bot (Event Listener)
   ↓
AI Control Layer (Prompt + Logic)
   ↓
LLM (Free Inference)
   ↓
Text-to-Speech
   ↓
VTuber Avatar
   ↓
OBS
   ↓
Live Twitch Stream

🧠 Core Components

Twitch Bot
Connects to Twitch chat, ingests events, filters spam, and applies cooldown rules.

AI Control Layer
Orchestrates responses, builds prompts with personality, and decides when the AI should speak.

LLM (AI Brain)
Generates natural language replies using free hosted inference models.

Text-to-Speech (TTS)
Converts AI-generated text into speech audio.

VTuber Layer
Animates a virtual avatar and performs lip-sync using audio input.

OBS
Combines video and audio sources and streams to Twitch.

🛠️ Tech Stack

Language: Python

Chat API: Twitch

AI Inference: Hugging Face

Text-to-Speech: Coqui TTS

VTuber Software: VTube Studio

Streaming: OBS Studio

🚀 Getting Started (High Level)

Create a Twitch bot account and generate OAuth tokens

Run the Twitch bot to listen to chat events

Connect the bot to free LLM inference

Convert responses to speech using TTS

Route audio to VTuber avatar for lip sync

Stream avatar and audio using OBS

🎯 Design Goals

Zero-cost: No paid APIs required

Loose coupling: Easy to replace AI, TTS, or avatar

Event-driven: Chat-driven response pipeline

Scalable: Upgrade-ready for better AI, voice, or MCP
