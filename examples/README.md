# Examples — Meeting Minutes Generator

Skill'i test etmek için hazır girdiler. Her klasörde bir `input.md` (kullanıcının sohbete yapıştıracağı içerik) ve beklenen davranışın notu var.

## Senaryolar

| # | Klasör | Ne test eder |
|---|---|---|
| 01 | `01_with_participant_list/` | Kullanıcı ayrı katılımcı listesi verir → liste esas alınır, transkripteki ek isimler EKLENMEZ. Hazırlayan açıkça verilir. |
| 02 | `02_transcript_only/` | Sadece transkript verilir, liste yok → katılımcılar konuşmalardan çıkarılır. Hazırlayan belirtilmez → varsayılan Kerem Türkyılmaz. |

## Nasıl kullanılır

1. İlgili `input.md` içeriğini Claude'a yapıştır.
2. "Bu toplantıdan tutanak oluştur" de.
3. Skill akışı otomatik çalışır:
   - Adım 1: Katılımcıları çözümle (registry + transkript)
   - Adım 2: Konu/aksiyon çıkarımı (yeni kurallar)
   - Adım 3: Markdown önizleme → onay bekler
   - Adım 4-6: JSON yaz, docx üret, doğrula

## Kontrol noktaları

Her senaryo için çıktı docx'inde şunları kontrol et:
- Üst bilgi (başlık/tarih/saat/yer) doğru mu?
- Katılımcılar beklenen sırada mı (firma önceliği + ünvan kıdemi)?
- Her topic'teki bullet maddeler anlamlı mı?
- Aksiyon `M01`, `M02`... şeklinde sıralı mı?
- Göreli tarihler ("önümüzdeki hafta pazartesi" vb.) mutlak GG.AA.YYYY'ye çevrilmiş mi?
- Hazırlayan doğru mu (kullanıcının dediği kişi veya varsayılan Kerem)?
