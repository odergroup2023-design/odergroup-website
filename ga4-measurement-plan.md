# GA4 ölçüm planı — Öder Group

İlk aşamada site, GTM dataLayer üzerinden aşağıdaki olayları üretir. GTM’de her olay için GA4 Event etiketi aynı olay adıyla gönderilmelidir.

| DataLayer olayı | Ne zaman oluşur | GA4 amacı |
|---|---|---|
| `form_start` | Ziyaretçi teklif formundaki ilk alana odaklandığında | Form başlatma |
| `generate_lead` | FormSubmit AJAX sağlayıcısı başarılı yanıt verdiğinde | **Ana dönüşüm / lead** |
| `form_error` | Sağlayıcı hatası veya zaman aşımı olduğunda | Form hata oranı |
| `phone_click` | Telefon bağlantısına tıklandığında | Telefon mikro dönüşümü |
| `whatsapp_click` | WhatsApp bağlantısına tıklandığında | WhatsApp mikro dönüşümü |
| `quote_cta_click` | “Teklif Al” veya teklif CTA bağlantısına tıklandığında | CTA etkileşimi |
| `sss_acildi` | SSS sorusu açıldığında | İçerik ilgisi |
| `okuma_derinligi` | Sayfanın %25, %50, %75 ve %100’ü görüldüğünde | İçerik etkileşimi |

`generate_lead` yalnızca FormSubmit API sağlayıcısı başarılı yanıt verdikten sonra çalışır. Bu nedenle form düğmesine basılması tek başına dönüşüm sayılmaz. Olay parametreleri arasında kişisel veri gönderilmez; yalnızca `form_name`, `lead_type`, `konu`, `method` ve sayfa yolu gibi sınırlı teknik bilgiler kullanılır.

## GA4’te önerilen ayarlar

1. GTM’de `generate_lead` için Custom Event tetikleyicisi oluşturun.
2. GA4 Event etiketiyle olay adını `generate_lead` olarak gönderin.
3. GA4 Yönetici → Events bölümünde `generate_lead` olayını **Key event** olarak işaretleyin.
4. `phone_click`, `whatsapp_click`, `quote_cta_click` olaylarını mikro dönüşüm olarak izleyin; ana dönüşüm olarak işaretlemeyin.
5. `form_error` olayını hata raporlarında kullanın.
6. Form başarı sayfasına ulaşan oturumları ayrıca doğrulamak için `tesekkurler.html` görüntülemesini ikincil kontrol olarak izleyin.

## Test notu

Mobil iPhone 13 ve iPad WebKit testinde gerçek form gönderimi yapılmadan `quote_cta_click` ve `form_start` olaylarının dataLayer’a düştüğü doğrulandı. `generate_lead` testi için gerçek sağlayıcı gönderimi yapılmadı; kod yolu yalnızca sağlayıcı başarı yanıtında çalışacak şekilde kontrol edildi.
