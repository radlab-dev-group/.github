---
title: "Błędy podczas uczenia i douczania transformatorów"
date: 2021-06-22
updated: 2024-04-27
slug: bledy-podczas-uczenia-i-douczania-transformatorow
description: "Chcę wykorzystać trainera do fine-tuningowania ale dostaję komunikat CUBLAS_STATUS_ALLOC_FAILED… Dostaję informację o braku pamięci na GPU pomimo tego, że…"
categories: ["transformatory"]
image: media/bledy-podczas-uczenia-i-douczania-transformatorow/_featured.png
lang: pl
wp_id: 2050
---

### Chcę wykorzystać trainera do fine-tuningowania ale dostaję komunikat CUBLAS\_STATUS\_ALLOC\_FAILED

**Problem** pojawia się w bibliotece huggingface (transformers-4.3.2) + pytorch (torch-1.7.1) i dotyczy braku pamięci GPU.

> (…) /pytorch/aten/src/THCUNN/ClassNLLCriterion.cu:108: cunn\_ClassNLLCriterion\_updateOutput\_kernel: block: \[0,0,0\], thread: \[13,0,0\] Assertion \`t >= 0 && t < n\_classes\` failed.                                                               (…)                                                                                                                                                      torch.autograd.backward(self, gradient, retain\_graph, create\_graph)   File „/usr/local/lib/python3.8/dist-packages/torch/autograd/\_\_init\_\_.py”, line 130, in backward     Variable.\_execution\_engine.run\_backward( RuntimeError: CUDA error: CUBLAS\_STATUS\_ALLOC\_FAILED when calling \`cublasCreate(handle)\`

**Rozwiązanie:** Prawdopodobnie źle ustawiona liczba klas w trainerze. Liczba etykiet w danych oraz zadeklarowanych są różne.

### Dostaję informację o braku pamięci na GPU pomimo tego, że mam

**Problem** pojawia się w bibliotece huggingface (transformers-4.3.2) + pytorch (torch-1.7.1).

> RuntimeError: CUDA out of memory. Tried to allocate 120.00 MiB (GPU 0; 11.17 GiB total capacity; 7. 92 GiB already allocated; 145.81 MiB free; 6.56 GiB reserved in total by PyTorch)

**Rozwiązanie:** Zmniejszyć domyśle wielkości dla długości sekwencji, rozmiaru batcha podczas testowania oraz rozmiaru batcha podczas ewaluacji.

```text
--max_seq_length
--per_device_train_batch_size
--per_device_eval_batch_size
```

### Podczas rozproszonego uczenia (np. clm) dostaję komunikat typu ValueError: expected sequence of length 1024 at dim:

**Problem:** Podczas uczenia/testowania/walidacji modelu dostaję komunikat

> 83%|███████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████▋ | 5/6 \[00:07<00:00, 1.03it/s\] Traceback (most recent call last): File „run\_clm.py”, line 579, in
> main()
> File „run\_clm.py”, line 527, in main
> train\_result = trainer.train(resume\_from\_checkpoint=checkpoint)
> File „/home/pkedzia/.local/lib/python3.8/site-packages/transformers/trainer.py”, line 1547, in train
> return inner\_training\_loop(
> File „/home/pkedzia/.local/lib/python3.8/site-packages/transformers/trainer.py”, line 1769, in \_inner\_training\_loop
> for step, inputs in enumerate(epoch\_iterator):
> File „/home/pkedzia/.local/lib/python3.8/site-packages/torch/utils/data/dataloader.py”, line 681, in **next**
> data = self.\_next\_data()
> File „/home/pkedzia/.local/lib/python3.8/site-packages/torch/utils/data/dataloader.py”, line 721, in \_next\_data
> data = self.\_dataset\_fetcher.fetch(index) # may raise StopIteration
> File „/home/pkedzia/.local/lib/python3.8/site-packages/torch/utils/data/\_utils/fetch.py”, line 52, in fetch
> return self.collate\_fn(data)
> File „/home/pkedzia/.local/lib/python3.8/site-packages/transformers/data/data\_collator.py”, line 70, in default\_data\_collator
> return torch\_default\_data\_collator(features)
> File „/home/pkedzia/.local/lib/python3.8/site-packages/transformers/data/data\_collator.py”, line 136, in torch\_default\_data\_collator
> batch\[k\] = torch.tensor(\[f\[k\] for f in features\])
> ValueError: expected sequence of length 1024 at dim 1 (got 393)

**Rozwiązanie:** Należy dodać parzystą liczbę workerów w preprocessie, czyli:

```text
--preprocessing_num_workers 2
```
