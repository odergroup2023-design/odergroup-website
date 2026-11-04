#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lighthouse raporlarini okur, MEDYAN alir ve firsat listesi basar.

Neden Python: YAML icinde shell icinde node -e yazmak uc katmanli tirnak
kacisi demek; bir denemede sessizce bos cikti uretti. Betik ayri dosyada
olunca kacis sorunu tamamen kalkar.

Neden medyan: GitHub paylasimli kosuculari degisken. Ayni sayfa ayni gun
1,4 sn ve 4,0 sn olculdu. Tek olcume bakip sayfa suclandırilmaz.
Dosya adlari: rapor/<sayfa>-1.json, -2.json, -3.json
"""
import json, pathlib, statistics, sys

KOK = pathlib.Path(__file__).resolve().parent.parent
RAPOR = KOK / "rapor"
ESIK_LCP = 2500
ESIK_PUAN = 90

# Firsat sirasi: LCP ye en cok etki edenden baslayarak
FIRSATLAR = [
    "render-blocking-resources", "server-response-time", "uses-rel-preload",
    "uses-responsive-images", "modern-image-formats", "efficient-animated-content",
    "unused-javascript", "unused-css-rules", "unminified-javascript",
    "third-party-summary", "font-display", "total-byte-weight",
    "bootup-time", "mainthread-work-breakdown", "uses-long-cache-ttl",
]

def sayi(a, k):
    x = a.get(k) or {}
    v = x.get("numericValue")
    return v if isinstance(v, (int, float)) else None

def kazanc(x):
    d = x.get("details") or {}
    v = d.get("overallSavingsMs")
    if isinstance(v, (int, float)):
        return v
    v = x.get("numericValue")
    return v if isinstance(v, (int, float)) else 0

# --- raporlari sayfaya gore grupla ---
gruplar = {}
if RAPOR.exists():
    for f in sorted(RAPOR.glob("*.json")):
        ad = f.stem
        if "-" in ad and ad.rsplit("-", 1)[-1].isdigit():
            ad = ad.rsplit("-", 1)[0]
        gruplar.setdefault(ad, []).append(f)

if not gruplar:
    print("## Olcum raporu bulunamadi.")
    sys.exit(0)

ozet = []
esik_asan = []

for ad, dosyalar in sorted(gruplar.items()):
    kosular = []
    for f in dosyalar:
        try:
            kosular.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception:
            pass
    if not kosular:
        ozet.append((ad, None, None, None, None, 0))
        continue
    def med(fn):
        d = [x for x in (fn(k) for k in kosular) if x is not None]
        return statistics.median(d) if d else None
    puan = med(lambda k: ((k.get("categories") or {}).get("performance") or {}).get("score"))
    lcp  = med(lambda k: sayi(k.get("audits") or {}, "largest-contentful-paint"))
    cls_ = med(lambda k: sayi(k.get("audits") or {}, "cumulative-layout-shift"))
    tbt  = med(lambda k: sayi(k.get("audits") or {}, "total-blocking-time"))
    puan100 = round((puan or 0) * 100)
    ozet.append((ad, puan100, lcp, cls_, tbt, len(kosular)))
    if (lcp or 0) > ESIK_LCP or puan100 < ESIK_PUAN:
        # firsatlar icin medyana en yakin kosuyu sec
        en_iyi = min(kosular, key=lambda k: abs((sayi(k.get("audits") or {}, "largest-contentful-paint") or 0) - (lcp or 0)))
        esik_asan.append((ad, lcp, puan100, en_iyi))

print("## Mobil Lighthouse — MEDYAN")
print("")
print("| Sayfa | Kosu | Puan | LCP | CLS | TBT | Durum |")
print("|---|---|---|---|---|---|---|")
for ad, puan, lcp, cls_, tbt, n in ozet:
    if puan is None:
        print("| %s | 0 | - | - | - | - | OKUNAMADI |" % ad)
        continue
    kotu = (lcp or 0) > ESIK_LCP or puan < ESIK_PUAN
    print("| %s | %d | %d | %.1f sn | %.3f | %d ms | %s |" % (
        ad, n, puan, (lcp or 0) / 1000.0, cls_ or 0, round(tbt or 0),
        "ESIK ASILDI" if kotu else "uygun"))
print("")
print("Esikler: LCP <= 2,5 sn · CLS <= 0,1 · mobil puan >= 90")
print("Degerler %d kosunun medyanidir; tek olcum gurultusu boylece elenir." % max(len(v) for v in gruplar.values()))
print("")

if not esik_asan:
    print("Esik asan sayfa yok.")
    sys.exit(0)

print("## Firsat listesi — hangi kaynak kac ms geciktiriyor")
for ad, lcp, puan, k in esik_asan:
    a = k.get("audits") or {}
    print("")
    print("### %s — LCP %.1f sn, puan %d" % (ad, (lcp or 0) / 1000.0, puan))
    print("")
    el = a.get("largest-contentful-paint-element") or {}
    try:
        it = ((el.get("details") or {}).get("items") or [])[0]
        n0 = ((it.get("items") or [])[0]).get("node") or {}
        kod = (n0.get("snippet") or n0.get("selector") or "-")[:140]
        print("LCP ogesi: `%s`" % kod)
        print("")
    except Exception:
        pass
    print("| Firsat | Kazanc | Not |")
    print("|---|---|---|")
    n = 0
    for key in FIRSATLAR:
        x = a.get(key)
        if not x:
            continue
        ms = kazanc(x)
        skor = x.get("score")
        if skor is not None and skor >= 0.9 and ms < 100:
            continue
        print("| %s | %s | %s |" % (
            (x.get("title") or key)[:60],
            (str(round(ms)) + " ms") if ms else "-",
            str(x.get("displayValue") or "")[:46]))
        n += 1
    if n == 0:
        print("| (Lighthouse belirgin firsat bulmadi) | - | - |")
    zincir = a.get("critical-request-chains") or {}
    if zincir.get("displayValue"):
        print("")
        print("Kritik istek zinciri: %s" % zincir["displayValue"])
