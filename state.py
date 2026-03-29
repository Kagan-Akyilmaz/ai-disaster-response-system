"""
state.py — Merkezi durum yönetimi (State Machine)

Tüm agent durumu burada tutulur. Thread-safe.
"""

import threading
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


class AgentStatus(Enum):
    IDLE          = auto()   # Bekliyor
    PLANNING      = auto()   # Plan oluşturuluyor
    RUNNING       = auto()   # Görev çalışıyor
    WAITING       = auto()   # Kullanıcı onayı bekleniyor
    PAUSED        = auto()   # Duraklatıldı
    FINISHED      = auto()   # Proje bitti
    ERROR         = auto()   # Hata durumu


@dataclass
class AgentState:
    # Proje bilgisi
    goal: str = ""
    project_dir: str = ""

    # Görev kuyruğu
    task_queue: List[str] = field(default_factory=list)
    current_task: str = ""
    completed_tasks: List[str] = field(default_factory=list)

    # Yürütme durumu
    status: AgentStatus = AgentStatus.IDLE
    step_count: int = 0
    last_output: str = ""
    error_count: int = 0

    # Telegram
    chat_id: Optional[int] = None

    # Meta
    started_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class StateManager:
    """Thread-safe durum yöneticisi."""

    def __init__(self):
        self._state = AgentState()
        self._lock = threading.RLock()

    # ── Okuma ────────────────────────────────────────────────────────────────

    @property
    def state(self) -> AgentState:
        with self._lock:
            return self._state

    def get(self, attr: str):
        with self._lock:
            return getattr(self._state, attr)

    # ── Yazma ────────────────────────────────────────────────────────────────

    def set(self, **kwargs):
        with self._lock:
            for k, v in kwargs.items():
                if hasattr(self._state, k):
                    setattr(self._state, k, v)
            self._state.updated_at = datetime.now()

    def set_status(self, status: AgentStatus):
        self.set(status=status)

    # ── Görev kuyruğu ────────────────────────────────────────────────────────

    def init_project(self, goal: str, project_dir: str, tasks: List[str], chat_id: int):
        with self._lock:
            self._state = AgentState(
                goal=goal,
                project_dir=project_dir,
                task_queue=tasks.copy(),
                current_task="",
                status=AgentStatus.PLANNING,
                chat_id=chat_id,
                started_at=datetime.now(),
            )

    def pop_next_task(self) -> Optional[str]:
        with self._lock:
            if self._state.task_queue:
                task = self._state.task_queue.pop(0)
                self._state.current_task = task
                return task
            return None

    def finish_current_task(self):
        with self._lock:
            if self._state.current_task:
                self._state.completed_tasks.append(self._state.current_task)
                self._state.current_task = ""

    def increment_step(self):
        with self._lock:
            self._state.step_count += 1

    def reset_steps(self):
        with self._lock:
            self._state.step_count = 0

    def increment_error(self):
        with self._lock:
            self._state.error_count += 1

    def is_running(self) -> bool:
        return self._state.status == AgentStatus.RUNNING

    def is_idle(self) -> bool:
        return self._state.status in (AgentStatus.IDLE, AgentStatus.FINISHED)

    def has_tasks(self) -> bool:
        with self._lock:
            return bool(self._state.task_queue) or bool(self._state.current_task)

    def summary(self) -> str:
        s = self._state
        done = len(s.completed_tasks)
        total = done + len(s.task_queue) + (1 if s.current_task else 0)
        return (
            f"📊 Durum: {s.status.name}\n"
            f"🎯 Hedef: {s.goal or 'yok'}\n"
            f"✅ Tamamlanan: {done}/{total} görev\n"
            f"🔄 Aktif görev: {s.current_task or 'yok'}\n"
            f"👣 Adım: {s.step_count}"
        )


# Singleton — tüm modüller bunu import eder
agent_state = StateManager()
