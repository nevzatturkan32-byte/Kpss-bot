import os
import re
import json
import datetime
import requests
from bs4 import BeautifulSoup

NTFY_KANAL = "nevzat_kpss_p94_takip_2026"
KARIYER = "https://isealimkariyerkapisi.cbiko.gov.tr"
ISKUR = "https://www.iskur.gov.tr/iskur/kurum-disi-kamu-isci-alimi-ilanlari/"
DOSYA = "ilanlar.json"

P94 = [
    "ortaöğretim", "p94", "kpssp94",
    "lise", "güvenlik", "destek personeli",
    "şoför", "hizmetli", "mübaşir",
    "infaz ve koruma", "zabıta", "itfaiye"
]

ALIM = [
    "personel", "alım", "memur",
    "sınav", "sözleşmeli", "kadro",
    "belediye", "işçi", "işçisi", "a.ş."
]

def bildirim_at(baslik, kurum, link):
    try:
        requests.post(
            f"https://ntfy.sh/{NTFY_KANAL}",
            data=f"{kurum}: {baslik}".encode("utf-8"),
            headers={
                "Title": "Yeni P94 / Kamu Ilani!",
                "Click": link,
                "Tags": "loudspeaker"
            },
            timeout=10
        )
    except Exception:
        pass

def ozetle(url, h):
    if url.lower().endswith(".pdf"):
        return {
            "puan": "KPSS Şartsız / PDF",
            "tur": "İŞKUR / Belediye Şirketi",
            "ozet": "İŞKUR Kurum Dışı Kamu İşçi Alımı PDF duyurusu."
        }
    try:
        r = requests.get(url, headers=h, timeout=15)
        r.encoding = r.apparent_encoding or "utf-8"
        s = BeautifulSoup(r.text, "html.parser")
        for x in s(["script", "style"]):
            x.decompose()
        m = " ".join(s.get_text(" ").split())
        mk = m.lower()
        kriter = ["ortaöğretim", "p94", "kpssp94", "lise mezunu", "lise düzeyinde"]
        if not any(k in mk for k in kriter):
            return None
        p = re.search(r'(50|55|60|65|70|75|80)\s*puan', mk)
        ps = f"{p.group(1)} Puan" if p else "İlanda Belirtilmiş"
        ms = "Mülakatsız" if ("sınav yapılmayacaktır" in mk or "puan sıralaması" in mk) else "Mülakat / Sözlü"
        return {"puan": ps, "tur": ms, "ozet": m[:240] + "..."}
    except Exception:
        return None

def tara():
    if os.path.exists(DOSYA):
        with open(DOSYA, "r", encoding="utf-8") as f:
            kayitlar = json.load(f)
    else:
        kayitlar = []

    mevcut_linkler = {x["link"] for x in kayitlar}
    yeni_eklendi = False
    bugun = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
    h = {"User-Agent": "Mozilla/5.0"}

    siteler = [
        ("https://www.resmigazete.gov.tr", "RESMİ GAZETE"),
        ("https://kamuilan.sbb.gov.tr", "SBB KAMU İLAN"),
        (KARIYER, "KARİYER KAPISI"),
        (ISKUR, "İŞKUR KURUM DIŞI")
    ]

    for s_url, s_ad in siteler:
        try:
            r = requests.get(s_url, headers=h, timeout=20)
            r.encoding = "utf-8"
            sp = BeautifulSoup(r.text, "html.parser")
            for a in sp.find_all("a", href=True):
                b = a.get_text(strip=True)
                hr = a["href"]
                if len(b) < 10:
                    continue
                lnk = hr if hr.startswith("http") else f"{s_url}/{hr.lstrip('/')}"
                if not (".gov.tr" in lnk or ".bel.tr" in lnk) or lnk in mevcut_linkler:
                    continue
                bk = b.lower()
                if any(k in bk for k in ALIM + P94):
                    detay = ozetle(lnk, h)
                    if detay or any(p in bk for p in P94) or ".pdf" in lnk.lower():
                        bilgi = detay or {"puan": "İlanda", "tur": "Kamu / Belediye", "ozet": b}
                        kayitlar.insert(0, {
                            "kurum": s_ad,
                            "baslik": b,
                            "puan": bilgi["puan"],
                            "tur": bilgi["tur"],
                            "ozet": bilgi["ozet"],
                            "link": lnk,
                            "tarih": bugun
                        })
                        mevcut_linkler.add(lnk)
                        bildirim_at(b, s_ad, lnk)
                        yeni_eklendi = True
        except Exception as e:
            print(s_ad, e)

    if yeni_eklendi or not os.path.exists(DOSYA):
        with open(DOSYA, "w", encoding="utf-8") as f:
            json.dump(kayitlar[:200], f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    tara()
