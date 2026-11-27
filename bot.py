import os
import json
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

BOT_TOKEN = os.environ["BOT_TOKEN"].strip()
CHAT_ID = os.environ["CHAT_ID"].strip()

# Sadece Ortaöğretim (Lise / P94) hedef kelimeleri
HEDEF_KELIMELER = [
    "ortaöğretim", "p94", "kpssp94", "lise mezunu", "lise düzeyinde",
    "koruma ve güvenlik", "destek personeli", "şoför", "temizlik", "hizmetli", "mübaşir", "infaz ve koruma"
]

# Sadece yükseköğretim alımı olan ilanları elemek için yasaklı kelimeler
HARIC_KELIMELER = [
    "sadece lisans", "sadece ön lisans", "önlisans mezunu", "lisans mezunu", "kpssp3", "kpssp93"
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
    # Eğer ilanda açıkça sadece lisans/önlisans diyorsa ve ortaöğretim geçmiyorsa ele
    if any(h in m for h in HARIC_KELIMELER) and ("ortaöğretim" not in m and "p94" not in m and "lise" not in m):
        return False
    return any(k in m for k in HEDEF_KELIMELER)

def ilanlari_tara():
    gonderilenler = kayitlari_yukle()
    yeni_eklenen = False
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    # Kaynak 1: Resmi Gazete (Kamu Personel Alım İlanları)
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

            if tam_link in gonderilenler:
                continue

            if ("personel" in baslik.lower() or "alım" in baslik.lower() or "memur" in baslik.lower()) and p94_uygun_mu(baslik):
                mesaj = (
                    f"🏛 <b>RESMİ GAZETE (ORTAÖĞRETİM / P94)</b>\n\n"
                    f"📌 <b>Kurum / İlan:</b> {baslik}\n\n"
                    f"🔗 <b>İlan Detayı:</b>\n{tam_link}"
                )
                telegram_gonder(mesaj)
                gonderilenler.append(tam_link)
                yeni_eklenen = True
    except Exception as e:
        print("RG hata:", e)

    # Kaynak 2: Doğrudan KPSS Ortaöğretim (P94) Kamu Alım Duyuruları
    try:
        rss_url = "https://news.google.com/rss/search?q=(%22orta%C3%B6%C4%9Fretim%22+OR+%22P94%22+OR+%22lise+mezunu%22)+%22personel+al%C4%B1m%C4%B1%22+kpss&hl=tr&gl=TR&ceid=TR:tr"
        rss_cevap = requests.get(rss_url, headers=headers, timeout=20)
        kok = ET.fromstring(rss_cevap.content)

        for item in kok.findall(".//item")[:12]:
            baslik = item.find("title").text
            link = item.find("link").text
            tarih = item.find("pubDate").text if item.find("pubDate") is not None else ""

            if link in gonderilenler:
                continue

            if p94_uygun_mu(baslik):
                mesaj = (
                    f"🎯 <b>KPSS ORTAÖĞRETİM (P94) İLANI</b>\n\n"
                    f"📌 <b>İlan:</b> {baslik}\n"
                    f"🗓 <b>Tarih:</b> {tarih[:16]}\n\n"
                    f"🔗 <b>Başvuru ve Şartlar:</b>\n{link}"
                )
                telegram_gonder(mesaj)
                gonderilenler.append(link)
                yeni_eklenen = True
    except Exception as e:
        print("RSS hata:", e)

    if yeni_eklenen:
        kayitlari_kaydet(gonderilenler)

if __name__ == "__main__":
    ilanlari_tara()
