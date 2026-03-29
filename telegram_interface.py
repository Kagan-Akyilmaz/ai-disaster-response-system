"""
telegram_interface.py — Telegram bot arayüzü

ÖZELLİKLER:
- chat_id doğrulama
- Güvenli mesaj gönderme (parçalama desteği)
- Komut yönlendirme
- Hata yalıtımı
"""

import telebot
from telebot.types import Message
from typing import Optional

from config import TELEGRAM_TOKEN
from state import agent_state, AgentStatus
from utils import log, friendly, safe_chunks

# ── Bot başlatma ──────────────────────────────────────────────────────────────

bot = telebot.TeleBot(TELEGRAM_TOKEN, threaded=False)

# ── Güvenli mesaj gönderme ────────────────────────────────────────────────────

def send(chat_id: Optional[int], text: str, plain: bool = False) -> bool:
    """
    Telegram'a güvenli mesaj gönderir.

    - chat_id None ise sessizce başarısız olur
    - Uzun mesajları parçalar
    - Hata olursa crash vermez

    Returns:
        True if all chunks sent successfully
    """
    if not chat_id:
        log.warning("[Telegram] chat_id yok, mesaj gönderilemedi.")
        return False

    msg = text if plain else friendly(text)
    all_ok = True

    for chunk in safe_chunks(msg):
        try:
            bot.send_message(chat_id, chunk)
        except Exception as e:
            log.error(f"[Telegram] Mesaj gönderilemedi: {e}")
            all_ok = False

    return all_ok


def send_plain(chat_id: Optional[int], text: str) -> bool:
    """Süslemesiz düz mesaj gönderir."""
    return send(chat_id, text, plain=True)


# ── Yardımcılar ───────────────────────────────────────────────────────────────

def _validate_chat_id(m: Message) -> int:
    """chat_id'yi kaydet ve döndür."""
    cid = m.chat.id
    if not agent_state.get("chat_id"):
        agent_state.set(chat_id=cid)
        log.info(f"[Telegram] chat_id kaydedildi: {cid}")
    return cid


# ── Komut Handler'ları ────────────────────────────────────────────────────────

@bot.message_handler(commands=["start"])
def cmd_start(m: Message):
    cid = _validate_chat_id(m)
    agent_state.set(chat_id=cid)
    send_plain(cid, (
        "👋 Merhaba! Ben otonom AI agent'ın.\n\n"
        "Komutlar:\n"
        "  /hedef <açıklama> — Yeni proje başlat\n"
        "  /devam            — Duraklatılmış işi devam ettir\n"
        "  /dur              — Durdur\n"
        "  /durum            — Mevcut durumu göster\n"
        "  /iptal            — Projeyi iptal et\n"
        "  /yardim           — Bu mesajı göster\n"
    ))


@bot.message_handler(commands=["hedef"])
def cmd_hedef(m: Message):
    """Yeni hedef belirle ve planlamayı başlat."""
    # Import burada — circular import önlemi
    from controller import start_project

    cid = _validate_chat_id(m)

    goal = m.text.replace("/hedef", "", 1).strip()
    if not goal:
        send_plain(cid, "❓ Hedef yaz! Örnek: /hedef Flask ile REST API yaz")
        return

    if agent_state.is_running():
        send_plain(cid, "⚠️ Zaten çalışıyor! Önce /dur veya /iptal kullan.")
        return

    send_plain(cid, f"🎯 Anladım! '{goal}' için plan yapıyorum...")
    start_project(goal, cid)


@bot.message_handler(commands=["devam"])
def cmd_devam(m: Message):
    cid = _validate_chat_id(m)
    status = agent_state.get("status")

    if status == AgentStatus.WAITING:
        agent_state.set(status=AgentStatus.RUNNING)
        agent_state.reset_steps()
        send_plain(cid, "▶️ Devam ediyorum kanka!")
    elif status == AgentStatus.PAUSED:
        agent_state.set(status=AgentStatus.RUNNING)
        send_plain(cid, "▶️ Duraklatma kaldırıldı, çalışıyorum.")
    else:
        send_plain(cid, f"ℹ️ Şu an zaten {status.name} durumundayım.")


@bot.message_handler(commands=["dur"])
def cmd_dur(m: Message):
    cid = _validate_chat_id(m)
    agent_state.set(status=AgentStatus.PAUSED)
    send_plain(cid, "⏸ Duraklattım. Devam için /devam yaz.")


@bot.message_handler(commands=["iptal"])
def cmd_iptal(m: Message):
    cid = _validate_chat_id(m)
    agent_state.set(status=AgentStatus.IDLE, goal="", current_task="", task_queue=[])
    send_plain(cid, "🗑 Proje iptal edildi. Yeni hedef için /hedef yaz.")


@bot.message_handler(commands=["durum"])
def cmd_durum(m: Message):
    cid = _validate_chat_id(m)
    send_plain(cid, agent_state.summary())


@bot.message_handler(commands=["yardim"])
def cmd_yardim(m: Message):
    cmd_start(m)


# ── Genel mesaj handler ───────────────────────────────────────────────────────

@bot.message_handler(func=lambda m: True)
def cmd_genel(m: Message):
    cid = _validate_chat_id(m)
    if not m.text:
        return

    text = m.text.strip()

    # Hedef belirtmeden serbest metin → yardım yönlendir
    if agent_state.is_idle():
        send_plain(cid, (
            "😅 Ne yapmamı istiyorsun tam olarak?\n"
            "Proje başlatmak için: /hedef <ne yapmamı istiyorsun>"
        ))
    else:
        send_plain(cid, "🤔 Komut bekliyor musun? /yardim yaz.")


# ── Bot çalıştırma ────────────────────────────────────────────────────────────

def start_polling():
    """Telegram bot polling döngüsünü başlatır. Thread'de çalıştır."""
    log.info("[Telegram] Bot polling başlıyor...")
    try:
        bot.infinity_polling(timeout=20, long_polling_timeout=15)
    except Exception as e:
        log.error(f"[Telegram] Polling hatası: {e}")
