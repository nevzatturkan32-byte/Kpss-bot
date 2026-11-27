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

)

if __name__ == "__main__":
    ilanlari_tara()
