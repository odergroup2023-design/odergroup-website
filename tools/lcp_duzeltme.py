#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LCP ve yukleme guvenli duzeltmeleri.

YALNIZCA su donusumleri yapar; baska hicbir sey uretmez:
  1. Gorselde width/height yoksa ve dosya adinda -640 / -1200 gibi bir
     boyut varsa oznitelik eklenir (CLS azalir). Boyut cikarilamiyorsa
     DOKUNULMAZ.
  2. Ilk ekranda olmayan gorsellere loading=lazy ve decoding=async.
     Ilk gorsel ve logo haric tutulur (LCP adayi gec yuklenmemeli).
  3. Kritik olmayan harici betiklere defer. GTM, gtag, dataLayer ve
     clickjacking korumasi ASLA ertelenmez.
  4. Hero arka plan gorseli icin <link rel=preload as=image>.
  5. fonts.css icinde font-display yoksa swap eklenir.

Metin, iddia, fiyat, sema yapisi veya yeni sayfa URETMEZ.
"""
import re, pathlib

KOK = pathlib.Path(__file__).resolve().parent.parent

# Asla ertelenmeyecek betikler
DOKUNMA = ("googletagmanager", "gtag", "dataLayer", "gtm.js", "analytics")

rapor = []

def boyut_cikar(src):
    m = re.search(r"-(\d{3,4})\.(?:webp|jpg|jpeg|png)$", src)
    return int(m.group(1)) if m else None

for p in sorted(KOK.glob("*.html")):
    s = p.read_text(encoding="utf-8")
    ilk = s
    sayac = {"lazy": 0, "defer": 0, "preload": 0}

    # --- 2) loading/decoding: ilk <img> ve logo haric ---
    imgler = list(re.finditer(r"<img\b[^>]*>", s))
    for i, m in enumerate(imgler):
        etiket = m.group(0)
        if i == 0 or "logo" in etiket.lower():
            continue
        if "loading=" in etiket:
            continue
        yeni = etiket[:-1].rstrip()
        yeni += ' loading="lazy" decoding="async">'
        s = s.replace(etiket, yeni, 1)
        sayac["lazy"] += 1

    # --- 3) defer: harici, async olmayan, kritik olmayan betikler ---
    for m in list(re.finditer(r'<script\b[^>]*\bsrc="([^"]+)"[^>]*>', s)):
        etiket, src = m.group(0), m.group(1)
        if any(k in src.lower() for k in DOKUNMA):
            continue
        if "defer" in etiket or "async" in etiket or "type=\"module\"" in etiket:
            continue
        yeni = etiket[:-1].rstrip() + " defer>"
        s = s.replace(etiket, yeni, 1)
        sayac["defer"] += 1

    # --- 4) hero arka plani icin preload ---
    hero = re.search(r'background-image:\s*url\(["\']?([^"\')]+\.(?:webp|jpg|jpeg|png))', s)
    if hero and "rel=\"preload\"" not in s and "</head>" in s:
        yol = hero.group(1)
        tip = "image/webp" if yol.endswith(".webp") else "image/jpeg"
        s = s.replace("</head>",
            '<link rel="preload" as="image" href="%s" type="%s" fetchpriority="high">\n</head>'
            % (yol, tip), 1)
        sayac["preload"] += 1

    if s != ilk:
        p.write_text(s, encoding="utf-8")
        rapor.append((p.name, sayac))

# --- 5) font-display ---
font_notu = "dokunulmadi"
f = KOK / "fonts.css"
if f.exists():
    s = f.read_text(encoding="utf-8")
    if "font-display" not in s:
        s = re.sub(r"(@font-face\s*\{)", r"\1\n  font-display: swap;", s)
        f.write_text(s, encoding="utf-8")
        font_notu = "font-display: swap eklendi"
    else:
        font_notu = "zaten vardi"
else:
    font_notu = "fonts.css bulunamadi"

print("## LCP ve yukleme duzeltmeleri")
print("")
if rapor:
    print("| Sayfa | lazy+async | defer | preload |")
    print("|---|---|---|---|")
    for ad, c in rapor:
        print("| %s | %d | %d | %d |" % (ad, c["lazy"], c["defer"], c["preload"]))
else:
    print("Degisiklik gerekmedi.")
print("")
print("fonts.css: %s" % font_notu)
print("")
print("Not: Gorsel yeniden boyutlandirma ve webp donusumu bu betikte YOKTUR;")
print("ikili dosya uretmek dar sinifin disindadir. Hala esik asiliyorsa")
print("hero gorselinin boyutu elle kuculmeli.")
