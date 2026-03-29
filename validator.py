"""
validator.py — Test + Review birleşik doğrulama sistemi

İki aşamalı doğrulama:
  1. Tester  — komut çıktısını analiz eder, hataları tespit eder
  2. Reviewer — AI çıktısının kalitesini değerlendirir
"""

from typing import Tuple

from ai_client import ask_ai, ask_ai_plain, parse_ai_output
from worker import run_command
from config import MAX_RETRIES
from utils import log, is_error_output


# ── TEST ─────────────────────────────────────────────────────────────────────

_TESTER_SYSTEM = """Sen bir kod test uzmanısın.
Sana bir komut ve çıktısı verilecek.
Hata var mı yok mu sadece şunları söyle:
STATUS: OK  veya  STATUS: FAIL
REASON: <kısa neden>
"""

def test_command_output(cmd: str, output: str) -> Tuple[bool, str]:
    """
    Komut çıktısını AI'ya değerlendirir.

    Returns:
        (passed, reason)
    """
    if not is_error_output(output):
        # Hızlı yol: belirgin hata işareti yok
        return True, "Çıktı normal görünüyor"

    prompt = f"Komut: {cmd}\nÇıktı:\n{output}"
    resp = ask_ai_plain(prompt, system=_TESTER_SYSTEM)

    passed = "STATUS: OK" in resp.upper()
    reason = resp.split("REASON:")[-1].strip() if "REASON:" in resp else resp[:200]
    return passed, reason


# ── FIX LOOP ──────────────────────────────────────────────────────────────────

_FIX_SYSTEM = """Sen bir hata ayıklama uzmanısın.
Sana bir komut ve hata çıktısı verilecek.
Hatayı düzelt ve SADECE çalıştırılacak yeni komutu ver (tek satır, başka açıklama yok).
"""

def test_and_fix(cmd: str, project_dir: str) -> Tuple[bool, str]:
    """
    Komutu çalıştırır, hatalıysa otomatik düzeltmeye çalışır.

    Returns:
        (final_success, final_output)
    """
    from worker import run_command as _run

    success, output = _run(cmd, project_dir)
    if success:
        return True, output

    for attempt in range(1, MAX_RETRIES + 1):
        passed, reason = test_command_output(cmd, output)
        if passed:
            log.info(f"[Validator] Test geçti: {reason}")
            return True, output

        log.warning(f"[Validator] Test başarısız (deneme {attempt}): {reason}")

        # Düzeltme isteği
        fix_prompt = f"Komut: {cmd}\nHata:\n{output}\nDüzeltilmiş komut:"
        fixed_cmd, ok = ask_ai(fix_prompt, system=_FIX_SYSTEM, enforce_format=False)

        if not ok or not fixed_cmd.strip():
            log.error("[Validator] Düzeltme önerisi alınamadı.")
            break

        # Yeni komutu temizle (sadece ilk satır)
        fixed_cmd = fixed_cmd.strip().splitlines()[0].strip()
        log.info(f"[Validator] Yeni komut deneniyor: {fixed_cmd!r}")

        success, output = _run(fixed_cmd, project_dir)
        cmd = fixed_cmd  # Sonraki iterasyon için güncelle

        if success:
            return True, output

    return False, output


# ── REVIEW ───────────────────────────────────────────────────────────────────

_REVIEW_SYSTEM = """Sen bir kod review uzmanısın.
Sana bir görevin çıktısı verilecek.
Bu çıktı görevi başarıyla tamamlamış mı?
Sadece şunu yaz: VERDICT: PASS  veya  VERDICT: FAIL
NOTES: <kısa yorum>
"""

def review_output(task: str, output: str) -> Tuple[bool, str]:
    """
    Görev çıktısının kalitesini AI'ya değerlendirir.

    Returns:
        (approved, notes)
    """
    prompt = f"Görev: {task}\nÇıktı:\n{output[:2000]}"
    resp = ask_ai_plain(prompt, system=_REVIEW_SYSTEM)

    approved = "VERDICT: PASS" in resp.upper()
    notes = resp.split("NOTES:")[-1].strip() if "NOTES:" in resp else resp[:200]
    log.info(f"[Reviewer] {'✅ PASS' if approved else '❌ FAIL'}: {notes}")
    return approved, notes
