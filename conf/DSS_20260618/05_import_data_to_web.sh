 #!/bin/bash

# Importujemy dane augmentowane (te, na których uczony był model manual + augmented)
#  -> do ręcznej weryfikacji podczas tutorialu
#  -> tym pokażemy jak 'poprawiając' dane wpłyniemy na wynik bez decyzji człowieka
bash code/web_app/import_to_db.sh \
  resources/dataset/twitteremo/augmented/clarinpl-twitteremo-train-sample-5k_labels_augmented-training.jsonl