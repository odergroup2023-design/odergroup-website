/* Kesif/teklif formu (FormSubmit).
   Kural: ziyaretci beklemez, hata mesaji gormez, talep kaybolmaz.
   - Gonder'e basilinca form aninda "Talebiniz alindi" kutusuyla degisir.
   - Talep ayni sayfada, arka planda FormSubmit'e gonderilir (ajax). Bu yol tum
     testlerde e-postayi teslim etti; yanit 20 sn'yi asabildigi icin 90 sn beklenir.
     Istek sunucuya ulastiktan sonra sekme kapansa bile e-posta gidiyor (26.11.2026 testi).
   - Basarisiz olursa 3 sn sonra bir kez daha denenir; o da olmazsa ayni veri
     sendBeacon ile duz form adresine birakilir. Ziyaretciye hata gosterilmez.
   - 27.11.2026: yalniz sendBeacon kullanan surumde bir gercek gonderim e-postaya
     dusmedi; bu yuzden beacon yalniz son yedek.
   Analitik olaylara ad, telefon, e-posta veya serbest metin gonderilmez. */
(function () {
  'use strict';
  var form = document.querySelector('form.form[action^="https://formsubmit.co/"]');
  if (!form) return;
  var ajaxUrl = form.action.replace('https://formsubmit.co/', 'https://formsubmit.co/ajax/');
  var gonderildi = false;

  function olay(ad, ek) {
    var p = { form_name: 'kesif_teklif_formu' };
    for (var k in ek) p[k] = ek[k];
    window.dataLayer = window.dataLayer || [];
    var d = { event: ad, sayfa: window.location.pathname };
    for (var j in p) d[j] = p[j];
    window.dataLayer.push(d);
    window.gtag = window.gtag || function () { window.dataLayer.push(arguments); };
    window.gtag('event', ad, p);
  }

  function tesekkur() {
    var kutu = document.createElement('div');
    kutu.setAttribute('role', 'status');
    kutu.setAttribute('tabindex', '-1');
    kutu.style.cssText = 'padding:28px 24px;border:1px solid rgba(255,255,255,.25);line-height:1.7';
    kutu.innerHTML = '<p style="font:600 1.25rem Archivo,sans-serif;margin:0 0 8px">Talebiniz alındı. Teşekkürler.</p>' +
      '<p style="margin:0">Keşif ve teklif ücretsizdir; 24 saat içinde size dönüş yapıyoruz. ' +
      'Acil durumlar için <a href="tel:+905345472239" style="text-decoration:underline">+90 534 547 22 39</a> ' +
      'numarasından telefon veya WhatsApp ile de ulaşabilirsiniz.</p>';
    form.style.display = 'none';
    form.parentNode.insertBefore(kutu, form.nextSibling);
    try { kutu.focus({ preventScroll: true }); kutu.scrollIntoView({ block: 'center' }); } catch (e) {}
  }

  function ajax(payload, sure) {
    var c = window.AbortController ? new AbortController() : null;
    var t = c ? window.setTimeout(function () { c.abort(); }, sure) : null;
    return fetch(ajaxUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
      body: JSON.stringify(payload),
      signal: c ? c.signal : undefined
    }).then(function (r) {
      return r.json().then(function (j) {
        if (!r.ok || !(j.success === true || j.success === 'true')) throw new Error('red');
        return true;
      });
    }).finally(function () { if (t) window.clearTimeout(t); });
  }

  function beacon(payload) {
    try {
      var v = new URLSearchParams();
      for (var k in payload) v.append(k, payload[k]);
      return !!(navigator.sendBeacon && navigator.sendBeacon(form.action, v));
    } catch (e) { return false; }
  }

  form.addEventListener('submit', function (event) {
    if (gonderildi) { event.preventDefault(); return; }
    if (!form.checkValidity()) return; /* tarayici eksik alanlari gosterir */
    var honey = form.querySelector('[name="_honey"]');
    if (honey && honey.value) { event.preventDefault(); return; }
    if (!window.fetch || !window.Promise || !window.FormData) return; /* cok eski tarayici: normal gonderim */

    event.preventDefault();
    gonderildi = true;
    var payload = {};
    new FormData(form).forEach(function (deger, ad) { if (typeof deger === 'string') payload[ad] = deger; });
    payload._url = window.location.href;
    /* Her talebe ayri konu: Gmail onceki (silinmis) yazismalara baglamasin. */
    if (payload.ad) payload._subject = (payload._subject || 'Yeni Keşif/Teklif Talebi') + ' — ' + payload.ad.slice(0, 60);
    var konu = payload.konu || 'Genel teklif';

    tesekkur();
    olay('form_submit_click', { konu: konu });

    ajax(payload, 90000).catch(function (e) {
      /* 90 sn zaman asimi: istek sunucuya ulasmistir, e-posta gider (tekrar gonderip cift kayit yaratma). */
      if (e && e.name === 'AbortError') return 'gecikmeli';
      return new Promise(function (ok) { window.setTimeout(ok, 3000); }).then(function () {
        return ajax(payload, 90000);
      });
    }).then(function (s) {
      olay('generate_lead', { lead_type: 'kesif_teklif', konu: konu, method: s === 'gecikmeli' ? 'formsubmit_ajax_gecikmeli' : 'formsubmit_ajax' });
    }).catch(function () {
      var b = beacon(payload);
      olay(b ? 'generate_lead' : 'form_delivery_failed', { lead_type: 'kesif_teklif', konu: konu, method: b ? 'formsubmit_beacon_yedek' : 'yok' });
    });
  });
})();
