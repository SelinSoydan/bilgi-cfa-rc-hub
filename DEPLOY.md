# Bilgi RC Hub: buluta kurulum (yaklaşık 20 dakika)

Uygulama bilgisayarında yerel bir dosyayla (`data/hub.db`) çalışır. Takım ve Faruk Hoca telefondan da girebilsin diye üç şey gerekiyor. Hepsi ücretsiz.

## 1. Ortak veritabanı: Supabase (8 dk)
1. https://supabase.com adresinde hesap aç ve **New project** de. Bölge olarak Frankfurt seç (Türkiye'ye en yakın).
2. Sol menüden **SQL Editor > New query**'ye gir. `supabase.sql` dosyasının içeriğini yapıştırıp **Run**'a bas.
3. **Project Settings > API** sayfasından iki şeyi kopyala:
   - **Project URL** (`https://....supabase.co`)
   - **service_role** anahtarı. Bu gizli bir anahtar; kimseyle paylaşma, koda ve sohbete yazma.

## 2. Kod: özel (private) GitHub reposu (2 dk)
- Repo **private** olmalı, çünkü içinde Borusan stratejimiz var.
- Claude bu adımı senin onayınla yapabilir (`gh repo create ... --private`).

## 3. Yayın: Streamlit Community Cloud (8 dk)
1. https://share.streamlit.io adresine GitHub hesabınla gir ve **Create app** de.
2. Repoyu seç, ana dosya olarak `app.py` yaz.
3. **Advanced settings > Secrets** kutusuna şunu yapıştır (değerleri kendin doldur):
   ```toml
   app_password = "takim-sifresi"

   [supabase]
   url = "https://PROJE.supabase.co"
   key = "SERVICE_ROLE_ANAHTARI"
   ```
4. **Deploy**'a bas. İlk açılışta uygulama, `seed.json` içindeki görevleri ve notları veritabanına kendisi yükler.
5. **Settings > Sharing**'den uygulamayı yalnızca davet ettiğin e-postalara açabilirsin. Uygulamada ayrıca takım şifresi de var.

## Bilmen gerekenler
- **Veri nerede?** Bulutta Supabase'te, bilgisayarında `data/hub.db` dosyasında. İkisi ayrı yerler.
- **Silinen görev:** Önce **Trash**'e gider ve oradan geri getirilir. "Delete forever" tek gerçek silme işlemidir.
- **Aynı anda düzenleme:** Her kaydın bir sürüm numarası var. İki kişi aynı anda değiştirirse uygulama birinin işini sessizce silmez, "tekrar dene" der.
- **claude.ai'daki eski site:** Bulut sürümü açılana kadar takımın aracı odur. Açılınca, oradaki son değişiklikler `seed.json` ile yeniden aktarılır.
