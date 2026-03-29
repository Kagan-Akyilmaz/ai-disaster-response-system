# 📡 AfeRota — Kahramanmaraş Afet Koordinasyon Sistemi

> **TUA Astro Hackathon 2026 | Samsun Ondokuz Mayıs Üniversitesi | 28-29 Mart**

**AfeRota**, afet anında kurtarma ekiplerini en hızlı ve en güvenli şekilde afet bölgelerine yönlendiren, yapay zeka destekli gerçek zamanlı bir koordinasyon sistemidir.

---

## 🚀 Özellikler

### 🗺️ Harita Sistemi
- 35 afet bölgesi Kahramanmaraş geneline yayılmış, numaralı pinler
- 6 koordinasyon merkezi (AFAD, Kızılay, AKUT) kare ikonlar
- OpenStreetMap + Esri uydu görüntüsü toggle

### 🛣️ Akıllı Rota Sistemi
- **Merkez → Afet → Merkez** rota mantığı (gidiş kalın, dönüş kesik çizgi)
- OSRM ile gerçek yol rotası
- Kapalı yol algılama → otomatik alternatif rota
- Her rota üzerinde km ve dakika etiketi
- Her merkez için ayrı "Hesapla" butonu

### 🤖 AI Öncelik Motoru
- Mahsur sayısı × Şiddet × Afet tipi × Isı sinyali formülü
- En kritik 10 afeti Türkçe sebep açıklamasıyla sıralar
- Otomatik harita zoom'u

### 📡 Gerçek Veri Modu
- **SIM / GERÇEK** toggle butonu
- AFAD Deprem API + Kandilli Rasathanesi entegrasyonu
- Son 24 saatin depremlerini Türkiye genelinde gösterir
- Nominatim ile tıklanan noktanın gerçek Türkçe adresi
- 81 il AFAD müdürlüğü, 30 il Kızılay şubesi, 8 AKUT bölge ekibi

### 📱 Telegram Entegrasyonu
Saha görevlisi telefondan komut yazar → harita 5 saniyede güncellenir

| Komut | Açıklama |
|-------|----------|
| `/liste` | Tüm aktif afet bölgelerini göster |
| `/kritikler` | Sadece kritik bölgeler |
| `/ozet` | Genel istatistik |
| `/merkez afad1` | Merkez görevleri |
| `/cikar 1` | Bölge çıkar, liste kayar |
| `/cikar 1 5 12` | Çoklu çıkarma |
| `/tamamlandi 3` | Kurtarma bitti |
| `/ekip_gonder 5 afad1` | Ekip gönderildi |
| `/durum_guncelle 1 mahsur 20` | Mahsur güncelle |
| `/afet isim 30 Kritik` | Yeni afet ekle |
| `/sifirla` | 35 afete döndür |

### 🏥 Altyapı Katmanları
- Hastaneler (OpenStreetMap Overpass API)
- Helikopter iniş alanları
- İtfaiye istasyonları
- Akaryakıt istasyonları
- Güvenli toplanma alanları (kapasite bilgisi)

### 🔬 Analiz Katmanları
- Isı haritası (enkaz altı canlı ısı sinyalleri)
- Siamese Net analizi (önce/sonra hasar tespiti)
- Afet yoğunluk haritası (risk skoru renk skalası)
- Riskli binalar
- Kapalı yollar (OSRM ile gerçek sokak)
- Trafik yoğunluk haritası

---

## 🛠️ Kurulum

### Gereksinimler
```
Python 3.8+
Flask
requests
pyTelegramBotAPI
```

### Kurulum Adımları

```bash
# 1. Repoyu klonla
git clone https://github.com/kullanici-adi/aferota.git
cd aferota

# 2. Bağımlılıkları yükle
pip install flask requests pyTelegramBotAPI flask-cors

# 3. Telegram token'ı ekle
# telegram_hackathon.py dosyasını aç, TELEGRAM_TOKEN değişkenini düzenle

# 4. Sistemi başlat
```

### Çalıştırma

**Terminal 1 — Harita:**
```bash
python app.py
```

**Terminal 2 — Telegram Bot:**
```bash
python telegram_hackathon.py
```

Tarayıcıda `localhost:5000` aç.

---

## 📁 Dosya Yapısı

```
aferota/
├── app.py                  # Flask backend, tüm API endpoint'leri
├── telegram_hackathon.py   # Telegram bot komutları
├── agent_bridge.py         # Opsiyonel agent köprüsü (port 5001)
├── afetler.json            # Dinamik afet verisi
├── afetler_backup.json     # Yedek (sıfırlama için)
├── requirements.txt
└── templates/
    └── index.html          # Harita arayüzü
```

---

## 🔌 API Endpoint'leri

| Endpoint | Metod | Açıklama |
|----------|-------|----------|
| `/api/afetler` | GET | Tüm afet bölgeleri |
| `/api/merkezler` | GET | 6 koordinasyon merkezi |
| `/api/atamalar` | GET | Merkez-afet atamaları |
| `/api/afet_cikar/<id>` | POST | Afet sil |
| `/api/afet_ekle` | POST | Yeni afet ekle |
| `/api/afetleri_sifirla` | POST | Yedekten sıfırla |
| `/api/gercek_depremler` | GET | AFAD + Kandilli API |
| `/api/afad_merkezler_tr` | GET | 81 il AFAD koordinatları |
| `/api/kizilay_tr` | GET | 30 il Kızılay şubeleri |
| `/api/akut_tr` | GET | 8 AKUT bölge ekibi |
| `/api/hastaneler` | GET | Hastaneler (OSM) |
| `/api/helikopter` | GET | Helipad noktaları |
| `/api/itfaiye` | GET | İtfaiye istasyonları |
| `/api/akaryakit` | GET | Akaryakıt istasyonları |
| `/api/ai_oncelik` | GET | AI öncelik sıralaması |
| `/api/kapali` | GET | Kapalı yollar |
| `/api/isi` | GET | Isı haritası verisi |
| `/api/riskli` | GET | Riskli binalar |
| `/api/siamese` | GET | Siamese analiz |

---

## 🌍 Veri Kaynakları

| Kaynak | Kullanım | Ücret |
|--------|----------|-------|
| [AFAD Deprem API](https://deprem.afad.gov.tr/apiv2) | Gerçek zamanlı deprem | Ücretsiz |
| [Kandilli Rasathanesi](http://www.koeri.boun.edu.tr) | Deprem fallback | Ücretsiz |
| [OpenStreetMap Overpass](https://overpass-api.de) | Hastane, itfaiye, yakıt | Ücretsiz |
| [Nominatim](https://nominatim.openstreetmap.org) | Adres çözümleme | Ücretsiz |
| [OSRM](https://router.project-osrm.org) | Gerçek yol rotası | Ücretsiz |
| [Esri World Imagery](https://www.esri.com) | Uydu görüntüsü | Ücretsiz |
| [Türksat](https://www.turksat.com.tr) | Uydu altyapısı ve haberleşme desteği | Kurumsal |
| [İMECE Uydusu](https://www.tubitak.gov.tr/imece) | Yüksek çözünürlüklü yerli uydu görüntüsü | RASAT/İMECE |

---

## 🏆 Hackathon

**TUA Astro Hackathon 2026**  
Samsun Ondokuz Mayıs Üniversitesi  
28-29 Mart 2026  
Konu: Uydu görüntüleri + AI ile kurtarma koordinasyonu

---

## 📄 Lisans

MIT License — Özgürce kullanabilirsiniz.
