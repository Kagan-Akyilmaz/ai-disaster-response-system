# 🤖 Otonom AI Agent — Production-Grade

Telegram üzerinden kontrol edilen, hedefleri otomatik planlayan ve
kod üretip çalıştıran modüler AI agent sistemi.

---

## 📁 Proje Yapısı

```
ai_agent/
├── main.py                 ← Giriş noktası
├── config.py               ← Merkezi konfigürasyon
├── state.py                ← Thread-safe durum makinesi
├── ai_client.py            ← OpenAI wrapper + format zorlama
├── planner.py              ← Hedefi görevlere böler
├── worker.py               ← Dosya yazar + komut çalıştırır
├── validator.py            ← Test + Review (birleşik doğrulama)
├── controller.py           ← Ana yürütme motoru (execution engine)
├── telegram_interface.py   ← Telegram bot + komut yönlendirme
├── web_viewer.py           ← Flask log viewer
├── requirements.txt
├── .env.example
└── utils/
    ├── __init__.py
    ├── logger.py           ← RotatingFileHandler tabanlı loglama
    └── helpers.py          ← Yardımcı fonksiyonlar
```

---

## 🚀 Kurulum

### 1. Bağımlılıkları kur
```bash
pip install -r requirements.txt
```

### 2. API anahtarlarını ayarla

`config.py` içinde direkt ayarla veya ortam değişkeni kullan:

```bash
export OPENAI_API_KEY="sk-proj-..."
export TELEGRAM_TOKEN="123456789:AAF..."
```

Ya da `.env` dosyası oluştur ve python-dotenv kullan:
```bash
cp .env.example .env
# .env dosyasını düzenle
pip install python-dotenv
```

Sonra `main.py` başına ekle:
```python
from dotenv import load_dotenv
load_dotenv()
```

### 3. Çalıştır
```bash
python main.py
```

---

## 📱 Telegram Komutları

| Komut | Açıklama |
|-------|----------|
| `/start` | Botu başlat, komutları göster |
| `/hedef <açıklama>` | Yeni proje başlat |
| `/devam` | Duraklatılmış işi devam ettir |
| `/dur` | İşi duraklat |
| `/iptal` | Projeyi iptal et |
| `/durum` | Mevcut durumu göster |
| `/yardim` | Yardım mesajı |

### Örnek kullanım:
```
/hedef Flask ile basit bir REST API yaz, /users endpoint'i olsun
```

---

## 🏗 Mimari

### Veri Akışı

```
Telegram Input
     │
     ▼
telegram_interface.py   ← Komut yönlendirme, chat_id doğrulama
     │
     ▼
controller.py           ← Proje başlatma + görev döngüsü
     │
     ├─► planner.py     ← Hedefi 2-8 adıma böl
     │
     ├─► ai_client.py   ← OpenAI çağrısı, FORMAT zorlama (retry)
     │
     ├─► worker.py      ← Dosya yaz, komut çalıştır (güvenli)
     │
     └─► validator.py   ← Test (hata tespiti) + Fix (otomatik düzeltme) + Review (onay)
          │
          ▼
     state.py           ← Thread-safe durum yönetimi (singleton)
          │
          ▼
     Telegram Output
```

### Güvenlik Katmanları

1. **Komut Engelleme** — `rm -rf`, `format`, `shutdown` vb. engellenir
2. **Timeout** — Her komut max 30 saniye çalışır
3. **Retry Limiti** — AI çağrısı ve komut düzeltme max 5 deneme
4. **Step Limiti** — 30 adım sonra kullanıcı onayı istenir
5. **Path Traversal Koruması** — Dosyalar sadece proje dizinine yazılır
6. **Thread-Safe State** — RLock ile korunan durum nesnesi

### AI Çıktı Formatı (ZORUNLU)

```
FILE: dosyaadi.py
KOD:
<python kodu>
END_FILE

CMD: python dosyaadi.py

AÇIKLAMA: Ne yaptığını anlat
```

Format uyumsuzluğunda `MAX_RETRIES` kadar otomatik yeniden deneme yapılır.

---

## 🌐 Web Panel

Çalışırken `http://localhost:5000` adresinden log viewer'a erişebilirsin.

- Her 10 saniyede otomatik yenilenir
- Son 4000 karakter log gösterilir
- `/api/status` endpoint'i JSON durum döndürür

---

## ⚙️ Konfigürasyon (config.py)

| Değişken | Varsayılan | Açıklama |
|----------|-----------|----------|
| `MODEL` | `gpt-4o-mini` | Kullanılacak OpenAI modeli |
| `STEP_LIMIT` | `30` | Onay olmadan max adım |
| `LOOP_DELAY` | `8` | Adımlar arası bekleme (sn) |
| `MAX_RETRIES` | `5` | Retry limiti |
| `CMD_TIMEOUT` | `30` | Komut timeout (sn) |
