"""
main.py — Giriş noktası

Başlatma sırası:
  1. Dizinleri oluştur
  2. Agent döngüsünü başlat (controller)
  3. Telegram bot'u başlat
  4. Flask log viewer'ı başlat (bloklayan)
"""

import os
import sys
import threading

from config import PROJECTS_DIR
from utils import log
from controller import start_agent_loop
from telegram_interface import start_polling
from web_viewer import start_web


def bootstrap():
    # Dizin hazırlığı
    os.makedirs(PROJECTS_DIR, exist_ok=True)
    log.info("=" * 60)
    log.info("  AI AGENT başlatılıyor")
    log.info("=" * 60)

    # Agent loop (daemon thread)
    start_agent_loop()

    # Telegram polling (daemon thread)
    tg_thread = threading.Thread(target=start_polling, daemon=True, name="TelegramPolling")
    tg_thread.start()
    log.info("[Main] Telegram bot thread başlatıldı.")

    # Web viewer — ana thread'i bloklar (Ctrl+C ile durur)
    log.info("[Main] Flask log viewer http://localhost:5000 adresinde başlıyor...")
    try:
        start_web(port=5000)
    except KeyboardInterrupt:
        log.info("[Main] Kapatılıyor... (Ctrl+C)")
        sys.exit(0)


if __name__ == "__main__":
    bootstrap()
