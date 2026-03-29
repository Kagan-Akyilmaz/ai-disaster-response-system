"""
worker.py — Dosya yazma ve komut yürütme işlemleri
"""

import os
import re
import subprocess
from typing import Tuple

from config import BLOCKED_COMMANDS, CMD_TIMEOUT
from utils import log, sanitize_filename, is_error_output


# ── Dosya Yazma ───────────────────────────────────────────────────────────────

def write_file(project_dir: str, filename: str, content: str) -> Tuple[bool, str]:
    """
    Proje dizinine dosya yazar.

    Returns:
        (success, message)
    """
    try:
        filename = sanitize_filename(filename)

        # Alt dizinlere izin ver (örn: src/main.py) ama proje dışına çıkamaz
        target = os.path.realpath(os.path.join(project_dir, filename))
        project_real = os.path.realpath(project_dir)
        if not target.startswith(project_real):
            return False, f"❌ Güvenlik: proje dışına dosya yazılamaz: {filename}"

        os.makedirs(os.path.dirname(target), exist_ok=True)

        with open(target, "w", encoding="utf-8") as f:
            f.write(content.strip())

        log.info(f"[Worker] Dosya yazıldı: {filename}")
        return True, f"✔ {filename} yazıldı"

    except Exception as e:
        log.error(f"[Worker] Dosya yazma hatası: {e}")
        return False, f"❌ Dosya hatası: {e}"


# ── Komut Güvenlik Kontrolü ───────────────────────────────────────────────────

def _is_safe_command(cmd: str) -> Tuple[bool, str]:
    """
    Komutun güvenli olup olmadığını kontrol eder.

    Returns:
        (is_safe, reason)
    """
    cmd_lower = cmd.lower().strip()

    for blocked in BLOCKED_COMMANDS:
        if blocked in cmd_lower:
            return False, f"Engellendi: '{blocked}' ifadesi içeriyor"

    # Mutlak yol yazma girişimleri
    if re.search(r">\s*/(?!dev/null)", cmd):
        
        return False, "Engellendi: kök dizine yazma girişimi"

    return True, ""


# ── Komut Yürütme ────────────────────────────────────────────────────────────

def run_command(cmd: str, project_dir: str) -> Tuple[bool, str]:
    """
    Komutu güvenli şekilde çalıştırır.

    Returns:
        (success, output)
    """
    import re

    cmd = cmd.strip()
    if not cmd:
        return False, "❌ Boş komut"

    safe, reason = _is_safe_command(cmd)
    if not safe:
        log.warning(f"[Worker] Komut engellendi: {reason}")
        return False, f"⚠️ Riskli komut engellendi. Neden: {reason}"

    try:
        log.info(f"[Worker] Komut çalıştırılıyor: {cmd!r}")
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            cwd=project_dir,
            timeout=CMD_TIMEOUT,
        )
        output = (result.stdout + result.stderr).strip()
        success = result.returncode == 0
        log.info(f"[Worker] Komut çıktısı (rc={result.returncode}): {output[:200]}")
        return success, output or "(çıktı yok)"

    except subprocess.TimeoutExpired:
        log.error(f"[Worker] Komut timeout: {cmd}")
        return False, f"❌ Komut {CMD_TIMEOUT}s içinde tamamlanamadı (timeout)"

    except Exception as e:
        log.error(f"[Worker] Komut hatası: {e}")
        return False, f"❌ Komut hatası: {e}"


# ── Sonuç Raporu ─────────────────────────────────────────────────────────────

def execute_parsed_output(parsed: dict, project_dir: str) -> str:
    """
    parse_ai_output() çıktısını uygular: dosyaları yazar, komutu çalıştırır.

    Returns:
        İnsan okunabilir sonuç özeti
    """
    lines = []

    # Dosya yazma
    for f in parsed.get("files", []):
        ok, msg = write_file(project_dir, f["name"], f["code"])
        lines.append(msg)

    # Komut çalıştırma
    cmd = parsed.get("cmd")
    if cmd:
        ok, output = run_command(cmd, project_dir)
        status = "✔" if ok else "❌"
        lines.append(f"{status} CMD: {cmd}\n{output}")

    # Açıklama
    exp = parsed.get("explanation", "")
    if exp:
        lines.append(f"💬 {exp}")

    return "\n".join(lines) if lines else "ℹ️ İşlem yapılmadı"
