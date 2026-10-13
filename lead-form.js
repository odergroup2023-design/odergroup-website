/* Mevcut FormSubmit hizmeti: başarılı sağlayıcı yanıtı gelmeden dönüşüm sayılmaz.
   Analitik olaylara ad, telefon, e-posta veya serbest metin gönderilmez. */
(function () {
  'use strict';
  var form = document.querySelector('form.form[action="https://formsubmit.co/info@odergroup.com.tr"]');
  if (!form || !window.fetch || !window.FormData || !window.AbortController) return;
  var button = form.querySelector('button[type="submit"]');
  if (!button) return;
  var busy = false;
  var status = document.createElement('p');
  status.setAttribute('role', 'status');
  status.setAttribute('aria-live', 'polite');
  status.hidden = true;
  status.style.cssText = 'color:#fff;font-size:.85rem;line-height:1.6;margin-top:14px';
  button.insertAdjacentElement('afterend', status);

  form.addEventListener('submit', async function (event) {
    event.preventDefault();
    if (busy || !form.reportValidity()) return;
    var honey = form.querySelector('[name="_honey"]');
    if (honey && honey.value) return;
    busy = true;
    var originalText = button.textContent;
    button.disabled = true;
    button.textContent = 'Talebiniz gönderiliyor…';
    status.hidden = false;
    status.textContent = 'Lütfen bekleyin; gönderim sonucunu kontrol ediyoruz.';
    var payload = {};
    new FormData(form).forEach(function (value, key) {
      if (typeof value === 'string') payload[key] = value;
    });
    payload._url = window.location.href;
    var controller = new AbortController();
    var timeout = window.setTimeout(function () { controller.abort(); }, 20000);
    try {
      var response = await fetch('https://formsubmit.co/ajax/info@odergroup.com.tr', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
        body: JSON.stringify(payload),
        signal: controller.signal
      });
      var result = await response.json();
      if (!response.ok || !(result.success === true || result.success === 'true')) {
        throw new Error('Sağlayıcı gönderimi onaylamadı');
      }
      window.dataLayer = window.dataLayer || [];
      window.gtag = window.gtag || function(){ window.dataLayer.push(arguments); };
      window.dataLayer.push({
        event: 'generate_lead',
        legacy_event: 'teklif_formu_gonderildi',
        sayfa: window.location.pathname,
        form_name: 'kesif_teklif_formu',
        lead_type: 'kesif_teklif',
        konu: payload.konu || 'Genel teklif',
        method: 'formsubmit_ajax',
        onay_kaynagi: 'formsubmit_api'
      });
      window.gtag('event', 'generate_lead', {form_name:'kesif_teklif_formu', lead_type:'kesif_teklif', konu:payload.konu || 'Genel teklif', method:'formsubmit_ajax'});
      status.textContent = 'Form hizmeti talebinizi kabul etti. Teşekkür sayfasına yönlendiriliyorsunuz.';
      window.setTimeout(function () {
        window.location.assign('tesekkurler.html');
      }, 300);
    } catch (error) {
      status.setAttribute('role', 'alert');
      status.textContent = 'Gönderim onayı alınamadı. Bilgileriniz bu formda duruyor. Yeniden deneyebilir veya +90 534 547 22 39 numarasından telefon/WhatsApp ile ulaşabilirsiniz.';
      window.dataLayer = window.dataLayer || [];
      window.dataLayer.push({ event: 'form_error', legacy_event: 'teklif_formu_hata', sayfa: window.location.pathname, form_name: 'kesif_teklif_formu' });
      window.gtag = window.gtag || function(){ window.dataLayer.push(arguments); };
      window.gtag('event', 'form_error', {form_name:'kesif_teklif_formu'});
      busy = false;
      button.disabled = false;
      button.textContent = originalText;
    } finally {
      window.clearTimeout(timeout);
    }
  });
})();
