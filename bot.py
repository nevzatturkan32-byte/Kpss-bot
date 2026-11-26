import os
import json
import requests
from bs4 import BeautifulSoup

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

# Takip etmek istediğin anahtar kelimeler (İstediğini ekleyip çıkarabilirsin)
ANAHTAR_KELIMELER = ["kpss", "sözleşmeli", "memur", "personel", "güvenlik", "büro", "destek", "koruma"]

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

def ilanlari_tara():
    gonderilenler = kayitlari_yukle()
    yeni_eklenen = False

    # Resmi Kamu İlanları Kaynağı (ilan.gov.tr Kamu Personel Alımları)
    url = "https://www.ilan.gov.tr/ilan/kategori/9/kamu-akademik-personel"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    try:
        cevap = requests.get(url, headers=headers, timeout=20)
        soup = BeautifulSoup(cevap.text, "html.parser")
        ilanlar = soup.find_all("a", href=True)

        for ilan in ilanlar:
            baslik = ilan.get_text(strip=True)
            link = ilan["href"]

            if len(baslik) < 25 or "/ilan/" not in link:
                continue

            tam_link = link if link.startswith("http") else f"https://www.ilan.gov.tr{link}"

            if tam_link in gonderilenler:
                continue

            # Anahtar kelime kontrolü
            baslik_kucuk = baslik.lower()
            if any(kelime in baslik_kucuk for kelime in ANAHTAR_KELIMELER):
                mesaj = (
                    f"📢 <b>YENİ KAMU İLANI YAYIMLANDI</b>\n\n"
                    f"📌 <b>İlan Başlığı:</b> {baslik}\n\n"
                    f"🔗 <b>Detaylar ve Başvuru Şartları:</b>\n{tam_link}"
                )
                telegram_gonder(mesaj)
                gonderilenler.append(tam_link)
                yeni_eklenen = True

    except Exception as e:
        print("Tarama hatası:", e)

    if yeni_eklenen:
        kayitlari_kaydet(gonderilenler)

if __name__ == "__main__":
    ilanlari_tara()
