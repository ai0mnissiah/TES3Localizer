"""
core/translator.py - Handles placeholder masking for game keywords and batch translation.
Supports multiple translation engines: Google Translate (Free), DeepL, or Passthrough/Custom.
"""
import os
import re
import json
import time
from deep_translator import GoogleTranslator

# Supported translation engines
AVAILABLE_ENGINES = ["google", "deepl"]

STOPWORDS = {
    "the", "and", "a", "of", "to", "in", "is", "that", "it", "he", "was", "for", "on", "are", "as", 
    "with", "his", "they", "i", "at", "be", "this", "have", "from", "or", "one", "had", "by", "word", 
    "but", "not", "what", "all", "were", "we", "when", "your", "can", "said", "there", "use", "an", 
    "each", "which", "she", "do", "how", "their", "if", "will", "up", "other", "about", "out", "many", 
    "then", "them", "these", "so", "some", "her", "would", "make", "like", "him", "into", "time", "has", 
    "look", "two", "more", "write", "go", "see", "number", "no", "way", "could", "people", "my", "than", 
    "first", "water", "been", "call", "who", "oil", "its", "now", "find", "new", "any", "me", "only", "very"
}

def load_keywords(keywords_file: str) -> list[str]:
    """Loads preserved topic/name keywords from a file."""
    keywords = set()
    if os.path.exists(keywords_file):
        with open(keywords_file, "r", encoding="utf-8") as f:
            for line in f:
                w = line.strip()
                if w and len(w) > 1 and w.lower() not in STOPWORDS:
                    keywords.add(w)
    return list(keywords)

def mask_placeholders(text: str, keywords: list[str]) -> tuple[str, list, list]:
    """
    Replaces % variables (e.g. %PCName) and game topics with {V0}, {P0} placeholders
    so the translation engine does not alter or break game dialogue logic.
    """
    var_reps = []
    def var_repl(m):
        val = m.group(0)
        idx = len(var_reps)
        var_reps.append(val)
        return f"{{V{idx}}}"
    processed = re.sub(r'%[a-zA-Z]+', var_repl, text)

    lower_text = processed.lower()
    present_keywords = [k for k in keywords if k.lower() in lower_text]
    present_keywords.sort(key=len, reverse=True)

    name_reps = []
    for k in present_keywords:
        pattern = ""
        if k[0].isalnum(): pattern += r'\b'
        pattern += re.escape(k)
        if k[-1].isalnum(): pattern += r'\b'
        def name_repl(m):
            val = m.group(0)
            idx = len(name_reps)
            name_reps.append(val)
            return f"{{P{idx}}}"
        processed = re.sub(pattern, name_repl, processed, flags=re.IGNORECASE)

    return processed, var_reps, name_reps

def unmask_placeholders(translated_text: str, var_reps: list, name_reps: list) -> str:
    """Restores masked variables and game topic keywords in the translated sentence."""
    result = translated_text
    for idx, name in enumerate(name_reps):
        placeholder = f"{{P{idx}}}"
        result = re.sub(re.escape(placeholder), name, result, flags=re.IGNORECASE)
    for idx, var in enumerate(var_reps):
        placeholder = f"{{V{idx}}}"
        result = re.sub(re.escape(placeholder), var, result, flags=re.IGNORECASE)
    return result

def get_translator_instance(engine: str = "google", target_lang: str = "pl", api_key: str = None):
    """Factory creating translation instance with informational output."""
    if engine.lower() == "deepl" and api_key:
        from deep_translator import DeeplTranslator
        print(f"[+] Active Engine: DeepL API (Target: {target_lang})")
        return DeeplTranslator(api_key=api_key, source="en", target=target_lang)
    else:
        print(f"[+] Active Engine: Google Translate Free (Target: {target_lang})")
        return GoogleTranslator(source="en", target=target_lang)

def run_translation(input_json: str, output_json: str, keywords_file: str, target_lang: str = "pl", engine: str = "google", api_key: str = None, batch_size: int = 25):
    """Translates dialogue texts in batch while guaranteeing game keyword preservation."""
    with open(input_json, "r", encoding="utf-8") as f:
        data = json.load(f)
    info_entries = data.get("INFO", {})

    keywords = load_keywords(keywords_file)
    print(f"[+] Preserved topics/keywords loaded: {len(keywords)}")

    # Load existing translated file if resuming
    translated = {}
    if os.path.exists(output_json):
        try:
            with open(output_json, "r", encoding="utf-8") as f:
                translated = json.load(f).get("INFO", {})
            print(f"[+] Resuming from existing translation: {len(translated)} entries.")
        except Exception:
            pass

    to_process_keys = [k for k, v in info_entries.items() if v.strip() and k not in translated]
    total = len(to_process_keys)
    print(f"[+] Entries remaining to translate: {total}")

    if total == 0:
        print("[+] Nothing to translate.")
        return

    translator = get_translator_instance(engine=engine, target_lang=target_lang, api_key=api_key)

    batch_keys = []
    batch_texts = []
    batch_vars = []
    batch_names = []
    current_chars = 0
    char_limit = 3500

    processed_count = 0
    start_time = time.time()

    for i, key in enumerate(to_process_keys):
        original_text = info_entries[key]
        proc_text, v_rep, n_rep = mask_placeholders(original_text, keywords)
        text_len = len(proc_text)

        if len(batch_texts) >= batch_size or (current_chars + text_len > char_limit):
            joined = "\n".join(batch_texts)
            try:
                trans_joined = translator.translate(joined)
                lines = [l.strip() for l in trans_joined.split("\n")]
                if len(lines) == len(batch_texts):
                    for k, l, v, n in zip(batch_keys, lines, batch_vars, batch_names):
                        translated[k] = unmask_placeholders(l, v, n)
                else:
                    raise ValueError("Batch line mismatch")
            except Exception:
                for k, t, v, n in zip(batch_keys, batch_texts, batch_vars, batch_names):
                    try:
                        time.sleep(0.3)
                        translated[k] = unmask_placeholders(translator.translate(t), v, n)
                    except Exception:
                        translated[k] = unmask_placeholders(t, v, n)

            processed_count += len(batch_keys)
            elapsed = time.time() - start_time
            speed = processed_count / elapsed if elapsed > 0 else 0
            eta_min = ((total - processed_count) / speed / 60) if speed > 0 else 0
            print(f"[*] Engine: [{engine.upper()}] | Progress: {processed_count}/{total} ({processed_count/total*100:.1f}%) | ETA: {eta_min:.1f} min")

            # Periodic save
            if processed_count % 100 < batch_size:
                data["INFO"] = translated
                with open(output_json, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)

            batch_keys, batch_texts, batch_vars, batch_names = [], [], [], []
            current_chars = 0
            time.sleep(1.0)

        batch_keys.append(key)
        batch_texts.append(proc_text)
        batch_vars.append(v_rep)
        batch_names.append(n_rep)
        current_chars += text_len

    if batch_texts:
        for k, t, v, n in zip(batch_keys, batch_texts, batch_vars, batch_names):
            try:
                translated[k] = unmask_placeholders(translator.translate(t), v, n)
            except Exception:
                translated[k] = unmask_placeholders(t, v, n)

    data["INFO"] = translated
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"[+] Translation complete using [{engine.upper()}]. Output: {output_json}")
