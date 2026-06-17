import json
import argparse
from pathlib import Path
from web_app.models import create_app, db, Example

def import_data(jsonl_path, db_path):
    app = create_app(db_path)
    with app.app_context():
        count = 0
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                data = json.loads(line)
                # Używamy pola 'tekst' zgodnie z formatem clarinpl lub 'text' zgodnie z opisem
                text = data.get('tekst') or data.get('text')
                if not text:
                    continue
                
                example = Example(text=text, original_id=data.get('id'))
                db.session.add(example)
                count += 1
                if count % 100 == 0:
                    db.session.commit()
            db.session.commit()
        print(f"Imported {count} examples.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--jsonl", required=True, help="Ścieżka do pliku JSONL")
    parser.add_argument("--db", default=None, help="Ścieżka do bazy (domyślnie instance/data.db)")
    args = parser.parse_args()
    
    import os
    from pathlib import Path
    
    # Resolve database path relative to instance/ directory
    if args.db is None:
        script_dir = Path(__file__).resolve().parent
        project_root = script_dir.parent.parent
        db_path = f"sqlite:///{project_root / 'instance' / 'data.db'}"
    else:
        db_path = args.db
    
    import_data(args.jsonl, db_path)
