---
title: "[Q&A] Uczenie GPU/CPU"
date: 2022-12-19
updated: 2024-04-27
slug: qa-uczenie-gpu-cpu
description: "Q: Jak uruchomić uczenie/inferencję na wybranych GPU? A: Należy uruchomić program z opcją: gdzie 0 i 1 to numery kart graficznych do rozproszonego obliczenia.…"
tags: ["cuda", "nvlink", "uczenie"]
categories: ["narzędzia", "Q&A", "transformatory"]
image: media/qa-uczenie-gpu-cpu/_featured.png
lang: pl
wp_id: 2099
---

**Q: Jak uruchomić uczenie/inferencję na wybranych GPU?**

**A:** Należy uruchomić program z opcją:

```text
CUDA_VISIBLE_DEVICES=0,1
```

gdzie *0* i *1* to numery kart graficznych do rozproszonego obliczenia.

**Q: Jak włączyć/wyłączyć obsługę NVX dla połączonych kart graficznych mostkiem NVLink?**

**A:** Przy połączonych kartach GPU obsługa NVlink w transformersach jest domyślnie uruchomiona. Aby wyłączyć obsługę NVX dla kart należy dodać do wywołania programu opcję

```text
NCCL_P2P_DISABLE=1
```
