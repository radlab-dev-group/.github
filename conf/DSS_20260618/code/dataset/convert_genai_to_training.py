import json
import argparse
import sys
from pathlib import Path

def convert_genai_to_training(input_path: Path, output_path: Path):
    """
    Convert JSONL from genai-classifier format to the original training format.
    
    GenAI format: {"text": "...", "labels": ["Pozytywna"], ...}
    Training format: {"text": "...", "pozytywny": 1, "negatywny": 0, "neutralny": 0, ...}
    """
    label_map = {
        "Pozytywna": "pozytywny",
        "pozytywny": "pozytywny",
        "Negatywna": "negatywny",
        "negatywny": "negatywny",
        "Neutralna": "neutralny",
        "neutralny": "neutralny",
    }
    
    all_labels = ["pozytywny", "negatywny", "neutralny"]
    
    count = 0
    with input_path.open('r', encoding='utf-8') as fin, \
         output_path.open('w', encoding='utf-8') as fout:
        for line in fin:
            if not line.strip():
                continue
            
            data = json.loads(line)
            
            # Extract text
            text = data.get("text")
            if text is None:
                # Fallback if field name is different
                text = data.get("text", "")
                
            # Extract labels
            genai_labels = data.get("labels", [])
            
            # Create output object
            out_obj = {
                "text": text
            }
            
            # Map labels to 0/1
            # Note: We assume single label for simplicity as per current task, 
            # but we can handle multiple if they exist.
            active_labels = [label_map.get(l) for l in genai_labels if l in label_map]
            
            for lbl in all_labels:
                out_obj[lbl] = 1 if lbl in active_labels else 0
            
            # Add other required fields with default 0 if missing from input
            # Original data had: radość, smutek, zaufanie, wstręt, strach, gniew, przeczuwanie, zdziwienie, ambiwalentny, sarkazm
            other_fields = ["radość", "smutek", "zaufanie", "wstręt", "strach", "gniew", "przeczuwanie", "zdziwienie", "ambiwalentny", "sarkazm"]
            for f in other_fields:
                out_obj[f] = data.get(f, 0)
                
            fout.write(json.dumps(out_obj, ensure_ascii=False) + "\n")
            count += 1
            
    print(f"Converted {count} lines from {input_path} to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Convert GenAI classifier output to training format.")
    parser.add_argument("--input", dest="input", type=Path, help="Path to input jsonl file (clean_labels)")
    parser.add_argument("--output", dest="output", type=Path, help="Path to output jsonl file")
    
    args = parser.parse_args()
    
    if not args.input.exists():
        print(f"Error: Input file {args.input} does not exist.")
        sys.exit(1)
        
    convert_genai_to_training(args.input, args.output)

if __name__ == "__main__":
    main()
