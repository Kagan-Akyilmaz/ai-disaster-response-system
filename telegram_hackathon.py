"""
telegram_hackathon.py — AfeRota Telegram Bot
"""
import telebot, requests, os, json

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
HARITA = "http://localhost:5000"
bot = telebot.TeleBot(TELEGRAM_TOKEN)

def api(endpoint, method="get", data=None):
    try:
        if method=="post":
            r=requests.post(f"{HARITA}{endpoint}",json=data or {},timeout=5)
        else:
            r=requests.get(f"{HARITA}{endpoint}",timeout=5)
        return r.json()
    except Exception as e:
        return {"basarili":False,"hata":str(e)}

# ── /liste ────────────────────────────────────────────────────
@bot.message_handler(commands=["liste"])
def cmd_liste(m):
    atamalar=api("/api/atamalar")
    if not isinstance(atamalar,list):
        bot.send_message(m.chat.id,"❌ Veri alinamadi."); return
    if not atamalar:
        bot.send_message(m.chat.id,"✅ Aktif afet bolgesi yok!"); return
    kritik=[a for a in atamalar if a["siddet"]=="Kritik"]
    agir=[a for a in atamalar if a["siddet"]=="Agir"]
    orta=[a for a in atamalar if a["siddet"]=="Orta"]
    metin=f"📋 AKTİF AFET BÖLGELERİ ({len(atamalar)})\n\n"
    if kritik:
        metin+="🔴 KRİTİK:\n"
        for a in kritik:
            metin+=f"  #{a['afet_id']} {a['afet_name']} — {a['mahsur']}k\n"
        metin+="\n"
    if agir:
        metin+="🟠 AĞIR:\n"
        for a in agir:
            metin+=f"  #{a['afet_id']} {a['afet_name']} — {a['mahsur']}k\n"
        metin+="\n"
    if orta:
        metin+="🟡 ORTA:\n"
        for a in orta[:5]:
            metin+=f"  #{a['afet_id']} {a['afet_name']}\n"
        if len(orta)>5: metin+=f"  ...ve {len(orta)-5} tane daha\n"
    metin+=f"\n/cikar <id> ile bolge cikarabilirsin"
    bot.send_message(m.chat.id,metin)

# ── /kritikler ────────────────────────────────────────────────
@bot.message_handler(commands=["kritikler"])
def cmd_kritikler(m):
    atamalar=api("/api/atamalar")
    kritik=[a for a in atamalar if a["siddet"]=="Kritik"]
    if not kritik:
        bot.send_message(m.chat.id,"✅ Kritik bolge yok!"); return
    metin=f"🔴 KRİTİK BÖLGELER ({len(kritik)})\n\n"
    for a in kritik:
        metin+=f"#{a['afet_id']} {a['afet_name']}\n"
        metin+=f"  👥 {a['mahsur']} mahsur | 🚗 {a['arac']}\n"
        metin+=f"  🏢 {a['merkez_name']} | 📍 {a['mesafe_km']}km\n\n"
    bot.send_message(m.chat.id,metin)

# ── /merkez ───────────────────────────────────────────────────
@bot.message_handler(commands=["merkez"])
def cmd_merkez(m):
    """
    /merkez AFAD1
    /merkez Kizilay1
    """
    parcalar=m.text.split()[1:]
    if not parcalar:
        bot.send_message(m.chat.id,
            "Kullanim: /merkez <merkez_id>\n"
            "Merkezler: afad1, afad2, kizilay1, kizilay2, akut1, akut2"
        ); return
    mid=parcalar[0].lower()
    atamalar=api("/api/atamalar")
    gorevler=[a for a in atamalar if a["merkez_id"].lower()==mid]
    if not gorevler:
        bot.send_message(m.chat.id,f"❌ '{mid}' merkezi bulunamadi veya gorevi yok."); return
    metin=f"🏢 {gorevler[0]['merkez_name'].upper()} GÖREVLERİ\n\n"
    toplam_mahsur=sum(g["mahsur"] for g in gorevler)
    metin+=f"Toplam: {len(gorevler)} gorev | {toplam_mahsur} mahsur\n\n"
    for i,g in enumerate(gorevler,1):
        metin+=f"{i}. #{g['afet_id']} {g['afet_name']}\n"
        metin+=f"   {g['siddet']} | {g['mahsur']}k | {g['mesafe_km']}km\n"
    bot.send_message(m.chat.id,metin)

# ── /ozet ─────────────────────────────────────────────────────
@bot.message_handler(commands=["ozet"])
def cmd_ozet(m):
    atamalar=api("/api/atamalar")
    if not isinstance(atamalar,list):
        bot.send_message(m.chat.id,"❌ Veri alinamadi."); return
    toplam_mahsur=sum(a["mahsur"] for a in atamalar)
    kritik=len([a for a in atamalar if a["siddet"]=="Kritik"])
    agir=len([a for a in atamalar if a["siddet"]=="Agir"])
    orta=len([a for a in atamalar if a["siddet"]=="Orta"])
    merkezler={}
    for a in atamalar:
        merkezler[a["merkez_name"]]=merkezler.get(a["merkez_name"],0)+1
    metin=(
        f"📊 SİSTEM ÖZETİ\n\n"
        f"👥 Toplam mahsur: {toplam_mahsur}\n"
        f"📍 Aktif bolge: {len(atamalar)}\n"
        f"🔴 Kritik: {kritik}\n"
        f"🟠 Agir: {agir}\n"
        f"🟡 Orta: {orta}\n\n"
        f"🏢 MERKEZ YÜKÜ:\n"
    )
    for mk,sayi in merkezler.items():
        metin+=f"  {mk}: {sayi} gorev\n"
    bot.send_message(m.chat.id,metin)

# ── /tamamlandi ───────────────────────────────────────────────
@bot.message_handler(commands=["tamamlandi","tamamlandı"])
def cmd_tamamlandi(m):
    """
    /tamamlandi 1    → Kurtarma tamamlandi, bölgeyi çıkar
    """
    parcalar=m.text.split()[1:]
    if not parcalar or not parcalar[0].isdigit():
        bot.send_message(m.chat.id,"Kullanim: /tamamlandi <afet_id>\nOrnek: /tamamlandi 1"); return
    afet_id=int(parcalar[0])
    atama=next((a for a in api("/api/atamalar") if a["afet_id"]==afet_id),None)
    sonuc=api(f"/api/afet_cikar/{afet_id}","post")
    if sonuc.get("basarili"):
        isim=atama["afet_name"] if atama else f"#{afet_id}"
        bot.send_message(m.chat.id,
            f"✅ KURTARMA TAMAMLANDI!\n\n"
            f"📍 {isim}\n"
            f"👥 {atama['mahsur'] if atama else '?'} kisi kurtarildi\n"
            f"📊 Kalan bolge: {sonuc['kalan']}"
        )
    else:
        bot.send_message(m.chat.id,f"❌ {sonuc.get('mesaj','Hata')}")

# ── /durum_guncelle ───────────────────────────────────────────
@bot.message_handler(commands=["durum_guncelle"])
def cmd_durum_guncelle(m):
    """
    /durum_guncelle 1 mahsur 20   → 1 nolu bölgenin mahsurunu 20 yap
    /durum_guncelle 1 siddet Kritik
    """
    parcalar=m.text.split()[1:]
    if len(parcalar)<3 or not parcalar[0].isdigit():
        bot.send_message(m.chat.id,
            "Kullanim: /durum_guncelle <id> <alan> <deger>\n"
            "Alanlar: mahsur, siddet\n"
            "Ornek: /durum_guncelle 1 mahsur 20\n"
            "Ornek: /durum_guncelle 1 siddet Kritik"
        ); return
    afet_id=int(parcalar[0])
    alan=parcalar[1].lower()
    deger=" ".join(parcalar[2:])
    try:
        import json as _json
        with open("afetler.json","r",encoding="utf-8") as f:
            afetler=_json.load(f)
        af=next((a for a in afetler if a["id"]==afet_id),None)
        if not af:
            bot.send_message(m.chat.id,f"❌ #{afet_id} bulunamadi"); return
        if alan=="mahsur":
            af["mahsur"]=int(deger)
        elif alan=="siddet":
            if deger.capitalize() not in ["Kritik","Agir","Orta"]:
                bot.send_message(m.chat.id,"Siddet: Kritik | Agir | Orta"); return
            af["siddet"]=deger.capitalize()
            renk={"Kritik":"#B71C1C","Agir":"#E65100","Orta":"#F9A825"}[af["siddet"]]
            af["renk"]=renk
        else:
            bot.send_message(m.chat.id,"Alan: mahsur veya siddet"); return
        with open("afetler.json","w",encoding="utf-8") as f:
            _json.dump(afetler,f,ensure_ascii=False,indent=2)
        bot.send_message(m.chat.id,
            f"✅ Guncellendi!\n"
            f"#{afet_id} {af['name']}\n"
            f"{alan}: {deger}"
        )
    except Exception as e:
        bot.send_message(m.chat.id,f"❌ Hata: {e}")

# ── /ekip_gonder ──────────────────────────────────────────────
@bot.message_handler(commands=["ekip_gonder"])
def cmd_ekip_gonder(m):
    """
    /ekip_gonder 1 AFAD1
    """
    parcalar=m.text.split()[1:]
    if len(parcalar)<2 or not parcalar[0].isdigit():
        bot.send_message(m.chat.id,
            "Kullanim: /ekip_gonder <afet_id> <merkez_id>\n"
            "Ornek: /ekip_gonder 5 afad1\n"
            "Merkezler: afad1, afad2, kizilay1, kizilay2, akut1, akut2"
        ); return
    afet_id=int(parcalar[0])
    merkez_adi=parcalar[1]
    atamalar=api("/api/atamalar")
    af=next((a for a in atamalar if a["afet_id"]==afet_id),None)
    if not af:
        bot.send_message(m.chat.id,f"❌ #{afet_id} bulunamadi"); return
    bot.send_message(m.chat.id,
        f"🚑 EKİP GÖNDERİLDİ!\n\n"
        f"📍 Hedef: {af['afet_name']}\n"
        f"🏢 Merkez: {merkez_adi.upper()}\n"
        f"👥 Mahsur: {af['mahsur']} kisi\n"
        f"📏 Mesafe: {af['mesafe_km']}km | ~{af['sure_dk']}dk\n\n"
        f"Kurtarma tamamlaninca: /tamamlandi {afet_id}"
    )

# ── /cikar ────────────────────────────────────────────────────
@bot.message_handler(commands=["cikar","cıkar"])
def cmd_cikar(m):
    parcalar=m.text.split()[1:]
    if not parcalar:
        bot.send_message(m.chat.id,
            "Kullanim: /cikar <afet_id>\n"
            "Ornek: /cikar 1\n"
            "Birden fazla: /cikar 1 5 12"
        ); return
    sonuclar=[]
    for p in parcalar:
        if not p.isdigit(): continue
        afet_id=int(p)
        sonuc=api(f"/api/afet_cikar/{afet_id}","post")
        if sonuc.get("basarili"):
            c=sonuc.get("cikarilan",{})
            sonuclar.append(f"✅ #{afet_id} — {c.get('name','?')} cikarildi")
        else:
            sonuclar.append(f"❌ #{afet_id} — {sonuc.get('mesaj','Hata')}")
    kalan=api("/api/afet_sayisi").get("sayi","?")
    bot.send_message(m.chat.id,"\n".join(sonuclar)+f"\n\n📊 Kalan: {kalan} bolge")

# ── /afet ─────────────────────────────────────────────────────
@bot.message_handler(commands=["afet"])
def cmd_afet(m):
    try:
        parcalar=m.text.replace("/afet","").strip().split()
        if len(parcalar)<2:
            bot.send_message(m.chat.id,"Kullanim: /afet <isim> <mahsur> <siddet>\nOrnek: /afet Merkez_enkaz 25 Kritik"); return
        mahsur=0; siddet="Orta"; isim_p=[]
        for p in parcalar:
            if p.isdigit(): mahsur=int(p)
            elif p.capitalize() in ["Kritik","Agir","Orta"]: siddet=p.capitalize()
            else: isim_p.append(p.replace("_"," "))
        isim=" ".join(isim_p) or "Yeni Afet"
        isim_l=isim.lower()
        tip="deprem"
        if any(k in isim_l for k in ["yangin","alev"]): tip="yangin"
        elif any(k in isim_l for k in ["sel","su"]): tip="sel"
        elif any(k in isim_l for k in ["heyelan","toprak"]): tip="heyelan"
        konum={"merkez":(37.575,36.922),"dulkad":(37.593,36.951),"onikis":(37.568,36.958),"turkoglu":(37.612,36.906),"pazarcik":(37.638,37.015)}
        import random
        lat,lng=37.580+random.uniform(-0.03,0.03),36.940+random.uniform(-0.03,0.03)
        for k,(la,lo) in konum.items():
            if k in isim_l: lat,lng=la,lo; break
        sonuc=api("/api/afet_ekle","post",{"name":isim,"mahsur":mahsur,"siddet":siddet,"tip":tip,"lat":lat,"lng":lng})
        if sonuc.get("basarili"):
            af=sonuc["afet"]
            bot.send_message(m.chat.id,f"✅ Afet eklendi!\n\n#{af['id']} {af['name']}\nSiddet: {af['siddet']} | Mahsur: {af['mahsur']}")
        else:
            bot.send_message(m.chat.id,f"❌ {sonuc.get('hata','Hata')}")
    except Exception as e:
        bot.send_message(m.chat.id,f"❌ {e}")

# ── /sifirla ──────────────────────────────────────────────────
@bot.message_handler(commands=["sifirla"])
def cmd_sifirla(m):
    sonuc=api("/api/afetleri_sifirla","post")
    if sonuc.get("basarili"):
        bot.send_message(m.chat.id,"✅ Tüm afet bölgeleri sıfırlandı!\n35 bölge yeniden yüklendi.")
    else:
        bot.send_message(m.chat.id,f"❌ {sonuc.get('mesaj','Hata')}")

# ── /durum ────────────────────────────────────────────────────
@bot.message_handler(commands=["durum"])
def cmd_durum(m):
    sayi=api("/api/afet_sayisi").get("sayi","?")
    bot.send_message(m.chat.id,
        f"📊 SİSTEM DURUMU\n\n"
        f"✅ Harita aktif: {HARITA}\n"
        f"📍 Aktif afet bölgesi: {sayi}\n"
    )

# ── /yardim ───────────────────────────────────────────────────
@bot.message_handler(commands=["yardim","start","help"])
def cmd_yardim(m):
    bot.send_message(m.chat.id,
        "🤖 AfeRota Komutları\n\n"
        "/liste — Tüm aktif bölgeleri gör\n"
        "/kritikler — Sadece kritik bölgeler\n"
        "/ozet — Genel istatistik\n"
        "/merkez <id> — Merkez görevleri\n"
        "  Örnek: /merkez afad1\n\n"
        "/cikar <id> — Bölge çıkar\n"
        "  Örnek: /cikar 1\n"
        "  Çoklu: /cikar 1 5 12\n\n"
        "/tamamlandi <id> — Kurtarma bitti\n"
        "  Örnek: /tamamlandi 3\n\n"
        "/ekip_gonder <id> <merkez> — Ekip gönder\n"
        "  Örnek: /ekip_gonder 5 afad1\n\n"
        "/durum_guncelle <id> <alan> <deger>\n"
        "  Örnek: /durum_guncelle 1 mahsur 20\n"
        "  Örnek: /durum_guncelle 1 siddet Agir\n\n"
        "/afet <isim> <mahsur> <siddet> — Yeni ekle\n"
        "/sifirla — Tüm afetleri sıfırla\n"
        "/durum — Sistem durumu\n"
    )

if __name__=="__main__":
    print("="*40)
    print("  AfeRota Telegram Bot aktif")
    print("  Komutlar: /yardim")
    print("="*40)
    bot.infinity_polling()
