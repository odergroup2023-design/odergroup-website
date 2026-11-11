#!/usr/bin/env python3
"""
IndexNow: degisen sayfalari Bing, Yandex ve IndexNow ortaklarina aninda bildirir
(ChatGPT aramasi Bing dizinini kullanir).

Kullanim: python3 tools/indexnow.py [ESKI_COMMIT] [YENI_COMMIT]
- Iki commit arasinda degisen kok dizindeki .html dosyalari bildirilir.
- Arguman yoksa sitemap.xml icindeki tum adresler bildirilir.
Anahtar, sitenin kokundeki <anahtar>.txt dosyasidir (IndexNow kurali geregi
herkese aciktir, gizli bilgi degildir).
Ag hatasi otomasyonu DURDURMAZ; yalnizca ozete yazilir.
"""
import json, pathlib, re, subprocess, sys, urllib.request, urllib.error

KOK = pathlib.Path(__file__).resolve().parent.parent
SITE = "https://www.odergroup.com.tr"
HOST = "www.odergroup.com.tr"

def anahtar():
    for f in KOK.glob("*.txt"):
        if re.fullmatch(r"[0-9a-f]{32}", f.stem) and f.read_text().strip() == f.stem:
            return f.stem
    return None

def adres(dosya):
    return SITE + "/" if dosya == "index.html" else SITE + "/" + dosya

def degisenler(eski, yeni):
    cikti = subprocess.run(["git", "diff", "--name-only", eski, yeni],
                           cwd=KOK, capture_output=True, text=True).stdout
    return sorted({adres(s) for s in cikti.split() if re.fullmatch(r"[^/]+\.html", s)
                   and (KOK / s).exists() and s not in ("404.html", "tesekkurler.html")})

def sitemap():
    t = (KOK / "sitemap.xml").read_text(encoding="utf-8")
    return re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", t)

def main():
    k = anahtar()
    print("### IndexNow")
    print()
    if not k:
        print("- anahtar dosyasi yok; atlandi")
        return
    liste = degisenler(sys.argv[1], sys.argv[2]) if len(sys.argv) == 3 else sitemap()
    if not liste:
        print("- degisen sayfa yok; bildirim gerekmedi")
        print()
        return
    govde = json.dumps({"host": HOST, "key": k,
                        "keyLocation": "%s/%s.txt" % (SITE, k),
                        "urlList": liste[:10000]}).encode()
    istek = urllib.request.Request("https://api.indexnow.org/indexnow", data=govde,
                                   headers={"Content-Type": "application/json; charset=utf-8"})
    try:
        with urllib.request.urlopen(istek, timeout=30) as y:
            print("- %d adres bildirildi, yanit HTTP %s" % (len(liste), y.status))
    except urllib.error.HTTPError as e:
        print("- bildirim reddedildi: HTTP %s (%d adres)" % (e.code, len(liste)))
    except Exception as e:
        print("- ag hatasi: %s (otomasyon devam eder)" % type(e).__name__)
    print()

if __name__ == "__main__":
    main()
