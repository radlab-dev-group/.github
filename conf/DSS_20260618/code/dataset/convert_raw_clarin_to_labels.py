import json
import argparse
import os


def convert_line(line):
    data = json.loads(line)
    text = data.get("tekst", "")

    # Etykiety to wszystkie klucze poza id, data i tekst
    exclude_keys = {"id", "data", "tekst"}
    labels = [
        key for key, value in data.items() if key not in exclude_keys and value == 1
    ]

    return json.dumps({"text": text, "labels": labels}, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(
        description="Convert raw Clarin PL TwitterEmo dataset to labels format."
    )
    parser.add_argument(
        "--input", required=True, help="Path to the input raw jsonl file"
    )
    parser.add_argument("--output", help="Path to the output jsonl file (optional)")

    args = parser.parse_args()

    input_path = args.input
    output_path = args.output

    if not output_path:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_labels{ext}"

    with (
        open(input_path, "r", encoding="utf-8") as f_in,
        open(output_path, "w", encoding="utf-8") as f_out,
    ):
        for line in f_in:
            if line.strip():
                converted = convert_line(line)
                f_out.write(converted + "\n")

    print(f"Conversion finished. Output saved to: {output_path}")


if __name__ == "__main__":
    main()
