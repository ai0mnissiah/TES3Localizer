# TES3Localizer

> **Lossless, topic-preserving dialogue extraction & localization toolchain for *The Elder Scrolls III: Morrowind* and OpenMW.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenMW Compatible](https://img.shields.io/badge/OpenMW-100%25%20Compatible-brightgreen.svg)](https://openmw.org/)

---

## ⚡ The Problem: The "Broken Dialogue Link" in TES3

For over 20 years, localizing *Morrowind* or massive mods like *Tamriel Rebuilt* into other languages has been notorious for breaking quests and locking player progress.

### Why do traditional tools break Morrowind?
Unlike modern RPGs, Morrowind does not use traditional choice buttons for player dialogue. Instead, **the game engine dynamically creates clickable blue hyperlinks inside NPC dialogue texts whenever it matches a keyword from the `DIAL` records.**

* **The Softlock Trap**: When an NPC says:  
  `"Before you go, I have instructions on your duties."`  
  The engine highlights **`duties`** and adds it to the player's topic list.  
  If a translation tool translates `duties` to Polish (*"obowiązków"*), German (*"Pflichten"*), or Spanish (*"deberes"*), **the game engine fails to detect the topic**, no hyperlink is generated, the player cannot select the topic, and the quest softlocks (e.g., doors remain locked).
* **The Script-Break Trap**: If a translator attempts to rename the `DIAL` records to the translated words, all game scripts calling `AddTopic "duties"` or quest condition checks immediately break.

---

## 💡 The Solution: TES3Localizer

`TES3Localizer` decouples the game engine logic from the text layer:

1. **Topic-Preserving Masking**: It scans master files (`Morrowind.esm`, `TR_Mainland.esm`), builds a database of all valid topics and NPC names, and masks them with tokens (`{P0}`, `{P1}`) before translation.
2. **Contextual Translation**: Any translation engine (Google Translate, DeepL, or advanced LLMs like Claude/GPT) translates the sentence naturally, while all required engine keywords stay intact.
3. **Surgical In-Place Binary Rebuilding**: Generates clean, lightweight `.esp` patches without touching original `.esm` files, preserving exact subrecord sequences (`INAM` → `PNAM` → `NNAM` → `DATA` → `SCVR` → `NAME` → `BNAM`) and link chains.

---

## 🚀 Quickstart

### Prerequisites
* Python 3.10+
* (Optional) `deep-translator` if using automatic translation:
  ```bash
  pip install deep-translator
  ```

---

## 🖥️ Graphical Interface (GUI)

Simply run:
```bash
python tes3localizer.py
```
*(or run `python gui.py`)*

A clean desktop window will open with tabs for **Extract**, **Translate**, and **Build ESP**.

---

## ⌨️ Command Line Interface (CLI)

`TES3Localizer` features simple, standardized English commands for command line or automated CI/CD workflows:

### 1. Extract dialogues and topic keywords from Master files
```bash
python tes3localizer.py extract --masters Morrowind.esm TR_Mainland.esm --out-json dialogues.json --out-topics topics.txt
```

### 2. Translate extracted JSON with keyword preservation
```bash
python tes3localizer.py translate --input dialogues.json --output dialogues_pl.json --topics topics.txt --lang pl
```
*(Supports language codes: `pl`, `de`, `es`, `fr`, `it`, `ru`, `uk`, `cs`, etc.)*

### 3. Build the binary `.esp` patch
```bash
python tes3localizer.py build --master Morrowind.esm --json dialogues_pl.json --output Polonizacja_PL.esp
```

### 4. All-in-One Pipeline
To run extraction, translation, and building in a single command:
```bash
python tes3localizer.py pipeline --master Morrowind.esm --output Polonizacja_PL.esp --lang pl
```

---

## 📂 Project Structure

```text
TES3Localizer/
├── core/
│   ├── tes3_format.py     # Binary packer/unpacker for TES3 records & subrecords
│   ├── extractor.py       # Extracts DIAL topics, NPC names, and INFO texts
│   ├── translator.py      # Keyword-preserving translation engine with batching
│   └── builder.py         # Surgical in-place binary .esp builder
├── gui.py                 # Graphical Desktop User Interface (Tkinter)
├── tes3localizer.py       # Main CLI entrypoint
└── README.md              # Project documentation
```

---

## 🎮 Compatibility

* **Vanilla TES3: Morrowind** (Steam / GOG / CD)
* **OpenMW** (Native cross-platform engine)
* **Tamriel Rebuilt** & other large-scale province mods
* **Zero Dirty Edits**: Only touches modified dialogue strings without overwriting world cells, physics, or game scripts.

---

## 📄 License

Distributed under the **MIT License**. Free for personal, modding, and commercial use.
