#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Toplu duzenleme — GitHub Actions kosucusunda calisir.

(j) C2 marka satiri her sayfanin alt bilgisine eklenir.
(k) Punycode temizligi: xn--odermimarlk-8zb.com -> odermimarlik.com

Kurallar:
  - Zaten varsa dokunmaz (fbrand sinifini arar).
  - Footer kapanis etiketi bulamadigi dosyayi ATLAR ve raporlar.
  - Yonlendirme sayfalarini (meta refresh) atlar.
  - Hicbir sey silmez; yalnizca ekler ve adres degistirir.
"""
import pathlib

KOK = pathlib.Path(__file__).resolve().parent.parent

MARKA = (
    '<div class="fbrand" style="margin-top:16px;font-size:.86rem;'
    'opacity:.82;line-height:1.6">\n'
    '  <strong>\u00d6der Mimarl\u0131k</strong> ve <strong>\u00d6DER Enerji</strong>, '
    '\u00d6DER GROUP markalar\u0131d\u0131r.\n'
    '  <a href="https://odermimarlik.com/" target="_blank" rel="noopener">'
    '\u0130\u00e7 mimarl\u0131k ve mobilya: odermimarlik.com</a> \u00b7\n'
    '  <a href="https://oderenerji.com/" target="_blank" rel="noopener">'
    'Enerji \u00fcr\u00fcnleri: oderenerji.com</a>\n'
    '</div>\n'
)

PUNYCODE = "xn--odermimarlk-8zb.com"
HEDEF = "odermimarlik.com"

eklendi = []
zaten_vardi = []
atlandi = []
punycode_duzeltildi = []

for p in sorted(KOK.glob("*.html")):
    s = p.read_text(encoding="utf-8")
    ilk = s

    if PUNYCODE in s:
        punycode_duzeltildi.append((p.name, s.count(PUNYCODE)))
        s = s.replace(PUNYCODE, HEDEF)

    bas = s[:4000].lower()
    if "http-equiv" in bas and "refresh" in bas:
        atlandi.append((p.name, "yonlendirme sayfasi"))
    elif 'class="fbrand"' in s:
        zaten_vardi.append(p.name)
    elif "</footer>" not in s:
        atlandi.append((p.name, "footer kapanis etiketi yok"))
    else:
        s = s.replace("</footer>", MARKA + "</footer>", 1)
        eklendi.append(p.name)

    if s != ilk:
        p.write_text(s, encoding="utf-8")

for ad in ("llms.txt", "llms-full.txt", "sitemap.xml"):
    f = KOK / ad
    if f.exists():
        s = f.read_text(encoding="utf-8")
        if PUNYCODE in s:
            punycode_duzeltildi.append((ad, s.count(PUNYCODE)))
            f.write_text(s.replace(PUNYCODE, HEDEF), encoding="utf-8")

print("## Toplu duzenleme sonucu")
print("")
print("Marka satiri eklendi (%d): %s" % (len(eklendi), ", ".join(eklendi) or "-"))
print("")
print("Zaten vardi (%d): %s" % (len(zaten_vardi), ", ".join(zaten_vardi) or "-"))
print("")
if punycode_duzeltildi:
    print("Punycode duzeltildi:")
    for ad, n in punycode_duzeltildi:
        print("  - %s: %d gecis" % (ad, n))
else:
    print("Punycode gecisi bulunmadi.")
print("")
if atlandi:
    print("ATLANDI (elle bakilacak):")
    for ad, sebep in atlandi:
        print("  - %s: %s" % (ad, sebep))
else:
    print("Atlanan dosya yok.")
