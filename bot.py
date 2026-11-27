
         import os
import json
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

BOT_TOKEN = os.environ["BOT_TOKEN"].strip()
CHAT_ID = os.environ["CHAT_ID"].strip()

ANAHTAR_KELIMELER = [
    "kpss", "sözleşmeli", "memur", "personel", "güvenlik",
    "büro", "destek", "koruma", "alım", "atama", "üniversite", "bakanlığı"
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
    sonuc = requests.post(url, data=veri, timeout=15)
    print("Telegram cevabi:", sonuc.text)

def ilanlari_tara():
    gonderilenler = kayitlari_yukle()
    yeni_eklenen = False
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    telegram_gonder("✅ <b>KPSS İlan Botun Aktif!</b>\nGüncel kamu ilanları taranıyor...")

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

            if any(kelime in baslik.lower() for kelime in ANAHTAR_KELIMELER):
                mesaj = (
                    f"🏛 <b>RESMİ GAZETE İLANI</b>\n\n"
                    f"📌 <b>Başlık:</b> {baslik}\n\n"
                    f"🔗 <b>İlan Linki:</b>\n{tam_link}"
                )
                telegram_gonder(mesaj)
                gonderilenler.append(tam_link)
                yeni_eklenen = True
    except Exception as e:
        print("RG hata:", e)

    try:
        rss_url = "https://news.google.com/rss/search?q=kpss+s%C3%B6zle%C5%9Fmeli+personel+al%C4%B1m%C4%B1+site:gov.tr&hl=tr&gl=TR&ceid=TR:tr"
        rss_cevap = requests.get(rss_url, headers=headers, timeout=20)
        kok = ET.fromstring(rss_cevap.content)

        for item in kok.findall(".//item")[:10]:
            baslik = item.find("title").text
            link = item.find("link").text
            tarih = item.find("pubDate").text if item.find("pubDate") is not None else ""

            if link in gonderilenler:
                continue

            mesaj = (
                f"📢 <b>YENİ KAMU ALIM DUYURUSU</b>\n\n"
                f"📌 <b>İlan:</b> {baslik}\n"
                f"🗓 <b>Tarih:</b> {tarih[:16]}\n\n"
                f"🔗 <b>Detay ve Başvuru:</b>\n{link}"
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
       
