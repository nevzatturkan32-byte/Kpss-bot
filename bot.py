import os
import json
import requests
from bs4 import BeautifulSoup

BOT_TOKEN = os.environ["BOT_TOKEN"].strip()
CHAT_ID = os.environ["CHAT_ID"].strip()

# Ortaöğretim (Lise / P94) ve ilgili kamu kadro kelimeleri
HEDEF_KELIMELER = [
    "ortaöğretim", "p94", "kpssp94", "lise", "koruma ve güvenlik",
    "güvenlik görevlisi", "destek personeli", "şoför", "hizmetli",
    "mübaşir", "infaz ve koruma", "sözleşmeli personel", "memur alım", "personel alım"
]

# Sadece yükseköğretim alımı olan ilanları elemek için
HARIC_KELIMELER = [
    "sadece lisans", "sadece ön lisans", "önlisans mezunu", "lisans mezunu", "kpssp3", "kpssp93", "akademik personel", "öğretim üyesi", "araştırma görevlisi"
]

KAYIT_DOSYASI = "gonderilenler.json"

def kayitlari_yukle():
    if os.path.exists(KAYIT_DOSYASI):
        with open(KAYIT_DOSYASI, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def kayitlari_kaydet(liste):
    with open(KAYIT_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(liste[-300:], f, ensure_ascii=False, indent=2)

def telegram_gonder(mesaj):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    veri = {
        "chat_id": CHAT_ID,
        "text": mesaj,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    requests.post(url, data=veri, timeout=15)

def p94_uygun_mu(metin):
    m = metin.lower()
    if any(h in m for h in HARIC_KELIMELER) and ("ortaöğretim" not in m and "p94" not in m and "lise" not in m):
        return False
    return any(k in m for k in HEDEF_KELIMELER)

def ilanlari_tara():
    gonderilenler = kayitlari_yukle()
    yeni_eklenen = False
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    # Kaynak 1: Doğrudan T.C. Resmi Gazete (Çeşitli İlanlar - Kamu Alımları)
    try:
        cevap = requests.get("https://www.resmigazete.gov.tr", headers=headers, timeout=20)
        cevap.encoding = "utf-8"
        soup = BeautifulSoup(cevap.text, "html.parser")

        for link_etiketi in soup.find_all("a", href=True):
            baslik = link_etiketi.get_text(strip=True)
            href = link_etiketi["href"]

            if len(baslik) < 15:
                continue

            tam_link = href if href.startswith("http") else f"https://www.resmigazete.gov.tr/{href.lstrip('/')}"

            # Sadece resmi devlet (.gov.tr) ilan linklerini al
            if ".gov.tr" not in tam_link or tam_link in gonderilenler:
                continue

            if ("personel" in baslik.lower() or "alım" in baslik.lower() or "memur" in baslik.lower() or "sınav" in baslik.lower()) and p94_uygun_mu(baslik):
                mesaj = (
                    f"🏛 <b>RESMİ GAZETE KAMU İLANI (P94 / ORTAÖĞRETİM)</b>\n\n"
                    f"📌 <b>Kurum / İlan:</b> {baslik}\n\n"
                    f"🔗 <b>Resmi İlan Metni:</b>\n{tam_link}"
                )
                telegram_gonder(mesaj)
                gonderilenler.append(tam_link)
                yeni_eklenen = True
    except Exception as e:
        print("RG hata:", e)

    # Kaynak 2: SBB Resmi Kamu İlan Portalı (kamuilan.sbb.gov.tr)
    try:
        sbb_url = "https://kamuilan.sbb.gov.tr"
        sbb_cevap = requests.get(sbb_url, headers=headers, timeout=20)
        sbb_cevap.encoding = "utf-8"
        sbb_soup = BeautifulSoup(sbb_cevap.text, "html.parser")

        for a in sbb_soup.find_all("a", href=True):
            baslik = a.get_text(strip=True)
            href = a["href"]

            if len(baslik) < 15:
                continue

            tam_link = href if href.startswith("http") else f"https://kamuilan.sbb.gov.tr/{href.lstrip('/')}"

            if tam_link in gonderilenler:
                continue

            if p94_uygun_mu(baslik):
                mesaj = (
                    f"📢 <b>KAMU İLAN PORTALI (ORTAÖĞRETİM / P94)</b>\n\n"
                    f"📌 <b>Kurum / İlan:</b> {baslik}\n\n"
                    f"🔗 <b>Resmi Başvuru Sayfası:</b>\n{tam_link}"
                )
                telegram_gonder(mesaj)
                gonderilenler.append(tam_link)
                yeni_eklenen = True
    except Exception as e:
        print("SBB hata:", e)

    if yeni_eklenen:
        kayitlari_kaydet(gonderilenler)

if __name__ == "__main__":
    ilanlari_tara()
