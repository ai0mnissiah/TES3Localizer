"""
core/builder.py - Surgically rebuilds TES3 .esp plugin patch from translated JSON,
preserving all original record structures, script results (BNAM), conditions (SCVR),
and link chains (PNAM/NNAM).
"""
import struct
import os
import json
from collections import OrderedDict
from .tes3_format import pack_subrecord, pack_record, build_header, strip_diacritics

def build_info_subrecords(orig_subs: list, translated_text: str, strip_non_ascii: bool = True) -> bytes:
    """Replaces only the NAME subrecord in-place, keeping all other subrecords intact."""
    result = b""
    name_placed = False

    for sub_t, sub_d in orig_subs:
        if sub_t == "NAME":
            if translated_text:
                text_to_pack = strip_diacritics(translated_text) if strip_non_ascii else translated_text
                result += pack_subrecord("NAME", text_to_pack.encode("cp1252", errors="replace") + b"\x00")
            else:
                result += pack_subrecord("NAME", sub_d)
            name_placed = True
        else:
            result += pack_subrecord(sub_t, sub_d)

    if not name_placed and translated_text:
        text_to_pack = strip_diacritics(translated_text) if strip_non_ascii else translated_text
        result += pack_subrecord("NAME", text_to_pack.encode("cp1252", errors="replace") + b"\x00")

    return result

def run_build(master_esm: str, translated_json: str, output_esp: str, author: str = "TES3Localizer", strip_non_ascii: bool = True):
    """Parses master ESM and generates a clean .esp patch with translated dialogue."""
    print(f"[+] Loading translations from: {translated_json}...")
    with open(translated_json, "r", encoding="utf-8") as f:
        translated_info = json.load(f).get("INFO", {})

    print(f"[+] Parsing master binary: {master_esm}...")
    orig_records = {}
    dial_data_map = {}
    current_dial = ""

    with open(master_esm, "rb") as f:
        while True:
            hdr = f.read(16)
            if len(hdr) < 16:
                break
            rec_type_b, rec_size, _, _ = struct.unpack("<4sIII", hdr)
            rec_type = rec_type_b.decode("ascii", errors="ignore").rstrip("\x00")

            if rec_type == "DIAL":
                data = f.read(rec_size)
                off = 0
                dial_name = ""
                dial_data = b"\x00"
                while off + 8 <= rec_size:
                    st, ss = struct.unpack("<4sI", data[off:off+8])
                    st = st.decode("ascii", errors="ignore").rstrip("\x00")
                    sd = data[off+8:off+8+ss]
                    if st == "NAME":
                        dial_name = sd.decode("cp1252", errors="replace").rstrip("\x00")
                    elif st == "DATA":
                        dial_data = sd
                    off += 8 + ss
                if dial_name:
                    dial_data_map[dial_name] = dial_data
                    current_dial = dial_name

            elif rec_type == "INFO":
                data = f.read(rec_size)
                off = 0
                inam = None
                subs = []
                while off + 8 <= rec_size:
                    st, ss = struct.unpack("<4sI", data[off:off+8])
                    st = st.decode("ascii", errors="ignore").rstrip("\x00")
                    sd = data[off+8:off+8+ss]
                    subs.append((st, sd))
                    if st == "INAM":
                        inam = sd.decode("cp1252", errors="replace").rstrip("\x00")
                    off += 8 + ss
                if inam:
                    orig_records[inam] = {"dial": current_dial, "subs": subs}
            else:
                f.seek(rec_size, os.SEEK_CUR)

    print(f"[+] Found {len(orig_records)} INFO dialogue nodes across {len(dial_data_map)} DIAL topics.")

    # Group INFOs by DIAL maintaining original order
    dial_to_inams = OrderedDict()
    for inam, rec in orig_records.items():
        dial_to_inams.setdefault(rec["dial"], []).append(inam)

    print(f"[+] Compiling ESP binary patch...")
    esp_records = b""
    num_records = 0

    for dial_name, inams in dial_to_inams.items():
        # Pack DIAL record
        dial_subs = pack_subrecord("NAME", dial_name.encode("cp1252", errors="replace") + b"\x00")
        dial_subs += pack_subrecord("DATA", dial_data_map.get(dial_name, b"\x00"))
        esp_records += pack_record("DIAL", dial_subs)
        num_records += 1

        # Pack INFO records
        for inam in inams:
            trans_text = translated_info.get(inam, "").strip()
            orig = orig_records.get(inam)
            if not orig:
                continue
            info_subs = build_info_subrecords(orig["subs"], trans_text, strip_non_ascii=strip_non_ascii)
            esp_records += pack_record("INFO", info_subs)
            num_records += 1

    header = build_header(master_esm, num_records, author=author)

    os.makedirs(os.path.dirname(os.path.abspath(output_esp)), exist_ok=True)
    with open(output_esp, "wb") as f:
        f.write(header)
        f.write(esp_records)

    size_mb = os.path.getsize(output_esp) / (1024 * 1024)
    print(f"[+] Success! Generated {num_records} records.")
    print(f"[+] ESP plugin created: {output_esp} ({size_mb:.2f} MB)")
