import os
import re
import json
import requests
from bs4 import BeautifulSoup

TOKEN = os.environ["BOT_TOKEN"].strip()
CHAT = os.environ["CHAT_ID"].strip()
KARIYER = "https://isealimkariyerkapisi.cbiko.gov.tr"
DOSYA = "gonderilenler.json"

P94 = [
    "ortaöğretim", "p94", "kpssp94",
    "lise", "güvenlik", "destek personeli",
    "şoför", "hizmetli", "mübaşir",
    "infaz ve koruma"
]

ALIM = [
    "personel", "alım", "memur",
    "sınav", "sözleşmeli", "kadro"
]

def gonder(msg):
    u = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    d = {
        "chat_id": CHAT,
        "text": msg,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    requests.post(u, data=d, timeout=15)

def ozetle(url, h):
    try:
        r = requests.get(url, headers=h, timeout=15)
        r.encoding = r.apparent_encoding or "utf-8"
        s = BeautifulSoup(r.text, "html.parser")
        for x in s(["script", "style"]):
            x.decompose()
        m = " ".join(s.get_text(" ").split())
        mk = m.lower()
        kriter = ["ortaöğretim", "p94", "kpssp94", "lise mezunu"]
        if not any(k in mk for k in kriter):
            return None
        p = re.search(r'(50|55|60|65|70|75|80)\s*puan', mk)
        ps = f"{p.group(1)} Puan" if p else "İlanda"
        if "sınav yapılmayacaktır" in mk or "puan sıralaması" in mk:
            ms = "⭐ Mülakatsız"
        else:
            ms = "🗣️ Mülakat/Sözlü"
        return (
            f"🎯 <b>Puan:</b> {ps}\n"
            f"⚖️ <b>Tür:</b> {ms}\n"
            f"📝 <b>Özet:</b> <i>{m[:260]}...</i>\n\n"
        )
    except Exception:
        return None 
    def tara():
    if os.path.exists(DOSYA):
        with open(DOSYA, "r", encoding="utf-8") as f:
            eski = json.load(f)
    else:
        eski = []

    yeni = False
    h = {"User-Agent": "Mozilla/5.0"}
    siteler = [
        ("https://www.resmigazete.gov.tr", "RESMİ GAZETE"),
        ("https://kamuilan.sbb.gov.tr", "SBB KAMU İLAN"),
        (KARIYER, "KARİYER KAPISI")
    ]

    for s_url, s_ad in siteler:
        try:
            r = requests.get(s_url, headers=h, timeout=20)
            r.encoding = "utf-8"
            sp = BeautifulSoup(r.text, "html.parser")
            for a in sp.find_all("a", href=True):
                b = a.get_text(strip=True)
                hr = a["href"]
                if len(b) < 15:
                    continue
                if hr.startswith("http"):
                    lnk = hr
                else:
                    lnk = f"{s_url}/{hr.lstrip('/')}"
                if ".gov.tr" not in lnk:
                    continue
                if lnk in eski:
                    continue
                bk = b.lower()
                if any(k in bk for k in ALIM + P94):
                    oz = ozetle(lnk, h)
                    if oz or any(p in bk for p in P94):
                        msj = (
                            f"🏛 <b>{s_ad} (P94)</b>\n\n"
                            f"📌 <b>İlan:</b> {b}\n\n"
                            f"{oz or ''}"
                            f"🔗 <b>İlan:</b>\n{lnk}\n"
                            f"🚀 <b>Başvuru:</b>\n{KARIYER}"
                        )
                        gonder(msj)
                        eski.append(lnk)
                        yeni = True
        except Exception as e:
            print(s_ad, e)

    if yeni:
        with open(DOSYA, "w", encoding="utf-8") as f:
            json.dump(eski[-300:], f, ensure_ascii=False)

if __name__ == "__main__":
    tara()

