/* Kesif/teklif formu (FormSubmit).
   FormSubmit'in yaniti 20 sn'yi asabiliyor; e-posta yine de iletiliyor (26.11.2026 testi).
   Bu yuzden ziyaretci beklemez ve hata gormez:
   - Talep navigator.sendBeacon ile tarayiciya teslim edilir. Tarayici, sayfa degisse
     bile istegi arka planda FormSubmit'e ulastirir.
   - Ziyaretci hemen tesekkurler.html sayfasina gecer.
   - sendBeacon yoksa ya da talebi kabul etmezse, formun kendi (normal) gonderimi
     yapilir; FormSubmit isi bitince _next ile yine tesekkurler.html'e yonlendirir.
   Analitik olaylara ad, telefon, e-posta veya serbest metin gonderilmez. */
(function () {
  'use strict';
  var form = document.querySelector('form.form[action^="https://formsubmit.co/"]');
  if (!form) return;
  var button = form.querySelector('button[type="submit"]');
  var gonderildi = false;

  function olay(yontem) {
    var konu = (form.elements.konu && form.elements.konu.value) || 'Genel teklif';
    window.dataLayer = window.dataLayer || [];
    window.dataLayer.push({
      event: 'generate_lead',
      legacy_event: 'teklif_formu_gonderildi',
      sayfa: window.location.pathname,
      form_name: 'kesif_teklif_formu',
      lead_type: 'kesif_teklif',
      konu: konu,
      method: yontem
    });
    window.gtag = window.gtag || function () { window.dataLayer.push(arguments); };
    window.gtag('event', 'generate_lead', {
      form_name: 'kesif_teklif_formu', lead_type: 'kesif_teklif', konu: konu, method: yontem,
      transport_type: 'beacon'
    });
  }

  form.addEventListener('submit', function (event) {
    if (gonderildi) { event.preventDefault(); return; }
    if (!form.checkValidity()) return; /* tarayici eksik alanlari gosterir */
    var honey = form.querySelector('[name="_honey"]');
    if (honey && honey.value) { event.preventDefault(); return; }

    var veri = new URLSearchParams();
    new FormData(form).forEach(function (deger, ad) {
      if (typeof deger === 'string') veri.append(ad, deger);
    });
    veri.append('_url', window.location.href);

    var teslim = false;
    try {
      teslim = !!(navigator.sendBeacon && navigator.sendBeacon(form.action, veri));
    } catch (e) { teslim = false; }

    gonderildi = true;
    if (button) { button.disabled = true; button.textContent = 'Talebiniz gönderiliyor…'; }

    if (teslim) {
      event.preventDefault();
      olay('formsubmit_beacon');
      window.setTimeout(function () { window.location.assign('tesekkurler.html'); }, 150);
    } else {
      /* Yedek yol: formun normal gonderimi (preventDefault yok). Hata mesaji yok. */
      olay('formsubmit_native');
    }
  });
})();
