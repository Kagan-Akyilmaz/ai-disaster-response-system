from flask import Flask, render_template, jsonify, request
import json, math, os, shutil

app = Flask(__name__)
AFET_DOSYA = os.path.join(os.path.dirname(__file__), "afetler.json")
AFET_YEDEK = os.path.join(os.path.dirname(__file__), "afetler_backup.json")

def afetleri_oku():
    with open(AFET_DOSYA, "r", encoding="utf-8") as f:
        return json.load(f)

def afetleri_yaz(liste):
    with open(AFET_DOSYA, "w", encoding="utf-8") as f:
        json.dump(liste, f, ensure_ascii=False, indent=2)

MERKEZLER = [
    {"id":"afad1","lat":37.5858,"lng":36.9371,"name":"AFAD Merkez-1","tip":"AFAD","renk":"#1565C0","ekip":"Ambulans, UMKE"},
    {"id":"afad2","lat":37.6050,"lng":36.9150,"name":"AFAD Merkez-2","tip":"AFAD","renk":"#0D47A1","ekip":"Ambulans, Vinc"},
    {"id":"kizilay1","lat":37.5650,"lng":36.9050,"name":"Kizilay-1","tip":"Kizilay","renk":"#B71C1C","ekip":"Motosiklet, Tibbi"},
    {"id":"kizilay2","lat":37.5750,"lng":37.0100,"name":"Kizilay-2","tip":"Kizilay","renk":"#C62828","ekip":"Ambulans, Tibbi"},
    {"id":"akut1","lat":37.5500,"lng":36.9400,"name":"AKUT Timi-1","tip":"AKUT","renk":"#1B5E20","ekip":"Arazi, Drone"},
    {"id":"akut2","lat":37.6200,"lng":36.9700,"name":"AKUT Timi-2","tip":"AKUT","renk":"#2E7D32","ekip":"Drone, IHA"},
]

KAPALI_YOLLAR = [
    {"a":{"lat":37.5780,"lng":36.9180},"b":{"lat":37.5760,"lng":36.9300},"neden":"Enkaz"},
    {"a":{"lat":37.5900,"lng":36.9420},"b":{"lat":37.5960,"lng":36.9560},"neden":"Sel"},
    {"a":{"lat":37.5640,"lng":36.9550},"b":{"lat":37.5710,"lng":36.9650},"neden":"Yangin"},
    {"a":{"lat":37.6090,"lng":36.8980},"b":{"lat":37.6120,"lng":36.9130},"neden":"Kopru"},
    {"a":{"lat":37.5980,"lng":36.9700},"b":{"lat":37.6020,"lng":36.9880},"neden":"Enkaz"},
    {"a":{"lat":37.5520,"lng":36.9080},"b":{"lat":37.5570,"lng":36.9200},"neden":"Yangin"},
    {"a":{"lat":37.6100,"lng":37.0000},"b":{"lat":37.6150,"lng":37.0180},"neden":"Yikildi"},
    {"a":{"lat":37.5360,"lng":36.9520},"b":{"lat":37.5420,"lng":36.9680},"neden":"Heyelan"},
    {"a":{"lat":37.6200,"lng":36.9380},"b":{"lat":37.6260,"lng":36.9530},"neden":"Yangin"},
    {"a":{"lat":37.5600,"lng":37.0100},"b":{"lat":37.5650,"lng":37.0280},"neden":"Enkaz"},
    {"a":{"lat":37.5830,"lng":36.9570},"b":{"lat":37.5900,"lng":36.9750},"neden":"Enkaz"},
    {"a":{"lat":37.5460,"lng":37.0080},"b":{"lat":37.5520,"lng":37.0240},"neden":"Sel"},
    {"a":{"lat":37.5700,"lng":36.8950},"b":{"lat":37.5760,"lng":36.9070},"neden":"Yangin"},
    {"a":{"lat":37.6130,"lng":36.9480},"b":{"lat":37.6190,"lng":36.9640},"neden":"Kopru"},
    {"a":{"lat":37.5850,"lng":36.9870},"b":{"lat":37.5920,"lng":37.0020},"neden":"Heyelan"},
]

def mesafe(lat1,lng1,lat2,lng2):
    R=6371
    dlat=math.radians(lat2-lat1); dlng=math.radians(lng2-lng1)
    a=math.sin(dlat/2)**2+math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dlng/2)**2
    return R*2*math.atan2(math.sqrt(a),math.sqrt(1-a))

def en_yakin_merkez(afet):
    tip_pref={"deprem":["AFAD","AKUT","Kizilay"],"yangin":["AKUT","AFAD","Kizilay"],"sel":["AFAD","Kizilay","AKUT"],"heyelan":["AKUT","AFAD","Kizilay"]}
    pref=tip_pref.get(afet["tip"],["AFAD"])
    en=None; sk=float('inf')
    for m in MERKEZLER:
        d=mesafe(afet["lat"],afet["lng"],m["lat"],m["lng"])
        b=pref.index(m["tip"])*1.5 if m["tip"] in pref else 8
        if d+b<sk: sk=d+b; en=m
    return en

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/merkezler")
def api_merkezler():
    return jsonify(MERKEZLER)

@app.route("/api/afetler")
def api_afetler():
    return jsonify(afetleri_oku())

@app.route("/api/afet_sayisi")
def api_afet_sayisi():
    return jsonify({"sayi": len(afetleri_oku())})

@app.route("/api/atamalar")
def api_atamalar():
    afetler=afetleri_oku()
    sonuc=[]
    for a in sorted(afetler,key=lambda x:x["id"]):
        m=en_yakin_merkez(a)
        d=mesafe(a["lat"],a["lng"],m["lat"],m["lng"])
        sonuc.append({
            "afet_id":a["id"],"afet_name":a["name"],
            "afet_lat":a["lat"],"afet_lng":a["lng"],
            "afet_renk":a["renk"],"siddet":a["siddet"],
            "tip":a["tip"],"mahsur":a["mahsur"],"arac":a["arac"],
            "merkez_id":m["id"],"merkez_name":m["name"],
            "merkez_tip":m["tip"],"merkez_renk":m["renk"],
            "merkez_lat":m["lat"],"merkez_lng":m["lng"],
            "mesafe_km":round(d,1),"sure_dk":round(d/40*60)
        })
    return jsonify(sonuc)

# ── DİNAMİK GÜNCELLEME ───────────────────────────────────────

@app.route("/api/afet_cikar/<int:afet_id>", methods=["POST"])
def afet_cikar(afet_id):
    afetler=afetleri_oku()
    onceki=len(afetler)
    cikarilan=next((a for a in afetler if a["id"]==afet_id),None)
    afetler=[a for a in afetler if a["id"]!=afet_id]
    if len(afetler)==onceki:
        return jsonify({"basarili":False,"mesaj":f"#{afet_id} bulunamadi"}),404
    afetleri_yaz(afetler)
    return jsonify({
        "basarili":True,
        "cikarilan":cikarilan,
        "kalan":len(afetler),
        "mesaj":f"#{afet_id} cikarildi, {len(afetler)} bolge kaldi"
    })

@app.route("/api/afet_ekle", methods=["POST"])
def afet_ekle():
    afetler=afetleri_oku()
    d=request.json
    yeni_id=max((a["id"] for a in afetler),default=0)+1
    siddet=d.get("siddet","Orta")
    renk={"Kritik":"#B71C1C","Agir":"#E65100","Orta":"#F9A825"}.get(siddet,"#F9A825")
    import random
    yeni={
        "id":yeni_id,
        "lat":float(d.get("lat",37.5750+random.uniform(-0.05,0.05))),
        "lng":float(d.get("lng",36.9400+random.uniform(-0.05,0.05))),
        "name":d.get("name",f"Yeni Afet #{yeni_id}"),
        "siddet":siddet,"tip":d.get("tip","deprem"),
        "mahsur":int(d.get("mahsur",0)),"renk":renk,
        "arac":d.get("arac","ambulans"),"sicaklik":0,"riskliBina":False,
    }
    afetler.append(yeni)
    afetleri_yaz(afetler)
    return jsonify({"basarili":True,"afet":yeni})

@app.route("/api/afetleri_sifirla", methods=["POST"])
def afetleri_sifirla():
    if os.path.exists(AFET_YEDEK):
        shutil.copy(AFET_YEDEK,AFET_DOSYA)
        return jsonify({"basarili":True,"mesaj":"Tum afetler sifirlandi"})
    return jsonify({"basarili":False,"mesaj":"Yedek bulunamadi"})

@app.route("/api/kapali")
def api_kapali():
    return jsonify(KAPALI_YOLLAR)

@app.route("/api/isi")
def api_isi():
    return jsonify([[a["lat"],a["lng"],min(0.95,0.35+a["mahsur"]/100)] for a in afetleri_oku() if a["mahsur"]>0])

@app.route("/api/riskli")
def api_riskli():
    return jsonify([
        {"lat":37.5748,"lng":36.9222,"risk":"Yuksek","ac":"Egim riski","renk":"#E65100"},
        {"lat":37.5782,"lng":36.9290,"risk":"Yuksek","ac":"Dis duvar hasarli","renk":"#E65100"},
        {"lat":37.5820,"lng":36.9140,"risk":"Yuksek","ac":"Zemin kaymasi","renk":"#E65100"},
        {"lat":37.6105,"lng":36.9060,"risk":"Yuksek","ac":"Agir hasar","renk":"#E65100"},
        {"lat":37.5682,"lng":36.9580,"risk":"Orta","ac":"Yapisal catlakar","renk":"#FBC02D"},
        {"lat":37.5840,"lng":36.9430,"risk":"Orta","ac":"Zemin cokme riski","renk":"#FBC02D"},
    ])

@app.route("/api/siamese")
def api_siamese():
    return jsonify([
        {"lat":37.5750,"lng":36.9220,"hasar":90,"tip":"cokus","renk":"#B71C1C"},
        {"lat":37.5780,"lng":36.9290,"hasar":85,"tip":"enkaz","renk":"#C62828"},
        {"lat":37.5980,"lng":36.9750,"hasar":88,"tip":"cokus","renk":"#B71C1C"},
        {"lat":37.5930,"lng":36.9510,"hasar":60,"tip":"sel","renk":"#1565C0"},
        {"lat":37.5550,"lng":36.9100,"hasar":70,"tip":"yangin","renk":"#E65100"},
    ])

@app.route("/api/bridge_durum")
def api_bridge_durum():
    try:
        import requests as req
        r=req.get("http://localhost:5001/api/bridge/durum",timeout=2)
        return jsonify({"aktif":True,**r.json()})
    except:
        return jsonify({"aktif":False})

@app.route("/api/bridge_afetler")
def api_bridge_afetler():
    try:
        import requests as req
        r=req.get("http://localhost:5001/api/bridge/yeni_afetler",timeout=2)
        return jsonify(r.json())
    except:
        return jsonify([])


@app.route("/api/gercek_depremler")
def api_gercek_depremler():
    """AFAD API'den gercek deprem verilerini cek."""
    try:
        import requests as req
        from datetime import datetime, timedelta

        # Son 24 saatin depremleri
        bitis = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        baslangic = (datetime.utcnow() - timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")

        url = "https://deprem.afad.gov.tr/apiv2/event/filter"
        params = {
            "start": baslangic,
            "end": bitis,
            "minmag": 2.0,
            "orderby": "timedesc",
            "limit": 50,
        }
        r = req.get(url, params=params, timeout=10)
        veriler = r.json()

        afetler = []
        for i, d in enumerate(veriler):
            mag = float(d.get("magnitude", 0))
            if mag < 2.0:
                continue

            # Büyüklüğe göre şiddet
            if mag >= 5.0:
                siddet = "Kritik"
                renk = "#B71C1C"
                mahsur = int((mag - 4) * 30)
            elif mag >= 4.0:
                siddet = "Agir"
                renk = "#E65100"
                mahsur = int((mag - 3) * 10)
            else:
                siddet = "Orta"
                renk = "#F9A825"
                mahsur = 0

            il = d.get("location", "Bilinmiyor").split("-")[-1].strip()
            afetler.append({
                "id": 1000 + i,
                "lat": float(d.get("latitude", 39.0)),
                "lng": float(d.get("longitude", 35.0)),
                "name": f"{il} — M{mag:.1f} Deprem",
                "siddet": siddet,
                "tip": "deprem",
                "mahsur": mahsur,
                "renk": renk,
                "arac": "ambulans" if siddet == "Kritik" else "drone",
                "sicaklik": 0,
                "riskliBina": mag >= 4.5,
                "buyukluk": mag,
                "zaman": d.get("date", ""),
                "derinlik": d.get("depth", 0),
            })

        return jsonify({
            "basarili": True,
            "sayi": len(afetler),
            "afetler": afetler,
            "kaynak": "AFAD API",
            "guncelleme": datetime.utcnow().strftime("%H:%M:%S UTC")
        })

    except Exception as e:
        # AFAD API erişilemezse Kandilli dene
        try:
            import requests as req
            r = req.get(
                "http://www.koeri.boun.edu.tr/scripts/lst0.asp",
                timeout=8
            )
            # Ham veriyi parse et
            satirlar = r.text.split("\n")
            afetler = []
            for i, satir in enumerate(satirlar):
                parcalar = satir.split()
                if len(parcalar) < 7:
                    continue
                try:
                    lat = float(parcalar[2])
                    lng = float(parcalar[3])
                    mag = float(parcalar[6])
                    if mag < 2.0 or not (35 < lat < 43) or not (25 < lng < 45):
                        continue
                    siddet = "Kritik" if mag >= 5 else "Agir" if mag >= 4 else "Orta"
                    renk = {"Kritik":"#B71C1C","Agir":"#E65100","Orta":"#F9A825"}[siddet]
                    konum = " ".join(parcalar[8:]) if len(parcalar) > 8 else "Turkiye"
                    afetler.append({
                        "id": 1000+i, "lat": lat, "lng": lng,
                        "name": f"{konum[:30]} — M{mag:.1f}",
                        "siddet": siddet, "tip": "deprem",
                        "mahsur": int(max(0,(mag-3)*8)),
                        "renk": renk, "arac": "ambulans",
                        "sicaklik": 0, "riskliBina": mag >= 4.5,
                        "buyukluk": mag,
                    })
                    if len(afetler) >= 30:
                        break
                except:
                    continue
            return jsonify({
                "basarili": True,
                "sayi": len(afetler),
                "afetler": afetler,
                "kaynak": "Kandilli Rasathanesi",
                "guncelleme": ""
            })
        except Exception as e2:
            return jsonify({"basarili": False, "hata": str(e2), "afetler": []})


# ── 81 İL AFAD MERKEZLERİ ────────────────────────────────────
@app.route("/api/afad_merkezler_tr")
def api_afad_merkezler_tr():
    merkezler = [
        {"il":"Adana","lat":37.0000,"lng":35.3213},{"il":"Adiyaman","lat":37.7648,"lng":38.2786},
        {"il":"Afyonkarahisar","lat":38.7507,"lng":30.5567},{"il":"Agri","lat":39.7191,"lng":43.0503},
        {"il":"Amasya","lat":40.6499,"lng":35.8353},{"il":"Ankara","lat":39.9208,"lng":32.8541},
        {"il":"Antalya","lat":36.8969,"lng":30.7133},{"il":"Artvin","lat":41.1828,"lng":41.8183},
        {"il":"Aydin","lat":37.8444,"lng":27.8458},{"il":"Balikesir","lat":39.6484,"lng":27.8826},
        {"il":"Bilecik","lat":40.1506,"lng":29.9792},{"il":"Bingol","lat":38.8854,"lng":40.4983},
        {"il":"Bitlis","lat":38.4006,"lng":42.1095},{"il":"Bolu","lat":40.7359,"lng":31.6061},
        {"il":"Burdur","lat":37.7204,"lng":30.2886},{"il":"Bursa","lat":40.1826,"lng":29.0665},
        {"il":"Canakkale","lat":40.1553,"lng":26.4142},{"il":"Cankiri","lat":40.6013,"lng":33.6134},
        {"il":"Corum","lat":40.5506,"lng":34.9556},{"il":"Denizli","lat":37.7765,"lng":29.0864},
        {"il":"Diyarbakir","lat":37.9144,"lng":40.2306},{"il":"Edirne","lat":41.6818,"lng":26.5623},
        {"il":"Elazig","lat":38.6748,"lng":39.2226},{"il":"Erzincan","lat":39.7500,"lng":39.5000},
        {"il":"Erzurum","lat":39.9000,"lng":41.2700},{"il":"Eskisehir","lat":39.7767,"lng":30.5206},
        {"il":"Gaziantep","lat":37.0662,"lng":37.3833},{"il":"Giresun","lat":40.9128,"lng":38.3895},
        {"il":"Gumushane","lat":40.4386,"lng":39.4814},{"il":"Hakkari","lat":37.5744,"lng":43.7408},
        {"il":"Hatay","lat":36.4018,"lng":36.3498},{"il":"Isparta","lat":37.7648,"lng":30.5566},
        {"il":"Mersin","lat":36.8000,"lng":34.6333},{"il":"Istanbul","lat":41.0082,"lng":28.9784},
        {"il":"Izmir","lat":38.4189,"lng":27.1287},{"il":"Kars","lat":40.6013,"lng":43.0975},
        {"il":"Kastamonu","lat":41.3887,"lng":33.7827},{"il":"Kayseri","lat":38.7312,"lng":35.4787},
        {"il":"Kirklareli","lat":41.7333,"lng":27.2167},{"il":"Kirsehir","lat":39.1425,"lng":34.1709},
        {"il":"Kocaeli","lat":40.8533,"lng":29.8815},{"il":"Konya","lat":37.8714,"lng":32.4846},
        {"il":"Kutahya","lat":39.4167,"lng":29.9833},{"il":"Malatya","lat":38.3552,"lng":38.3095},
        {"il":"Manisa","lat":38.6191,"lng":27.4289},{"il":"Kahramanmaras","lat":37.5858,"lng":36.9371},
        {"il":"Mardin","lat":37.3212,"lng":40.7245},{"il":"Mugla","lat":37.2153,"lng":28.3636},
        {"il":"Mus","lat":38.9462,"lng":41.7539},{"il":"Nevsehir","lat":38.6939,"lng":34.6857},
        {"il":"Nigde","lat":37.9667,"lng":34.6833},{"il":"Ordu","lat":40.9862,"lng":37.8797},
        {"il":"Rize","lat":41.0201,"lng":40.5234},{"il":"Sakarya","lat":40.6940,"lng":30.4358},
        {"il":"Samsun","lat":41.2867,"lng":36.3300},{"il":"Siirt","lat":37.9333,"lng":41.9500},
        {"il":"Sinop","lat":42.0231,"lng":35.1531},{"il":"Sivas","lat":39.7477,"lng":37.0179},
        {"il":"Tekirdag","lat":40.9781,"lng":27.5115},{"il":"Tokat","lat":40.3167,"lng":36.5500},
        {"il":"Trabzon","lat":41.0015,"lng":39.7178},{"il":"Tunceli","lat":39.1079,"lng":39.5479},
        {"il":"Sanliurfa","lat":37.1591,"lng":38.7969},{"il":"Usak","lat":38.6823,"lng":29.4082},
        {"il":"Van","lat":38.4891,"lng":43.4089},{"il":"Yozgat","lat":39.8181,"lng":34.8147},
        {"il":"Zonguldak","lat":41.4564,"lng":31.7987},{"il":"Aksaray","lat":38.3687,"lng":34.0370},
        {"il":"Bayburt","lat":40.2552,"lng":40.2249},{"il":"Karaman","lat":37.1759,"lng":33.2287},
        {"il":"Kirikkale","lat":39.8468,"lng":33.5153},{"il":"Batman","lat":37.8812,"lng":41.1351},
        {"il":"Sirnak","lat":37.5164,"lng":42.4611},{"il":"Bartin","lat":41.6344,"lng":32.3375},
        {"il":"Ardahan","lat":41.1105,"lng":42.7022},{"il":"Igdir","lat":39.9167,"lng":44.0333},
        {"il":"Yalova","lat":40.6500,"lng":29.2667},{"il":"Karabuk","lat":41.2061,"lng":32.6204},
        {"il":"Kilis","lat":36.7184,"lng":37.1212},{"il":"Osmaniye","lat":37.0746,"lng":36.2464},
        {"il":"Duzce","lat":40.8438,"lng":31.1565},
    ]
    return jsonify([{
        "id": f"afad_{m['il'].lower()}",
        "lat": m["lat"], "lng": m["lng"],
        "name": f"AFAD {m['il']} Il Mudurlugu",
        "tip": "AFAD", "renk": "#1565C0",
        "il": m["il"], "ekip": "AFAD Il Ekibi"
    } for m in merkezler])

@app.route("/api/adres")
def api_adres():
    """Nominatim ile koordinattan adres bul."""
    try:
        import requests as req
        lat = request.args.get("lat")
        lng = request.args.get("lng")
        r = req.get(
            f"https://nominatim.openstreetmap.org/reverse",
            params={"lat": lat, "lon": lng, "format": "json", "accept-language": "tr"},
            headers={"User-Agent": "AfeRota/1.0"},
            timeout=5
        )
        d = r.json()
        adres = d.get("display_name", "Adres bulunamadi")
        # Kısalt
        parcalar = adres.split(",")
        kisa = ", ".join(parcalar[:3]) if len(parcalar) >= 3 else adres
        return jsonify({"adres": kisa, "tam_adres": adres})
    except Exception as e:
        return jsonify({"adres": "Adres alinamadi", "hata": str(e)})


# ── KIZILAY 81 İL ─────────────────────────────────────────────
@app.route("/api/kizilay_tr")
def api_kizilay_tr():
    subeler = [
        {"il":"Adana","lat":37.0017,"lng":35.3289},{"il":"Adiyaman","lat":37.7636,"lng":38.2770},
        {"il":"Afyonkarahisar","lat":38.7565,"lng":30.5416},{"il":"Agri","lat":39.7225,"lng":43.0567},
        {"il":"Ankara","lat":39.9272,"lng":32.8644},{"il":"Antalya","lat":36.9081,"lng":30.6956},
        {"il":"Bursa","lat":40.1956,"lng":29.0603},{"il":"Diyarbakir","lat":37.9251,"lng":40.2149},
        {"il":"Erzurum","lat":39.9043,"lng":41.2679},{"il":"Eskisehir","lat":39.7919,"lng":30.5243},
        {"il":"Gaziantep","lat":37.0594,"lng":37.3825},{"il":"Hatay","lat":36.4072,"lng":36.3422},
        {"il":"Istanbul","lat":41.0136,"lng":28.9550},{"il":"Izmir","lat":38.4127,"lng":27.1384},
        {"il":"Kahramanmaras","lat":37.5775,"lng":36.9258},{"il":"Kayseri","lat":38.7205,"lng":35.4853},
        {"il":"Kocaeli","lat":40.7654,"lng":29.9408},{"il":"Konya","lat":37.8667,"lng":32.4833},
        {"il":"Malatya","lat":38.3554,"lng":38.3312},{"il":"Mersin","lat":36.8121,"lng":34.6415},
        {"il":"Samsun","lat":41.2923,"lng":36.3313},{"il":"Sanliurfa","lat":37.1674,"lng":38.7955},
        {"il":"Trabzon","lat":41.0053,"lng":39.7195},{"il":"Van","lat":38.4942,"lng":43.3800},
        {"il":"Elazig","lat":38.6810,"lng":39.2264},{"il":"Erzincan","lat":39.7517,"lng":39.4900},
        {"il":"Manisa","lat":38.6145,"lng":27.4258},{"il":"Mugla","lat":37.2108,"lng":28.3672},
        {"il":"Nevsehir","lat":38.6939,"lng":34.6857},{"il":"Sakarya","lat":40.6885,"lng":30.4369},
    ]
    return jsonify([{
        "id": f"kizilay_{s['il'].lower()}",
        "lat": s["lat"], "lng": s["lng"],
        "name": f"Kizilay {s['il']} Subesi",
        "tip": "Kizilay", "renk": "#B71C1C", "il": s["il"],
        "ekip": "Ambulans, Tibbi Yardim, Kan Bankasi"
    } for s in subeler])

# ── AKUT BÖLGE EKİPLERİ ───────────────────────────────────────
@app.route("/api/akut_tr")
def api_akut_tr():
    return jsonify([
        {"id":"akut_istanbul","lat":41.0150,"lng":28.9700,"name":"AKUT Istanbul Bolge Ekibi","bolge":"Marmara","ekip":"220 gonullu","renk":"#1B5E20","tip":"AKUT"},
        {"id":"akut_ankara","lat":39.9400,"lng":32.8600,"name":"AKUT Ankara Bolge Ekibi","bolge":"Ic Anadolu","ekip":"85 gonullu","renk":"#1B5E20","tip":"AKUT"},
        {"id":"akut_izmir","lat":38.4200,"lng":27.1400,"name":"AKUT Izmir Bolge Ekibi","bolge":"Ege","ekip":"110 gonullu","renk":"#1B5E20","tip":"AKUT"},
        {"id":"akut_antalya","lat":36.9000,"lng":30.7000,"name":"AKUT Antalya Bolge Ekibi","bolge":"Akdeniz","ekip":"75 gonullu","renk":"#1B5E20","tip":"AKUT"},
        {"id":"akut_trabzon","lat":41.0050,"lng":39.7200,"name":"AKUT Trabzon Bolge Ekibi","bolge":"Karadeniz","ekip":"60 gonullu","renk":"#1B5E20","tip":"AKUT"},
        {"id":"akut_erzurum","lat":39.9050,"lng":41.2700,"name":"AKUT Erzurum Bolge Ekibi","bolge":"Dogu Anadolu","ekip":"45 gonullu","renk":"#1B5E20","tip":"AKUT"},
        {"id":"akut_diyarbakir","lat":37.9150,"lng":40.2100,"name":"AKUT Diyarbakir Bolge Ekibi","bolge":"Guneydogu","ekip":"50 gonullu","renk":"#1B5E20","tip":"AKUT"},
        {"id":"akut_kahramanmaras","lat":37.5820,"lng":36.9300,"name":"AKUT Kahramanmaras Ekibi","bolge":"Akdeniz","ekip":"40 gonullu","renk":"#1B5E20","tip":"AKUT"},
    ])

# ── HASTANELERİ OVERPASS API İLE ÇEK ─────────────────────────
@app.route("/api/hastaneler")
def api_hastaneler():
    """Kahramanmaras hastaneleri — Overpass API (OpenStreetMap)"""
    try:
        import requests as req
        query = """
        [out:json][timeout:10];
        area["name"="Kahramanmaraş"]->.searchArea;
        node["amenity"="hospital"](area.searchArea);
        out body;
        """
        r = req.post(
            "https://overpass-api.de/api/interpreter",
            data={"data": query}, timeout=12
        )
        veriler = r.json().get("elements", [])
        hastaneler = []
        for h in veriler:
            tags = h.get("tags", {})
            hastaneler.append({
                "lat": h["lat"], "lng": h["lon"],
                "isim": tags.get("name", "Hastane"),
                "tip": tags.get("healthcare", "hospital"),
                "adres": tags.get("addr:street", ""),
                "telefon": tags.get("phone", ""),
                "yatak": tags.get("beds", "?"),
            })
        if not hastaneler:
            raise Exception("Overpass bos dondu")
        return jsonify({"basarili": True, "hastaneler": hastaneler, "kaynak": "OpenStreetMap"})
    except:
        # Fallback — bilinen Kahramanmaraş hastaneleri
        return jsonify({"basarili": True, "kaynak": "Statik", "hastaneler": [
            {"lat":37.5820,"lng":36.9310,"isim":"Kahramanmaras Egitim Arastirma Hastanesi","tip":"Devlet","yatak":600,"adres":"Merkez"},
            {"lat":37.5780,"lng":36.9150,"isim":"Necip Fazil Sehir Hastanesi","tip":"Sehir","yatak":1000,"adres":"Dulkadiroglu"},
            {"lat":37.5690,"lng":36.9480,"isim":"Onikisubat Devlet Hastanesi","tip":"Devlet","yatak":250,"adres":"Onikisubat"},
            {"lat":37.6090,"lng":36.9200,"isim":"Turkoglu Ilce Hastanesi","tip":"Ilce","yatak":80,"adres":"Turkoglu"},
            {"lat":37.5750,"lng":36.9320,"isim":"Ozel Umit Hastanesi","tip":"Ozel","yatak":120,"adres":"Merkez"},
        ]})

# ── HELİKOPTER İNİŞ ALANLARI ─────────────────────────────────
@app.route("/api/helikopter")
def api_helikopter():
    return jsonify([
        {"lat":37.5543,"lng":36.9480,"isim":"Kahramanmaras Havalimani","tip":"Havaalani","kapasite":"Buyuk"},
        {"lat":37.5820,"lng":36.9310,"isim":"EAH Helipad","tip":"Hastane Helipad","kapasite":"Orta"},
        {"lat":37.5780,"lng":36.9150,"isim":"Sehir Hastanesi Helipad","tip":"Hastane Helipad","kapasite":"Buyuk"},
        {"lat":37.5858,"lng":36.9371,"isim":"AFAD Helikopter Pisti","tip":"AFAD","kapasite":"Orta"},
        {"lat":37.6050,"lng":36.9150,"isim":"AFAD Merkez-2 Pisti","tip":"AFAD","kapasite":"Kucuk"},
        {"lat":37.6380,"lng":37.0150,"isim":"Pazarcik Acil Inis Alani","tip":"Acil","kapasite":"Kucuk"},
        {"lat":37.6050,"lng":37.0800,"isim":"Elbistan Inis Alani","tip":"Acil","kapasite":"Kucuk"},
    ])

# ── İTFAİYE İSTASYONLARI ─────────────────────────────────────
@app.route("/api/itfaiye")
def api_itfaiye():
    try:
        import requests as req
        query = """
        [out:json][timeout:10];
        area["name"="Kahramanmaraş"]->.searchArea;
        node["amenity"="fire_station"](area.searchArea);
        out body;
        """
        r = req.post("https://overpass-api.de/api/interpreter", data={"data": query}, timeout=12)
        veriler = r.json().get("elements", [])
        istasyonlar = []
        for h in veriler:
            tags = h.get("tags", {})
            istasyonlar.append({
                "lat": h["lat"], "lng": h["lon"],
                "isim": tags.get("name", "Itfaiye Istasyonu"),
                "adres": tags.get("addr:street", ""),
            })
        if not istasyonlar:
            raise Exception("Bos")
        return jsonify({"basarili": True, "istasyonlar": istasyonlar, "kaynak": "OpenStreetMap"})
    except:
        return jsonify({"basarili": True, "kaynak": "Statik", "istasyonlar": [
            {"lat":37.5810,"lng":36.9220,"isim":"Merkez Itfaiye Istasyonu","adres":"Merkez"},
            {"lat":37.5950,"lng":36.9490,"isim":"Dulkadiroglu Itfaiye","adres":"Dulkadiroglu"},
            {"lat":37.5660,"lng":36.9560,"isim":"Onikisubat Itfaiye","adres":"Onikisubat"},
            {"lat":37.6080,"lng":36.9100,"isim":"Turkoglu Itfaiye","adres":"Turkoglu"},
            {"lat":37.6040,"lng":37.0780,"isim":"Elbistan Itfaiye","adres":"Elbistan"},
        ]})

# ── AKARYAKIT İSTASYONLARI ────────────────────────────────────
@app.route("/api/akaryakit")
def api_akaryakit():
    try:
        import requests as req
        query = """
        [out:json][timeout:10];
        area["name"="Kahramanmaraş"]["admin_level"="6"]->.searchArea;
        node["amenity"="fuel"](area.searchArea);
        out body;
        """
        r = req.post("https://overpass-api.de/api/interpreter", data={"data": query}, timeout=12)
        veriler = r.json().get("elements", [])[:15]
        return jsonify({"basarili": True, "istasyonlar": [
            {"lat": h["lat"], "lng": h["lon"],
             "isim": h.get("tags",{}).get("name","Akaryakit"),
             "marka": h.get("tags",{}).get("brand","")}
            for h in veriler
        ], "kaynak": "OpenStreetMap"})
    except:
        return jsonify({"basarili": True, "kaynak": "Statik", "istasyonlar": [
            {"lat":37.5830,"lng":36.9180,"isim":"Shell Merkez","marka":"Shell"},
            {"lat":37.5920,"lng":36.9420,"isim":"BP Dulkadiroglu","marka":"BP"},
            {"lat":37.5660,"lng":36.9500,"isim":"Opet Onikisubat","marka":"Opet"},
            {"lat":37.6070,"lng":36.9130,"isim":"Total Turkoglu","marka":"Total"},
            {"lat":37.5780,"lng":36.8960,"isim":"Petrol Ofisi Bati","marka":"PO"},
        ]})


# ── AI ÖNCELİK MOTORU ────────────────────────────────────────
@app.route("/api/ai_oncelik")
def api_ai_oncelik():
    afetler = afetleri_oku()
    if not afetler:
        return jsonify([])
    sonuclar = []
    for a in afetler:
        # Çok faktörlü skor
        siddet_p = {"Kritik":100,"Agir":60,"Orta":25}.get(a["siddet"],25)
        mahsur_p = min(100, a["mahsur"] * 1.5)
        tip_p = {"deprem":90,"yangin":75,"sel":60,"heyelan":50}.get(a["tip"],40)
        isi_p = max(0, (a.get("sicaklik",36)-36)*20) if a.get("sicaklik",0)>36 else 0
        riskli_p = 20 if a.get("riskliBina") else 0
        skor = siddet_p*0.35 + mahsur_p*0.30 + tip_p*0.20 + isi_p*0.10 + riskli_p*0.05

        # Türkçe sebep
        sebepler = []
        if a["siddet"] == "Kritik": sebepler.append("kritik şiddet")
        if a["mahsur"] >= 30: sebepler.append(f"{a['mahsur']} mahsur")
        elif a["mahsur"] >= 10: sebepler.append(f"{a['mahsur']} kişi tehlikede")
        if a["tip"] == "deprem": sebepler.append("deprem enkaz riski")
        elif a["tip"] == "yangin": sebepler.append("yangın yayılma riski")
        if a.get("sicaklik",0) > 37.5: sebepler.append("yüksek ısı sinyali")
        if a.get("riskliBina"): sebepler.append("yakında riskli bina")
        sebep = " · ".join(sebepler[:3]) if sebepler else "standart müdahale"

        sonuclar.append({
            "afet_id": a["id"],
            "afet_name": a["name"],
            "lat": a["lat"], "lng": a["lng"],
            "skor": round(skor, 1),
            "sebep": sebep,
            "oncelik": 0,
            "renk": a["renk"]
        })

    sonuclar.sort(key=lambda x: -x["skor"])
    for i,s in enumerate(sonuclar):
        s["oncelik"] = i+1
    return jsonify(sonuclar[:10])

# ── GERÇEK ZAMANLI AFAD KONTROL ───────────────────────────────
@app.route("/api/afad_canli")
def api_afad_canli():
    """Son 30 dakikadaki yeni depremleri kontrol et."""
    try:
        import requests as req
        from datetime import datetime, timedelta
        baslangic = (datetime.utcnow()-timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
        bitis = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        url = "https://deprem.afad.gov.tr/apiv2/event/filter"
        r = req.get(url, params={"start":baslangic,"end":bitis,"minmag":3.0,"orderby":"timedesc","limit":5}, timeout=8)
        veriler = r.json()
        if not veriler:
            return jsonify({"yeni":False,"depremler":[]})
        depremler = []
        for d in veriler:
            mag = float(d.get("magnitude",0))
            depremler.append({
                "lat": float(d.get("latitude",39)),
                "lng": float(d.get("longitude",35)),
                "buyukluk": mag,
                "konum": d.get("location","?"),
                "zaman": d.get("date",""),
                "siddet": "Kritik" if mag>=5 else "Agir" if mag>=4 else "Orta"
            })
        return jsonify({"yeni": len(depremler)>0, "depremler": depremler, "sayac": len(depremler)})
    except Exception as e:
        return jsonify({"yeni":False,"depremler":[],"hata":str(e)})

# ── ROTA OPTİMİZASYON SKORU ──────────────────────────────────
@app.route("/api/rota_skor")
def api_rota_skor():
    """İki rota arasında karşılaştırma skoru döndür."""
    try:
        mesafe1 = float(request.args.get("m1", 10))
        mesafe2 = float(request.args.get("m2", 13))
        sure1 = float(request.args.get("s1", 15))
        sure2 = float(request.args.get("s2", 20))
        mesafe_kazanim = round((mesafe2-mesafe1)/mesafe2*100, 1) if mesafe2>0 else 0
        sure_kazanim = round((sure2-sure1)/sure2*100, 1) if sure2>0 else 0
        return jsonify({
            "mesafe_kazanim": mesafe_kazanim,
            "sure_kazanim": sure_kazanim,
            "mesaj": f"Bu rota alternatiften %{sure_kazanim} daha hızlı, {round(mesafe2-mesafe1,1)}km daha kısa"
        })
    except:
        return jsonify({"mesaj":"Hesaplanamadı"})

if __name__=="__main__":
    if not os.path.exists(AFET_YEDEK):
        shutil.copy(AFET_DOSYA,AFET_YEDEK)
        print("Yedek olusturuldu.")
    app.run(debug=True,port=5000)
