"""
TES3Localizer - Lossless Dialogue & Mod Localization Toolchain for The Elder Scrolls III: Morrowind / OpenMW.
CLI Entrypoint.
"""
import sys
import argparse
from core.extractor import run_extraction
from core.translator import run_translation
from core.builder import run_build

def main():
    parser = argparse.ArgumentParser(
        prog="tes3localizer",
        description="TES3Localizer: Clean, lossless dialogue extraction and localization toolchain for Morrowind & OpenMW mods."
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # 1. Extract command
    extract_p = subparsers.add_parser("extract", help="Extract dialogues and game keywords/topics from ESM/ESP files to JSON.")
    extract_p.add_argument("--masters", nargs="+", required=True, help="List of master files to scan (e.g. Morrowind.esm TR_Mainland.esm)")
    extract_p.add_argument("--out-json", default="dialogues.json", help="Path to output JSON dialogue file (default: dialogues.json)")
    extract_p.add_argument("--out-topics", default="topics.txt", help="Path to output preserved keywords file (default: topics.txt)")

    # 2. Translate command
    trans_p = subparsers.add_parser("translate", help="Translate extracted dialogue JSON while preserving game topic keywords.")
    trans_p.add_argument("--input", default="dialogues.json", help="Path to source dialogue JSON file")
    trans_p.add_argument("--output", default="dialogues_translated.json", help="Path to output translated dialogue JSON")
    trans_p.add_argument("--topics", default="topics.txt", help="Path to preserved topics/keywords file")
    trans_p.add_argument("--lang", default="pl", help="Target language code (e.g. pl, de, es, fr, ru) (default: pl)")
    trans_p.add_argument("--batch-size", type=int, default=25, help="Batch size for translation requests (default: 25)")

    # 3. Build command
    build_p = subparsers.add_parser("build", help="Build a binary .esp plugin patch from master ESM and translated JSON.")
    build_p.add_argument("--master", required=True, help="Path to base master ESM (e.g. Morrowind.esm)")
    build_p.add_argument("--json", default="dialogues_translated.json", help="Path to translated JSON file")
    build_p.add_argument("--output", default="Translation_Patch.esp", help="Path to output .esp plugin file")
    build_p.add_argument("--author", default="TES3Localizer", help="Plugin author name (default: TES3Localizer)")
    build_p.add_argument("--keep-diacritics", action="store_true", help="Keep native UTF-8 diacritics instead of standard Latin transliteration")

    # 4. Pipeline command (all-in-one)
    pipe_p = subparsers.add_parser("pipeline", help="Run full pipeline: extract -> translate -> build in a single step.")
    pipe_p.add_argument("--master", required=True, help="Path to base master ESM (e.g. Morrowind.esm)")
    pipe_p.add_argument("--output", default="Translation_Patch.esp", help="Path to final .esp plugin")
    pipe_p.add_argument("--lang", default="pl", help="Target language code (default: pl)")

    # 5. GUI command
    gui_p = subparsers.add_parser("gui", help="Launch interactive graphical desktop interface.")

    if len(sys.argv) == 1:
        # No arguments provided -> launch GUI
        try:
            import gui
            gui.launch_gui()
            return
        except ImportError:
            parser.print_help()
            return

    args = parser.parse_args()

    if args.command == "extract":
        run_extraction(args.masters, args.out_json, args.out_topics)
    elif args.command == "translate":
        run_translation(args.input, args.output, args.topics, target_lang=args.lang, batch_size=args.batch_size)
    elif args.command == "build":
        run_build(args.master, args.json, args.output, author=args.author, strip_non_ascii=not args.keep_diacritics)
    elif args.command == "pipeline":
        extracted_json = "temp_dialogues.json"
        topics_txt = "temp_topics.txt"
        translated_json = f"temp_dialogues_{args.lang}.json"
        print("[*] Stage 1/3: Extracting...")
        run_extraction([args.master], extracted_json, topics_txt)
        print("[*] Stage 2/3: Translating...")
        run_translation(extracted_json, translated_json, topics_txt, target_lang=args.lang)
        print("[*] Stage 3/3: Building ESP patch...")
        run_build(args.master, translated_json, args.output)
        print("[+] Pipeline complete! Output file ready:", args.output)
    elif args.command == "gui":
        import gui
        gui.launch_gui()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
