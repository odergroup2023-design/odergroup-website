"""Blog rehberlerinin guncellik kontrolu (salt okunur).

Her blog-*.html icin:
  1. BlogPosting semasindaki dateModified (yoksa datePublished) okunur.
  2. Rehberin dayandigi hizmet sayfalari bulunur (.related kutusundaki,
     blog olmayan ic baglantilar).
  3. Hizmet sayfasinin <main> icindeki gorunen metni, rehberin bu tarihle
     ilk kaydedildigi commit'teki surumle bugunku surum arasinda karsilastirilir. Yalniz kod, stil veya
     olcum etiketi degisikligi sayilmaz; metin degistiyse rehber
     "guncellenmeli" olarak isaretlenir.
  4. sitemap.xml lastmod ile dateModified uyumu ve 12 aydan eski rehberler
     ayrica listelenir.

Hicbir dosyayi degistirmez. Rapor Markdown olarak stdout'a yazilir;
guncellenmesi gereken rehber varsa cikis kodu 10 olur.
"""
import html
import json
import re
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
ESKI_GUN = 365


def git(*a):
    return subprocess.run(["git", *a], cwd=KOK, capture_output=True, text=True).stdout


def gorunen_metin(kaynak):
    m = re.search(r"<main[\s>].*?</main>", kaynak, re.S | re.I)
    s = m.group(0) if m else kaynak
    s = re.sub(r"<(script|style|noscript)\b.*?</\1>", " ", s, flags=re.S | re.I)
    s = re.sub(r"<!--.*?-->", " ", s, flags=re.S)
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def cumleler(metin):
    return [c.strip() for c in re.split(r"(?<=[.!?])\s+", metin) if len(c.strip()) > 3]


def rehber_tarihi(kaynak):
    for blok in re.findall(r'<script type="application/ld\+json">(.*?)</script>', kaynak, re.S):
        try:
            d = json.loads(blok)
        except ValueError:
            continue
        if isinstance(d, dict) and d.get("@type") == "BlogPosting":
            return d.get("dateModified") or d.get("datePublished")
    return None


def dayanilan_sayfalar(kaynak):
    m = re.search(r'<div class="related">(.*?)</div>', kaynak, re.S)
    alan = m.group(1) if m else ""
    linkler = re.findall(r'href="([a-z0-9\-]+\.html)"', alan)
    return [l for l in dict.fromkeys(linkler)
            if not l.startswith("blog") and l not in ("index.html",) and (KOK / l).exists()]


def taban_surum(dosya, tarih):
    """Rehberin bugunku dateModified degerini ilk tasidigi commit.
    Rehber o andan beri icerik olarak guncellenmemistir; hizmet sayfasi
    o commit'teki haliyle karsilastirilir (ayni gun yapilan degisiklikler de yakalanir)."""
    for rev in git("log", "--reverse", "--format=%H", "--", dosya).split():
        if rehber_tarihi(git("show", f"{rev}:{dosya}")) == tarih:
            return rev
    return ""


def main():
    bugun = date.today()
    sitemap = (KOK / "sitemap.xml").read_text(encoding="utf-8")
    guncellenmeli, uyumsuz, eski, incelenen = [], [], [], 0

    for yol in sorted(KOK.glob("blog-*.html")):
        kaynak = yol.read_text(encoding="utf-8")
        tarih = rehber_tarihi(kaynak)
        if not tarih:
            continue
        incelenen += 1

        lm = re.search(rf"/{re.escape(yol.name)}</loc><lastmod>([^<]+)</lastmod>", sitemap)
        if lm and lm.group(1)[:10] != tarih[:10]:
            uyumsuz.append(f"`{yol.name}`: sayfa {tarih[:10]}, sitemap {lm.group(1)[:10]}")

        if bugun - date.fromisoformat(tarih[:10]) > timedelta(days=ESKI_GUN):
            eski.append(f"`{yol.name}` (son güncelleme {tarih[:10]})")

        rev = taban_surum(yol.name, tarih)
        if not rev:
            continue
        for sayfa in dayanilan_sayfalar(kaynak):
            eski_kaynak = git("show", f"{rev}:{sayfa}")
            if not eski_kaynak:
                continue
            once = gorunen_metin(eski_kaynak)
            simdi = gorunen_metin((KOK / sayfa).read_text(encoding="utf-8"))
            if once == simdi:
                continue
            a, b = set(cumleler(once)), set(cumleler(simdi))
            cikan = [c for c in cumleler(once) if c not in b][:4]
            giren = [c for c in cumleler(simdi) if c not in a][:4]
            satir = [f"- **`{yol.name}`** ({tarih[:10]}) → `{sayfa}` metni o tarihten sonra değişti."]
            satir += [f"  - çıkan: {c[:220]}" for c in cikan]
            satir += [f"  - giren: {c[:220]}" for c in giren]
            guncellenmeli.append("\n".join(satir))

    out = [f"# Rehber güncellik raporu — {bugun.isoformat()}", "",
           f"İncelenen rehber: {incelenen}", ""]
    out += ["## Güncellenmesi gerekenler", ""] + (guncellenmeli or ["Yok. Tüm rehberler dayandıkları hizmet sayfalarıyla uyumlu."]) + [""]
    if uyumsuz:
        out += ["## Sitemap tarihi uyumsuz", ""] + [f"- {x}" for x in uyumsuz] + [""]
    if eski:
        out += [f"## {ESKI_GUN} günden uzun süredir güncellenmeyenler (gözden geçirin)", ""] + [f"- {x}" for x in eski] + [""]
    out += ["Bu rapor salt okunurdur; hiçbir yazı otomatik değiştirilmez. "
            "Güncelleme PR ile ve onayla yapılır."]
    print("\n".join(out))
    return 10 if (guncellenmeli or uyumsuz) else 0


if __name__ == "__main__":
    sys.exit(main())
