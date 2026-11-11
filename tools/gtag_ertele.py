#!/usr/bin/env python3
"""
Olcum etiketlerini (GTM + GA4 gtag.js) ilk boyamadan sonraya erteler.

DAR SINIF: yalniz <head> icindeki yukleme zamanlamasi degisir; metin,
gorsel, sema, baglanti degismez. Ana sayfada (PR #44/#47/#53) olculdu:
TBT 859 -> 100 ms, puan 63/74 -> 92.

Tetikleyiciler: ilk etkilesim (tiklama, dokunma, tus, kaydirma) aninda;
etkilesim yoksa load + 3,5 sn. dataLayer kuyrugu satir ici kalir,
gtag()/dataLayer.push() cagrilari kaybolmaz; kutuphane gelince islenir.

Guvenlik:
- '_gtmYukle' iceren sayfa zaten ertelenmistir -> dokunulmaz.
- GTM cagrisi tam kalibiyla bulunamazsa sayfa ATLANIR (tahmin yok).
- Ayni girdiyle ikinci calisma hicbir sey degistirmez.
"""
import pathlib, re

KOK = pathlib.Path(__file__).resolve().parent.parent

GTAG = re.compile(r'<script async src="(https://www\.googletagmanager\.com/gtag/js\?id=G-[A-Z0-9]+)"></script>')
GTM = re.compile(
    r"\(function\(w,d,s,l,i\)\{(?P<govde>.*?)\}\)\(window,document,'script','dataLayer','(?P<id>GTM-[A-Z0-9]+)'\);",
    re.S)

def ertele(html):
    if "_gtmYukle" in html:
        return None, "zaten ertelenmis"
    m = GTM.search(html)
    if not m:
        return None, "GTM kalibi yok"
    g = GTAG.search(html)
    gtag_satir = ""
    if g:
        gtag_satir = ("var g=document.createElement('script');g.async=true;"
                      "g.src='%s';document.head.appendChild(g);" % g.group(1))
    yeni = (
        "var _gtmYukle=function(w,d,s,l,i){%s};\n"
        "/* LCP: olcum etiketleri ilk boyamadan sonra yuklenir (tools/gtag_ertele.py).\n"
        "   Etkilesim aninda, aksi halde load + 3,5 sn. dataLayer kuyrugu korunur. */\n"
        "(function(){\n"
        "  var yuklendi=false;\n"
        "  function basla(){\n"
        "    if(yuklendi) return; yuklendi=true;\n"
        "    _gtmYukle(window,document,'script','dataLayer','%s');\n"
        "    %s\n"
        "  }\n"
        "  ['click','touchstart','keydown','scroll'].forEach(function(o){\n"
        "    addEventListener(o,basla,{once:true,passive:true});\n"
        "  });\n"
        "  if(document.readyState==='complete'){ setTimeout(basla,3500); }\n"
        "  else { addEventListener('load',function(){ setTimeout(basla,3500); },{once:true}); }\n"
        "})();"
    ) % (m.group("govde"), m.group("id"), gtag_satir)
    html = html[:m.start()] + yeni + html[m.end():]
    if g:
        html = GTAG.sub("", html, count=1)
    return html, "ertelendi" + (" (GTM + gtag)" if g else " (yalniz GTM)")

def main():
    sonuc = {}
    for f in sorted(KOK.glob("*.html")):
        eski = f.read_text(encoding="utf-8")
        yeni, durum = ertele(eski)
        if yeni is not None and yeni != eski:
            f.write_text(yeni, encoding="utf-8")
        sonuc.setdefault(durum, []).append(f.name)
    print("### Olcum etiketi ertelemesi")
    print()
    for durum, ad in sorted(sonuc.items()):
        print("- %s (%d): %s" % (durum, len(ad), ", ".join(ad)))
    print()

if __name__ == "__main__":
    main()
