#!/usr/bin/env python3
"""Bir kerelik: mobil LCP icin kucuk varliklar uretir.

1) Latin-ext font dosyalarini (archivo-2, inter-9) yalniz sitede GERCEKTEN
   kullanilan karakterlere indirger -> fonts/<ad>-tr.woff2 (eski dosyalar
   silinmez). fonts.css'te ilgili iki @font-face yeni dosyaya ve tam
   karakter listesine cevrilir.
2) Kapak gorselinin 760 px surumunu uretir (1,75x ekranlar icin) ve
   index.html'deki 1. slayt ile mobil preload'a 1.75x aday olarak ekler.

Her adim dogrulanir; bir kontrol tutmazsa betik hata verir ve is akisi
commit yapmaz. Ozet $GITHUB_STEP_SUMMARY'ye yazilir.
"""
import os
import re
import sys
import unicodedata
from pathlib import Path

from fontTools.ttLib import TTFont
from fontTools import subset
from PIL import Image

KOK = Path(__file__).resolve().parent.parent
OZET = []


def yaz(s=""):
    print(s)
    OZET.append(s)


def aralik_coz(ur):
    """'U+0100-02BA, U+0304' -> kod noktasi kumesi"""
    s = set()
    for p in ur.split(","):
        p = p.strip().upper().replace("U+", "")
        if not p:
            continue
        if "-" in p:
            a, b = p.split("-")
            s.update(range(int(a, 16), int(b, 16) + 1))
        else:
            s.add(int(p, 16))
    return s


def aralik_yaz(kodlar):
    kodlar = sorted(kodlar)
    parcalar, i = [], 0
    while i < len(kodlar):
        j = i
        while j + 1 < len(kodlar) and kodlar[j + 1] == kodlar[j] + 1:
            j += 1
        a, b = kodlar[i], kodlar[j]
        parcalar.append(f"U+{a:04X}" if a == b else f"U+{a:04X}-{b:04X}")
        i = j + 1
    return ", ".join(parcalar)


def metin_karakterleri():
    """Gorunen metin olabilecek tum karakterler (html + js)."""
    k = set()
    dosyalar = sorted(KOK.glob("*.html")) + sorted(KOK.glob("*.js"))
    for f in dosyalar:
        t = f.read_text(encoding="utf-8", errors="ignore")
        k.update(ord(c) for c in t)
        # NFC/NFD farki: ayrik yazilmis harfleri de kapsa
        k.update(ord(c) for c in unicodedata.normalize("NFC", t))
    return k, len(dosyalar)


def birlesik_isaretler():
    bulunan = []
    for f in sorted(KOK.glob("*.html")):
        for n, satir in enumerate(f.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            for c in satir:
                if 0x300 <= ord(c) <= 0x36F or 0x400 <= ord(c) <= 0x52F:
                    bulunan.append(f"{f.name}:{n} U+{ord(c):04X}")
    return bulunan


# ---------------------------------------------------------------- fontlar
TURKCE = {0x011E, 0x011F, 0x0130, 0x015E, 0x015F}  # Ğ ğ İ Ş ş


def fontlar():
    css_yol = KOK / "fonts.css"
    css = css_yol.read_text(encoding="utf-8")
    kullanilan, n = metin_karakterleri()
    yaz(f"### Fontlar\nTaranan dosya: {n}")

    bloklar = re.findall(r"@font-face\s*\{[^}]*\}", css)
    yeni_css = css
    for kaynak, latin_ad in (("archivo-2", "archivo-3"), ("inter-9", "inter-10")):
        blok = next(b for b in bloklar if f"fonts/{kaynak}.woff2" in b)
        ur = re.search(r"unicode-range:\s*([^;]+);", blok).group(1)
        kapsam = aralik_coz(ur)
        latin_blok = next(b for b in bloklar if f"fonts/{latin_ad}.woff2" in b)
        latin = aralik_coz(re.search(r"unicode-range:\s*([^;]+);", latin_blok).group(1))
        gerek = ((kullanilan & kapsam) - latin) | TURKCE

        giris = KOK / "fonts" / f"{kaynak}.woff2"
        cikis = KOK / "fonts" / f"{kaynak}-tr.woff2"
        cmap_eski = TTFont(giris).getBestCmap()
        eksik_kaynakta = sorted(c for c in gerek if c not in cmap_eski)
        gerek = {c for c in gerek if c in cmap_eski}

        opt = subset.Options()
        opt.flavor = "woff2"
        opt.layout_features = ["*"]
        opt.name_IDs = ["*"]
        opt.notdef_outline = True
        f = TTFont(giris)
        s = subset.Subsetter(opt)
        s.populate(unicodes=sorted(gerek))
        s.subset(f)
        f.flavor = "woff2"
        f.save(cikis)

        # dogrulama
        yeni = TTFont(cikis)
        cmap = yeni.getBestCmap()
        eksik = sorted(c for c in gerek if c not in cmap)
        if eksik:
            sys.exit(f"HATA {cikis.name}: eksik {aralik_yaz(eksik)}")
        if "fvar" in TTFont(giris) and "fvar" not in yeni:
            sys.exit(f"HATA {cikis.name}: degisken agirlik tablosu kayboldu")

        eski_kb = giris.stat().st_size / 1024
        yeni_kb = cikis.stat().st_size / 1024
        yaz(f"- {kaynak}: {eski_kb:.0f} KB -> {cikis.name} {yeni_kb:.1f} KB; "
            f"karakter: {aralik_yaz(gerek)}"
            + (f"; kaynak fontta zaten yok: {aralik_yaz(eksik_kaynakta)}" if eksik_kaynakta else ""))

        yeni_blok = blok.replace(f"fonts/{kaynak}.woff2", f"fonts/{kaynak}-tr.woff2")
        yeni_blok = yeni_blok.replace(ur, aralik_yaz(gerek))
        yeni_css = yeni_css.replace(blok, yeni_blok)

    css_yol.write_text(yeni_css, encoding="utf-8")
    b = birlesik_isaretler()
    if b:
        yaz(f"- Not: metinde birlesik isaret / Kiril karakteri var ({len(b)}); "
            f"ek font dosyasi yukletiyor: {', '.join(b[:12])}")
    else:
        yaz("- Metinde birlesik isaret / Kiril karakteri yok.")


# ---------------------------------------------------------------- gorsel
def kapak():
    yaz("\n### Kapak gorseli")
    kaynak = KOK / "optimized" / "oder-group-fuar-standi-1200.webp"
    cikis = KOK / "optimized" / "oder-group-fuar-standi-760.webp"
    im = Image.open(kaynak)
    w, h = im.size
    yeni = im.resize((760, round(h * 760 / w)), Image.LANCZOS)
    yeni.save(cikis, "WEBP", quality=74, method=6)
    yaz(f"- {kaynak.name} {kaynak.stat().st_size/1024:.0f} KB ({w}x{h}) -> "
        f"{cikis.name} {cikis.stat().st_size/1024:.0f} KB ({yeni.size[0]}x{yeni.size[1]})")

    yol = KOK / "index.html"
    t = yol.read_text(encoding="utf-8")
    eski_set = ("image-set(url('optimized/oder-group-fuar-standi-640.webp') 1x,"
                "url('optimized/oder-group-fuar-standi-1200.webp') 2x)")
    yeni_set = ("image-set(url('optimized/oder-group-fuar-standi-640.webp') 1x,"
                "url('optimized/oder-group-fuar-standi-760.webp') 1.75x,"
                "url('optimized/oder-group-fuar-standi-1200.webp') 2x)")
    eski_pre = ('imagesrcset="optimized/oder-group-fuar-standi-640.webp 1x, '
                'optimized/oder-group-fuar-standi-1200.webp 2x"')
    yeni_pre = ('imagesrcset="optimized/oder-group-fuar-standi-640.webp 1x, '
                'optimized/oder-group-fuar-standi-760.webp 1.75x, '
                'optimized/oder-group-fuar-standi-1200.webp 2x"')
    if t.count(eski_set) != 1 or t.count(eski_pre) != 1:
        sys.exit(f"HATA index.html: beklenen kalip bulunamadi "
                 f"(slayt {t.count(eski_set)}, preload {t.count(eski_pre)})")
    t = t.replace(eski_set, yeni_set).replace(eski_pre, yeni_pre)
    yol.write_text(t, encoding="utf-8")
    yaz("- index.html: 1. slayt ve mobil preload'a 760 px (1.75x) eklendi.")


if __name__ == "__main__":
    fontlar()
    kapak()
    oz = os.environ.get("GITHUB_STEP_SUMMARY")
    if oz:
        with open(oz, "a", encoding="utf-8") as f:
            f.write("## Mobil varlik uretimi\n" + "\n".join(OZET) + "\n")
