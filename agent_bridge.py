"""
agent_bridge.py — Telegram Agent ile Hackathon Harita Sistemi Arasinda Kopru

Calistirma: python agent_bridge.py
Port: 5001

Bu servis:
- Telegram'dan gelen afet komutlarini alir
- Harita sistemine (port 5000) iletir
- Geri bildirimleri Telegram'a gonderir
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import os
import threading
import time
from datetime import datetime

app = Flask(__name__)
CORS(app)

# ── DINAMIK VERİ DEPOSU ──────────────────────────────────────
# Harita sistemi buradan okur
veri = {
    "yeni_afetler": [],      # Telegram'dan eklenen afetler
    "kapali_yollar_ek": [],  # Telegram'dan eklenen kapalı yollar
    "bildirimler": [],        # Son bildirimler
    "son_guncelleme": None,
}

afet_id_sayac = 100  # 35'ten sonra devam et

# ── API ENDPOINTLERİ ─────────────────────────────────────────

@app.route("/api/bridge/durum")
def durum():
    return jsonify({
        "aktif": True,
        "yeni_afet_sayisi": len(veri["yeni_afetler"]),
        "son_guncelleme": veri["son_guncelleme"],
    })

@app.route("/api/bridge/yeni_afetler")
def yeni_afetler():
    return jsonify(veri["yeni_afetler"])

@app.route("/api/bridge/kapali_yollar")
def kapali_yollar():
    return jsonify(veri["kapali_yollar_ek"])

@app.route("/api/bridge/bildirimler")
def bildirimler():
    return jsonify(veri["bildirimler"][-10:])  # Son 10

@app.route("/api/bridge/afet_ekle", methods=["POST"])
def afet_ekle():
    global afet_id_sayac
    d = request.json
    afet_id_sayac += 1

    # Konum tahmini (isim bazlı basit eşleştirme)
    konum_map = {
        "merkez": (37.5750, 36.9220),
        "dulkadiroglu": (37.5930, 36.9510),
        "onikisubat": (37.5680, 36.9580),
        "turkoglu": (37.6100, 36.9060),
        "pazarcik": (37.6380, 37.0150),
        "elbistan": (37.6050, 37.0800),
        "andirin": (37.6700, 36.9200),
        "afsin": (37.5600, 37.1200),
        "goksun": (37.5100, 37.0500),
    }

    isim_lower = d.get("name", "").lower()
    lat, lng = 37.5800, 36.9400  # default merkez
    for anahtar, (la, lo) in konum_map.items():
        if anahtar in isim_lower:
            lat, lng = la, lo
            # Küçük rastgele offset — aynı noktaya çakışmasın
            import random
            lat += random.uniform(-0.005, 0.005)
            lng += random.uniform(-0.005, 0.005)
            break

    siddet = d.get("siddet", "Orta")
    renk_map = {"Kritik": "#B71C1C", "Agir": "#E65100", "Orta": "#F9A825"}

    yeni = {
        "id": afet_id_sayac,
        "lat": lat,
        "lng": lng,
        "name": d.get("name", f"Yeni Afet #{afet_id_sayac}"),
        "siddet": siddet,
        "tip": d.get("tip", "deprem"),
        "mahsur": int(d.get("mahsur", 0)),
        "renk": renk_map.get(siddet, "#F9A825"),
        "arac": d.get("arac", "ambulans"),
        "sicaklik": 0,
        "riskliBina": False,
        "kaynak": "telegram",
        "zaman": datetime.now().strftime("%H:%M:%S"),
    }

    veri["yeni_afetler"].append(yeni)
    veri["son_guncelleme"] = datetime.now().isoformat()

    bildirim_ekle(f"Yeni afet eklendi: {yeni['name']} ({yeni['siddet']})")

    return jsonify({"basarili": True, "afet": yeni})

@app.route("/api/bridge/kapali_ekle", methods=["POST"])
def kapali_ekle():
    d = request.json
    veri["kapali_yollar_ek"].append({
        "a": d.get("a", {"lat": 37.5800, "lng": 36.9300}),
        "b": d.get("b", {"lat": 37.5820, "lng": 36.9400}),
        "neden": d.get("neden", "Engel"),
        "zaman": datetime.now().strftime("%H:%M:%S"),
    })
    veri["son_guncelleme"] = datetime.now().isoformat()
    bildirim_ekle(f"Kapali yol eklendi: {d.get('neden','Engel')}")
    return jsonify({"basarili": True})

@app.route("/api/bridge/temizle", methods=["POST"])
def temizle():
    veri["yeni_afetler"] = []
    veri["kapali_yollar_ek"] = []
    veri["bildirimler"] = []
    return jsonify({"basarili": True})

def bildirim_ekle(mesaj):
    veri["bildirimler"].append({
        "mesaj": mesaj,
        "zaman": datetime.now().strftime("%H:%M:%S")
    })

if __name__ == "__main__":
    print("=" * 50)
    print("  AGENT KOPRUSU - Port 5001")
    print("=" * 50)
    app.run(host="0.0.0.0", port=5001, debug=False)
