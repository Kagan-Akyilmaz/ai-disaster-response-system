"""
controller.py — Ana yürütme motoru

Büyük proje desteği için:
- Her adımda mevcut proje dosyalarını okur (proje hafızası)
- AI'ya tam bağlam gönderir (hangi dosyalar var, içerikleri ne)
- Tutarsızlık önlenir
"""

import os
import threading
import time
import traceback

from config import (
    LOOP_DELAY, STEP_LIMIT, PROJECTS_DIR,
    MAX_FILE_CONTEXT, MAX_FILES_IN_CTX
)
from state import agent_state, AgentStatus
from planner import create_plan
from ai_client import ask_ai, parse_ai_output
from worker import execute_parsed_output
from validator import test_and_fix, review_output
from utils import log, make_project_dir


# ── Proje Hafızası ────────────────────────────────────────────────────────────

def _read_project_context(project_dir: str) -> str:
    """
    Proje dizinindeki mevcut dosyaları okur ve AI'ya gönderilecek
    bağlam stringi oluşturur.

    Büyük dosyalar kısaltılır, max MAX_FILES_IN_CTX dosya alınır.
    """
    if not project_dir or not os.path.exists(project_dir):
        return ""

    CODE_EXTENSIONS = {
        ".py", ".js", ".ts", ".html", ".css", ".json",
        ".yaml", ".yml", ".toml", ".txt", ".md", ".env",
        ".sh", ".bat", ".sql",
    }

    files_content = []
    total_chars = 0

    try:
        all_files = []
        for root, dirs, files in os.walk(project_dir):
            # __pycache__, .git gibi dizinleri atla
            dirs[:] = [d for d in dirs if d not in ("__pycache__", ".git", "node_modules", ".venv")]
            for fname in files:
                ext = os.path.splitext(fname)[1].lower()
                if ext in CODE_EXTENSIONS:
                    full_path = os.path.join(root, fname)
                    rel_path = os.path.relpath(full_path, project_dir)
                    all_files.append((rel_path, full_path))

        # En fazla MAX_FILES_IN_CTX dosya al
        for rel_path, full_path in all_files[:MAX_FILES_IN_CTX]:
            try:
                with open(full_path, encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                # Uzun dosyaları kısalt
                if len(content) > MAX_FILE_CONTEXT // max(len(all_files), 1):
                    content = content[:MAX_FILE_CONTEXT // max(len(all_files), 1)] + "\n... (dosya kısaltıldı)"

                files_content.append(f"### {rel_path}\n```\n{content}\n```")
                total_chars += len(content)

                if total_chars >= MAX_FILE_CONTEXT:
                    files_content.append("... (daha fazla dosya var, bağlam limiti aşıldı)")
                    break

            except Exception:
                pass

    except Exception as e:
        log.warning(f"[Controller] Proje bağlamı okunamadı: {e}")
        return ""

    if not files_content:
        return ""

    return (
        f"## MEVCUT PROJE DOSYALARI ({len(files_content)} dosya)\n\n" +
        "\n\n".join(files_content)
    )


# ── Proje Başlatma ────────────────────────────────────────────────────────────

def start_project(goal: str, chat_id: int):
    from telegram_interface import send_plain

    try:
        project_dir = make_project_dir(PROJECTS_DIR, goal)
        tasks = create_plan(goal)

        agent_state.init_project(
            goal=goal,
            project_dir=project_dir,
            tasks=tasks,
            chat_id=chat_id,
        )
        agent_state.set(status=AgentStatus.RUNNING)

        log.info(f"[Controller] Proje başladı: {goal!r}, {len(tasks)} adım")

        plan_text = "\n".join(f"  {i+1}. {t}" for i, t in enumerate(tasks))
        send_plain(chat_id,
            f"📋 Plan hazır! {len(tasks)} adım var:\n\n{plan_text}\n\n🚀 Başlıyorum!")

    except Exception as e:
        log.error(f"[Controller] Proje başlatma hatası: {e}")
        from telegram_interface import send_plain
        send_plain(chat_id, f"❌ Proje başlatılamadı: {e}")


# ── Tek Adım Yürütme ─────────────────────────────────────────────────────────

def _execute_step():
    from telegram_interface import send, send_plain

    state       = agent_state.state
    goal        = state.goal
    project_dir = state.project_dir
    task        = state.current_task
    last_out    = state.last_output
    chat_id     = state.chat_id
    completed   = state.completed_tasks
    pending     = state.task_queue

    if not task:
        task = agent_state.pop_next_task()
        if not task:
            agent_state.set(status=AgentStatus.FINISHED)
            send_plain(chat_id,
                f"🎉 Proje tamamlandı!\n\n"
                f"✅ {len(completed)} görev başarıyla tamamlandı.\n"
                f"📁 Dosyalar: {project_dir}"
            )
            log.info("[Controller] Proje tamamlandı.")
            return

    log.info(f"[Controller] Görev yürütülüyor: {task!r}")

    # ── Proje hafızasını oku ──────────────────────────────────────────────────
    project_context = _read_project_context(project_dir)

    # ── Tamamlanan görevler özeti ──────────────────────────────────────────────
    completed_summary = ""
    if completed:
        completed_summary = "## TAMAMLANAN GÖREVLER\n" + "\n".join(
            f"✅ {t}" for t in completed[-5:]  # Son 5 görevi göster
        )

    # ── Bekleyen görevler ──────────────────────────────────────────────────────
    pending_summary = ""
    if pending:
        pending_summary = "## SONRAKI GÖREVLER\n" + "\n".join(
            f"⏳ {t}" for t in pending[:3]  # İlk 3 bekleyeni göster
        )

    # ── AI'ya gönder ──────────────────────────────────────────────────────────
    prompt = f"""# PROJE BİLGİSİ
**Ana Hedef:** {goal}

{completed_summary}

## AKTİF GÖREV (ŞIMDI YAPILACAK)
{task}

{pending_summary}

{project_context}

## SON ÇIKTI
{last_out[:800] if last_out else 'Yok (ilk adım)'}

---
Aktif görevi tamamla. Mevcut dosyalarla tutarlı ol. ZORUNLU formatı kullan.
"""

    raw_output, ok = ask_ai(prompt)

    if not ok or not raw_output:
        log.error("[Controller] AI'dan çıktı alınamadı.")
        agent_state.increment_error()
        return

    parsed = parse_ai_output(raw_output)

    # ── Çalıştır ──────────────────────────────────────────────────────────────
    result_text = execute_parsed_output(parsed, project_dir)
    log.info(f"[Controller] Çalıştırma sonucu:\n{result_text}")

    # ── CMD test & fix ────────────────────────────────────────────────────────
    if parsed.get("cmd"):
        fix_success, fix_output = test_and_fix(parsed["cmd"], project_dir)
        result_text += f"\n\n🔧 Test: {'✅' if fix_success else '❌'}\n{fix_output}"

    # ── Review ────────────────────────────────────────────────────────────────
    approved, notes = review_output(task, result_text)

    agent_state.set(last_output=result_text)
    agent_state.increment_step()

    # ── Telegram bildir ───────────────────────────────────────────────────────
    done_count = len(completed) + (1 if approved else 0)
    total_count = done_count + len(pending) + (0 if approved else 1)

    report = (
        f"📍 [{done_count}/{total_count}] {task}\n\n"
        f"{result_text[:1500]}\n\n"
        f"{'✅ Onaylandı' if approved else '🔄 Yeniden denenecek'}: {notes}"
    )
    send(chat_id, report)

    if approved:
        log.info(f"[Controller] Görev onaylandı: {task!r}")
        agent_state.finish_current_task()
        agent_state.set(current_task="")
    else:
        log.warning(f"[Controller] Görev onaylanmadı: {notes}")


# ── Ana Döngü ─────────────────────────────────────────────────────────────────

def _agent_loop():
    log.info("[Controller] Agent döngüsü başladı.")

    while True:
        try:
            status = agent_state.get("status")

            if status == AgentStatus.RUNNING:
                step = agent_state.get("step_count")

                if step >= STEP_LIMIT:
                    agent_state.set(status=AgentStatus.WAITING)
                    agent_state.reset_steps()
                    chat_id = agent_state.get("chat_id")
                    from telegram_interface import send_plain
                    send_plain(chat_id,
                        f"⚠️ {STEP_LIMIT} adım tamamlandı, onay bekliyorum.\n"
                        "  /devam → devam et\n"
                        "  /dur   → durdur"
                    )
                else:
                    _execute_step()

            elif status in (AgentStatus.FINISHED, AgentStatus.IDLE):
                time.sleep(LOOP_DELAY * 2)

            time.sleep(LOOP_DELAY)

        except Exception:
            log.error(f"[Controller] Döngü hatası:\n{traceback.format_exc()}")
            time.sleep(LOOP_DELAY)


def start_agent_loop():
    t = threading.Thread(target=_agent_loop, daemon=True, name="AgentLoop")
    t.start()
    log.info("[Controller] Agent loop thread başlatıldı.")
    return t
