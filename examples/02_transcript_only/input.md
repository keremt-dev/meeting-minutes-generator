# Senaryo 02 — Sadece transkript, katılımcı listesi ve hazırlayan verilmemiş

Kullanıcı ham transkripti yapıştırır; ayrı liste yoktur, hazırlayan da belirtilmemiştir. Skill'in konuşmalardan katılımcıları çıkarması ve hazırlayan için varsayılanı kullanması beklenir.

## Kullanıcının skill'e vereceği metin (sohbete kopyalanır)

---

Toplantı 23 Nisan 2026 Perşembe günü saat 15:00'te Teams üzerinden başladı. Konu: Veri Ambarı Mimari Gözden Geçirmesi.

Salih: Bugün veri ambarı mimarisini gözden geçireceğiz. Ömer, star schema tasarımını özetleyebilir misin?

Ömer Lüser: Tabii. Fact tabloları olarak Satış, Rezervasyon ve Bilet kullanıyoruz; boyutlar Zaman, Güzergah, Müşteri ve Araç. Slowly Changing Dimension Type 2 uyguluyoruz müşteri boyutuna.

Semih Serdar: Performans tarafında partisyon stratejisini konuşalım — günlük partisyon mu, aylık mı?

Ömer: Veri hacmi gün başına 5M civarında; günlük partisyon mantıklı görünüyor.

Cevat Uzun: Bir not düşeyim — eski sistemden migrate ederken soft-delete kayıtları nasıl taşıyacağız?

Salih: Bu konuyu ayrı bir çalışma yapalım. Cevat, 2 hafta içinde migration stratejisi dokümanı çıkarır mısın?

Cevat: Tamam, 7 Mayıs'a kadar hazır olur.

Ömer: Karar: Fact tabloları günlük partisyonlanacak, müşteri boyutu SCD Type 2 olarak kalacak.

Semih Serdar: Performans testi için test ortamında 30 günlük veri üretmemiz lazım. Ben bu hafta sonuna kadar test data generator'ı hazırlarım.

Salih: Mehmet Cevheri de bu konuda destek versin, script review yapar.

Mehmet Cevheri Bozoğlan: Olur, pazartesi Semih'le oturup bakarız.

Salih: Sonraki adımlar için 30 Nisan'da tekrar buluşalım. Kapatıyorum.

---

## Beklenen davranış (test kriteri)

- `participants` konuşmalardan çıkarılır: Salih Bağ, Ömer Lüser, Semih Serdar Cengizoğlu, Cevat Uzun, Mehmet Cevheri Bozoğlan (5 kişi)
- Registry'de hepsinin kaydı mevcut; firma/ünvan otomatik doldurulur
- Sıralama: TÜRKSAT (Salih) → PROLİNE-PİA (Ömer Lüser — Teknik Lider → Semih Serdar — Kıdemli Uzman) → PIA GRUP (Cevat Uzun, Mehmet Cevheri Bozoğlan — ünvana göre)
- Göreli tarihler: "2 hafta içinde" → 07.05.2026 (Cevat açıkça söyledi, kullan). "Bu hafta sonuna kadar" → 27.04.2026 (Pazar) veya "25.04.2026" (Cumartesi) — yakın Pazar'ı seç
- Actions:
  - M01: Migration stratejisi dokümanı — Cevat Uzun — 07.05.2026
  - M02: Test data generator — Semih Serdar Cengizoğlu — ~26-27.04.2026
  - M03: Script review — Mehmet Cevheri Bozoğlan — 27.04.2026 (pazartesi)
- Kararlar: topic items'a "Karar: ..." öneki ile
- `prepared_by` = **Kerem Türkyılmaz** (kullanıcı belirtmedi → varsayılan)
