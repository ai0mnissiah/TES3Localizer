"""
core/extractor.py - Extracts DIAL topics, NPC names, and dialogue INFO texts from TES3 ESM/ESP files.
"""
import struct
import os
import json

def extract_dialogues_and_topics(master_files: list[str]) -> tuple[dict, set, set]:
    """
    Scans TES3 ESM/ESP files and extracts:
      - dialogues: dict mapping INAM -> dialogue text (NAME)
      - topics: set of all clickable DIAL topic strings
      - npc_names: set of all NPC full names (FNAM)
    """
    dialogues = {}
    topics = set()
    npc_names = set()

    for file_path in master_files:
        if not os.path.exists(file_path):
            print(f"[-] File not found: {file_path}")
            continue

        print(f"[+] Scanning: {os.path.basename(file_path)}...")
        with open(file_path, "rb") as f:
            while True:
                hdr = f.read(16)
                if len(hdr) < 16:
                    break
                rec_type_b, rec_size, _, _ = struct.unpack("<4sIII", hdr)
                rec_type = rec_type_b.decode("ascii", errors="ignore").rstrip("\x00")
                data = f.read(rec_size)

                if rec_type == "DIAL":
                    off = 0
                    dial_name = ""
                    dial_type = 0
                    while off + 8 <= rec_size:
                        st, ss = struct.unpack("<4sI", data[off:off+8])
                        st = st.decode("ascii", errors="ignore").rstrip("\x00")
                        sd = data[off+8:off+8+ss]
                        if st == "NAME":
                            dial_name = sd.decode("cp1252", errors="replace").rstrip("\x00")
                        elif st == "DATA":
                            dial_type = sd[0] if sd else 0
                        off += 8 + ss
                    # Type 0 = Regular topic (hyperlinked in dialogues)
                    if dial_type == 0 and dial_name.strip():
                        topics.add(dial_name.strip())

                elif rec_type == "NPC_":
                    off = 0
                    while off + 8 <= rec_size:
                        st, ss = struct.unpack("<4sI", data[off:off+8])
                        st = st.decode("ascii", errors="ignore").rstrip("\x00")
                        sd = data[off+8:off+8+ss]
                        if st == "FNAM":
                            fname = sd.decode("cp1252", errors="replace").rstrip("\x00")
                            if fname.strip():
                                npc_names.add(fname.strip())
                        off += 8 + ss

                elif rec_type == "INFO":
                    off = 0
                    inam = None
                    text = ""
                    while off + 8 <= rec_size:
                        st, ss = struct.unpack("<4sI", data[off:off+8])
                        st = st.decode("ascii", errors="ignore").rstrip("\x00")
                        sd = data[off+8:off+8+ss]
                        if st == "INAM":
                            inam = sd.decode("cp1252", errors="replace").rstrip("\x00")
                        elif st == "NAME":
                            text = sd.decode("cp1252", errors="replace").rstrip("\x00")
                        off += 8 + ss
                    if inam:
                        dialogues[inam] = text

    return dialogues, topics, npc_names

def run_extraction(master_files: list[str], output_json: str, output_topics_txt: str = None):
    dialogues, topics, npc_names = extract_dialogues_and_topics(master_files)
    
    # Save dialogues
    os.makedirs(os.path.dirname(os.path.abspath(output_json)), exist_ok=True)
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump({"INFO": dialogues}, f, indent=4, ensure_ascii=False)
    print(f"[+] Saved {len(dialogues)} dialogue entries to: {output_json}")

    # Save topics / names preservation list
    if output_topics_txt:
        combined = {item for item in topics.union(npc_names) if len(item) > 1}
        with open(output_topics_txt, "w", encoding="utf-8") as f:
            for item in sorted(combined):
                f.write(item + "\n")
        print(f"[+] Saved {len(combined)} preserved topics and NPC names to: {output_topics_txt}")
