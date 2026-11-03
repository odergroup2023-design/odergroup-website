#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DURUM.md yi OLCUMDEN uretir. Elle tutulan bolum yoktur.

Neden: elle tutulan durum kaydi eskiyor ve eski kayittan konusmaya yol
aciyor. Bu betik her calismada dosyayi sifirdan yazar; eski kayit diye
bir sey kalmaz.

Giris gerektiren alanlar (Google Isletme Profili, LinkedIn, Bing, Meta)
kosucudan okunamaz. Bunlar ASLA eski degerle doldurulmaz; "OLCULEMEDI —
giris gerekli" olarak yazilir ve SENDEN GEREKEN bolumunde listelenir.
"""
import json, pathlib, datetime, re

KOK = pathlib.Path(__file__).resolve().parent.parent
RAPOR = KOK / "rapor"
BUGUN = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

# Kosucudan olculemeyen, giris gerektiren alanlar
# (ad, ne bakilacak, kac gunde bir)
GIRIS_GEREKLI = [
    ("Google Isletme Profili", "kategoriler, hizmet listesi, yeni yorumlar, haftalik gonderi", 7),
    ("LinkedIn sirket sayfasi", "adres alani, sahipsiz ikinci Oder Group sayfasi, gonderi", 14),
    ("Bing Webmaster Tools", "site ve sitemap kaydi, dizin durumu", 30),
    ("Instagram / YouTube / Facebook", "ad, adres, telefon, site baglantisi", 30),
    ("Kompass ve sektor dizinleri", "kayit var mi, bilgiler ayni mi", 30),
    ("FM / AVM / zincir magaza tedarikci portallari", "kayit durumu", 30),
]

# Sabit bir baslangic gunune gore periyot hesabi; durum dosyasi tutmaya gerek yok.
BASLANGIC = datetime.date(2026, 11, 4)
GUN = (datetime.date.today() - BASLANGIC).days

def gunu_geldi(periyot):
    return GUN % periyot == 0

def kalan_gun(periyot):
    return (-GUN) % periyot

satir = []
def y(s=""):
    satir.append(s)

y("# DURUM — otomatik uretildi")
y("")
y("Son olcum: **%s**" % BUGUN)
y("")
y("> Bu dosya her otomasyon calismasinda OLCUMDEN yeniden yazilir.")
y("> Elle duzenlemeyin; bir sonraki calismada ustune yazilir.")
y("")

# --- Lighthouse ---
y("## Mobil performans (Lighthouse, PSI kotasiz)")
y("")
esik_asan = []
if RAPOR.exists():
    y("| Sayfa | Puan | LCP (ms) | CLS | TBT (ms) | Durum |")
    y("|---|---|---|---|---|---|")
    for f in sorted(RAPOR.glob("*.json")):
        try:
            r = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            y("| %s | - | - | - | - | OKUNAMADI |" % f.stem)
            continue
        a = r.get("audits", {})
        puan = round((r.get("categories", {}).get("performance", {}).get("score") or 0) * 100)
        def sayi(k):
            v = a.get(k, {}).get("numericValue")
            return round(v) if isinstance(v, (int, float)) else None
        lcp, cls_, tbt = sayi("largest-contentful-paint"), sayi("cumulative-layout-shift"), sayi("total-blocking-time")
        lcp_sn = (a.get("largest-contentful-paint", {}).get("numericValue") or 0) / 1000.0
        kotu = lcp_sn > 2.5 or puan < 90
        if kotu:
            esik_asan.append((f.stem, round(lcp_sn, 1), puan))
        y("| %s | %d | %s | %s | %s | %s |" % (
            f.stem, puan,
            lcp if lcp is not None else "-",
            a.get("cumulative-layout-shift", {}).get("displayValue", "-"),
            tbt if tbt is not None else "-",
            "ESIK ASILDI" if kotu else "uygun"))
else:
    y("Olcum raporu bulunamadi.")
y("")
y("Esikler: LCP <= 2,5 sn · CLS <= 0,1 · mobil puan >= 90")
y("")

# --- Depo taramasi ---
y("## Depo taramasi")
y("")
htmlar = sorted(KOK.glob("*.html"))
fbrand = [p.name for p in htmlar if 'class="fbrand"' in p.read_text(encoding="utf-8")]
puny = [p.name for p in htmlar if "xn--odermimarlk-8zb" in p.read_text(encoding="utf-8")]
mobilcss = [p.name for p in htmlar if "mobile.css" in p.read_text(encoding="utf-8")]
y("- Toplam HTML sayfasi: **%d**" % len(htmlar))
y("- C2 marka satiri olan: **%d / %d**" % (len(fbrand), len(htmlar)))
y("- mobile.css baglantisi olan: **%d / %d**" % (len(mobilcss), len(htmlar)))
y("- Punycode adresi kalan dosya: **%d**%s" % (len(puny), (" (" + ", ".join(puny) + ")") if puny else ""))
y("")

# --- Iddia taramasi (kaynak kod uzerinde, kelime sinirli) ---
y("## Iddia taramasi (ham kaynak, kelime sinirli)")
y("")
desenler = {
    "IREC": r"\bIREC\b", "ISO": r"\bISO\b", "7/24": r"7/24",
    "81 il": r"\b81 il\b", "SLA garantisi": r"SLA garantisi",
    "kisa surede": r"k\u0131sa s\u00fcrede", "CAFM": r"\bCAFM\b",
}
metinler = {p.name: p.read_text(encoding="utf-8") for p in htmlar}
for ad in ("llms.txt", "llms-full.txt"):
    f = KOK / ad
    if f.exists():
        metinler[ad] = f.read_text(encoding="utf-8")
bulgu = False
for etiket, desen in desenler.items():
    nerede = [(d, len(re.findall(desen, m))) for d, m in metinler.items() if re.search(desen, m)]
    if nerede:
        bulgu = True
        y("- **%s**: %s" % (etiket, ", ".join("%s (%d)" % (d, n) for d, n in nerede)))
if not bulgu:
    y("Taranan ifadelerin hicbiri bulunmadi.")
y("")

# --- Senden gereken ---
y("## SENDEN GEREKEN — otomasyon bunlara erisemez")
y("")
y("Asagidakiler giris (oturum) gerektirdigi icin kosucudan **olculemez**.")
y("Eski deger yazilmaz; durumlari yalnizca sen dogrulayabilirsin.")
y("")
bugun_kontrol = []
for ad, ne, periyot in GIRIS_GEREKLI:
    if gunu_geldi(periyot):
        bugun_kontrol.append((ad, ne, periyot))
        y("- **%s** — **BUGUN KONTROL ET** (her %d gunde bir) · %s" % (ad, periyot, ne))
    else:
        y("- %s — siradaki kontrol %d gun sonra (her %d gunde bir) · %s" % (ad, kalan_gun(periyot), periyot, ne))
y("")
y("Ayrica otomasyonun ureteMEYECEGI, yalnizca senden gelebilecek veriler:")
y("")
y("- Dogrulanabilir sayilar: tamamlanan proje, hizmet verilen il, bakim sozlesmesi, ortalama mudahale suresi")
y("- Hangi musteri adlarinin yayinlanabilecegi (yoksa tanimli anonim format)")
y("- Ucuncu taraf kayitlari: sektor dizinleri, meslek odasi, tedarikci portallari")
y("")

if esik_asan:
    y("## ACIL — esik asan sayfalar")
    y("")
    for ad, lcp, puan in esik_asan:
        y("- **%s**: LCP %s sn, mobil puan %d" % (ad, lcp, puan))
    y("")
    y("Guvenli duzeltmeler ayni calismada uygulandi. Hala esigin ustundeyse")
    y("tasarimi etkileyen mudahale gerekiyor demektir; bu otomatik yapilmaz.")
    y("")

(KOK / "DURUM.md").write_text("\n".join(satir) + "\n", encoding="utf-8")

print("## Durum kaydi uretildi")
print("")
print("- DURUM.md yazildi (%d satir)" % len(satir))
print("- C2 marka satiri: %d/%d sayfa" % (len(fbrand), len(htmlar)))
print("- Punycode kalan: %d dosya" % len(puny))
if esik_asan:
    print("- ESIK ASAN: " + ", ".join("%s (LCP %s sn)" % (a, b) for a, b, c in esik_asan))
print("- Giris gerektiren alanlar OLCULEMEDI olarak isaretlendi (%d kalem)" % len(GIRIS_GEREKLI))

# Gunu gelen kontroller icin hatirlatma dosyasi; is akisi bunu gorurse issue acar.
hat = RAPOR / "hatirlatma.txt"
RAPOR.mkdir(exist_ok=True)
if bugun_kontrol:
    hat.write_text(
        "\n".join("- %s (her %d gunde bir): %s" % (a, p, n) for a, n, p in bugun_kontrol),
        encoding="utf-8")
    print("- HATIRLATMA: bugun kontrol edilecek %d alan var" % len(bugun_kontrol))
else:
    if hat.exists():
        hat.unlink()
    print("- Bugun giris gerektiren kontrol yok")
