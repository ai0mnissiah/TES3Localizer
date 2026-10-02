"""
core/tes3_format.py - Low-level TES3 record/subrecord packer and unpacker.
"""
import struct
import os

def pack_subrecord(sub_type: str, data: bytes) -> bytes:
    """Pack a single TES3 subrecord: 4-byte ASCII type + 4-byte uint32 size + data."""
    type_b = sub_type.encode("ascii")[:4].ljust(4, b"\x00")
    return struct.pack("<4sI", type_b, len(data)) + data

def pack_record(rec_type: str, subrecords_bytes: bytes, flags: int = 0) -> bytes:
    """Pack a top-level TES3 record: 4-byte ASCII type + 4-byte uint32 size + 8-byte flags + data."""
    type_b = rec_type.encode("ascii")[:4].ljust(4, b"\x00")
    return struct.pack("<4sIII", type_b, len(subrecords_bytes), flags, 0) + subrecords_bytes

def build_header(master_file: str, num_records: int, author: str = "TES3Localizer", description: str = "Translation patch") -> bytes:
    """Create valid TES3 HEDR/MAST/DATA header for .esp plugin."""
    version = struct.pack("<f", 1.2)
    file_type = struct.pack("<I", 1)  # 1 = ESP plugin
    author_b = author.encode("cp1252", errors="replace")[:32].ljust(32, b"\x00")
    desc_b = description.encode("cp1252", errors="replace")[:256].ljust(256, b"\x00")
    num_b = struct.pack("<I", num_records)
    hedr_data = version + file_type + author_b + desc_b + num_b

    subs = pack_subrecord("HEDR", hedr_data)
    subs += pack_subrecord("MAST", os.path.basename(master_file).encode("cp1252", errors="replace") + b"\x00")
    master_size = os.path.getsize(master_file) if os.path.exists(master_file) else 0
    subs += pack_subrecord("DATA", struct.pack("<q", master_size))
    return pack_record("TES3", subs)

def strip_diacritics(text: str) -> str:
    """Replace non-ASCII / Polish characters with standard Latin equivalents for 100% font compatibility."""
    mapping = {
        'ą': 'a', 'ć': 'c', 'ę': 'e', 'ł': 'l', 'ń': 'n', 'ó': 'o', 'ś': 's', 'ź': 'z', 'ż': 'z',
        'Ą': 'A', 'Ć': 'C', 'Ę': 'E', 'Ł': 'L', 'Ń': 'N', 'Ó': 'O', 'Ś': 'S', 'Ź': 'Z', 'Ż': 'Z'
    }
    return "".join(mapping.get(c, c) for c in text)
