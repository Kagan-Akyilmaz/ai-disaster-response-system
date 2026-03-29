"""
planner.py — Akıllı modüler planlama sistemi

Büyük projeler için:
- Önce projeyi modüllere böler
- Her modülü ayrı görev olarak planlar
- Bağımlılık sırasına dikkat eder
- Gereksiz adımları filtreler
"""

import re
from typing import List

from ai_client import ask_ai_plain
from utils import log

# ── Proje büyüklüğü tespiti ───────────────────────────────────────────────────

def _estimate_complexity(goal: str) -> str:
    """Hedefin karmaşıklık seviyesini tahmin eder."""
    big_keywords = [
        "sistem", "platform", "uygulama", "site", "api", "backend",
        "frontend", "veritabanı", "authentication", "dashboard",
        "e-ticaret", "blog", "forum", "chat", "microservice"
    ]
    goal_lower = goal.lower()
    matches = sum(1 for kw in big_keywords if kw in goal_lower)
    return "large" if matches >= 2 else "small"


# ── Küçük proje planlaması ────────────────────────────────────────────────────

_SIMPLE_PLANNER_SYSTEM = """Sen bir yazılım proje planlamacısısın.

Sana bir hedef verilecek. Bu hedefi somut, yürütülebilir adımlara böleceksin.

KURALLAR:
- En fazla 6 adım yaz.
- Her adım kendi başına çalıştırılabilir bir iş olmalı.
- "Araştır", "Düşün", "Planla" gibi soyut adımlar yazma.
- Python ortamının kurulu olduğunu varsay.
- Sadece numaralı liste: "1. ..." formatında yaz.
- Türkçe yaz.
"""

# ── Büyük proje planlaması ────────────────────────────────────────────────────

_LARGE_PLANNER_SYSTEM = """Sen kıdemli bir yazılım mimarısın.

Sana büyük bir proje hedefi verilecek. Bunu önce modüllere böl, sonra her modül için somut adımlar oluştur.

KURALLAR:
- Maksimum 10 adım yaz (büyük projede bile).
- Her adım tek bir dosya veya tek bir işlev grubu olmalı.
- Adımları bağımlılık sırasına göre yaz (önce temel, sonra üst katman).
- Şu sırayı takip et: config/models → database → core logic → API/routes → tests
- "Araştır", "Planla", "İncele" gibi soyut adımlar YAZMA.
- Her adım "X dosyasını oluştur" veya "X fonksiyonunu yaz" şeklinde somut olsun.
- Numaralı liste: "1. ..." formatında yaz.
- Türkçe yaz.

ÖRNEK ÇIKTI (Flask API için):
1. Proje yapısını ve config.py dosyasını oluştur
2. Veritabanı modellerini yaz (models.py)
3. Veritabanı bağlantısını kur (database.py)
4. Kullanıcı kimlik doğrulama fonksiyonlarını yaz (auth.py)
5. API route'larını oluştur (routes.py)
6. Ana uygulama dosyasını yaz (app.py)
7. Uygulamayı test et ve çalıştır
"""


def create_plan(goal: str) -> List[str]:
    """
    Hedefe göre akıllı plan oluşturur.
    Büyük projeler için modüler planlama yapar.
    """
    complexity = _estimate_complexity(goal)
    log.info(f"[Planner] Karmaşıklık seviyesi: {complexity} — Hedef: {goal!r}")

    if complexity == "large":
        system = _LARGE_PLANNER_SYSTEM
        log.info("[Planner] Büyük proje modu — modüler planlama yapılıyor...")
    else:
        system = _SIMPLE_PLANNER_SYSTEM

    response = ask_ai_plain(f"Hedef: {goal}", system=system)
    tasks = _parse_tasks(response)

    if not tasks:
        log.warning("[Planner] Plan alınamadı, fallback kullanılıyor.")
        tasks = _fallback_plan(goal)

    log.info(f"[Planner] {len(tasks)} adım oluşturuldu:\n" +
             "\n".join(f"  {i+1}. {t}" for i, t in enumerate(tasks)))
    return tasks


def _parse_tasks(text: str) -> List[str]:
    tasks = []
    for line in text.split("\n"):
        line = line.strip()
        match = re.match(r"^\d+[\.\)]\s+(.+)$", line)
        if match:
            task = match.group(1).strip()
            if task and len(task) > 3:
                tasks.append(task)
    return tasks


def _fallback_plan(goal: str) -> List[str]:
    return [
        f"Projenin ana dosyasını oluştur: {goal}",
        "Kodu test et ve çalıştır",
    ]
