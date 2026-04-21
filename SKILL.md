---
name: meeting-minutes-generator
description: "TCDD BVA projesi toplantı tutanağı oluşturma aracı. Toplantı notları ve katılımcı listesinden resmi Word (.docx) formatında toplantı tutanağı üretir. Tetikleyiciler: 'toplantı tutanağı oluştur', 'toplantı notu yaz', 'meeting minutes', 'toplantı raporu hazırla', 'tutanak oluştur'. Kullanıcı toplantı özeti veya notları paylaştığında ve bundan bir Word dokümanı üretilmesi istendiğinde bu skill kullanılmalıdır. Katılımcı listesi, görüşülen konular ve aksiyon maddeleri içeren herhangi bir toplantı notu için tetiklenmelidir."
---

# TCDD Toplantı Tutanağı Oluşturucu

Toplantı notları ve katılımcı bilgilerinden TCDD BVA projesi formatında resmi toplantı tutanağı (.docx) üretir.

## Ne Zaman Kullanılır

- Kullanıcı toplantı notları/özeti paylaşıp "tutanak oluştur", "word dokümanı yap" dediğinde
- Katılımcı listesi + görüşülen konular + aksiyon maddeleri içeren metin verildiğinde
- "Bu toplantı notunu formatına işle" gibi talepler geldiğinde

## Çalışma Akışı

### Adım 1: Katılımcıları Çözümle (Registry Lookup)

**Katılımcı kaynağı — öncelik sırası:**

1. **Kullanıcı ayrı bir katılımcı listesi verdiyse** (örn. "Katılımcılar: Salih, Kerem, Eren..." veya tablo şeklinde) → **bu listeyi kullan**. Transkriptte konuşan ama listede olmayan kişileri EKLEME.
2. **Ayrı liste yoksa** → toplantı metninden/transkriptten konuşan isimleri çıkar (`Ad:` ile başlayan satırlar, "X dedi", "Y ekledi" gibi kalıplar). Sadece gerçekten toplantıya katılan kişileri al; metinde adı geçen ama dışarıdan referans verilen kişileri (örn. "Ahmet'e gönderelim") katılımcı sayma.

Çıkarılan her katılımcı ismini `data/participants.json` kayıt defterinde ara:

1. **Eşleşme kuralı:** Büyük/küçük harf ve Türkçe karakter duyarsız. Önce `name` alanında tam eşleşme, sonra `aliases` içinde eşleşme ara.
2. **Bulunduysa:** `unit` ve `title` alanlarını registry'den otomatik doldur. (Registry'de `unit`/`title` boş ise aşağıdaki adım devreye girer.)
3. **Bulunmadıysa veya eksik bilgi varsa:** Kullanıcıya o kişi için `unit` (kurum) ve `title` (ünvan) sor. Cevabı aldıktan sonra `participants.json`'a yeni kayıt olarak ekle — bir sonraki toplantıda tekrar sormayalım.
4. **Alias önerisi:** Kullanıcı kısa ad (örn. "Salih") kullandıysa ve tam isim registry'de farklıysa, kısa adı mevcut kaydın `aliases` listesine ekle.

Registry güncellemelerini Write/Edit tool ile `participants.json`'a kaydet.

**Çıktı sıralaması (önemli):** Katılımcı tablosunda kişiler şu düzende listelenir:

1. **Firma önceliği** (`_unit_order` alanına göre): TCDD Taşımacılık A.Ş. → UDHAM → TÜRKSAT → PROLİNE-PİA → PROLINE → PIA GRUP → (diğer).
2. **Ünvan kıdemi** (`_title_rank` alanına göre, firma içinde): Direktör → Daire Başkanı → Daire Başkan Yardımcısı → Program Yöneticisi → Şube Müdürü → Proje Yöneticisi → Teknik Lider → Kıdemli Uzman → Uzman → İş Analisti → Mühendis...
3. **Aynı ünvan içinde** alfabetik (ad soyad).

Bu sıralama, oluşturulan JSON'daki `participants` dizisinin sırasını belirler — `generate_minutes.py` aldığı sırayı aynen tabloya yazar.

### Adım 2: Toplantı Verilerini JSON'a Dönüştür

Adım 1'de çözümlenen katılımcılarla birlikte, toplantı notlarından aşağıdaki JSON yapısını oluştur. Şema detayları için `references/data-schema.md` dosyasını incele.

```json
{
  "meeting": {
    "title": "TOPLANTI BAŞLIĞI",
    "date": "GG.AA.YYYY",
    "time": "SS.DD",
    "location": "Toplantı yeri"
  },
  "participants": [
    { "name": "Ad Soyad", "unit": "Kurum", "title": "Ünvan" }
  ],
  "topics": [
    {
      "title": "Konu Başlığı",
      "items": ["Madde 1", "Madde 2"]
    }
  ],
  "actions": [
    {
      "no": "M01",
      "text": "Yapılacak iş açıklaması",
      "responsible": "Sorumlu birim",
      "planned_date": ""
    }
  ],
  "prepared_by": "Hazırlayan kişi adı"
}
```

**Temel biçim kuralları:**
- `topics` içindeki her konu otomatik numaralandırılır (1., 2., 3....)
- `items` içindeki maddeler bullet point olarak eklenir
- `actions` tablosu İŞLEM MADDELERİ bölümüne yazılır
- `prepared_by` kuralı:
  - Kullanıcı bir isim verdiyse (örn. "Tutanağı X hazırlayacak", "Hazırlayan: X") → o ismi yaz
  - Hiçbir şey verilmediyse → varsayılan olarak **"Kerem Türkyılmaz"** yaz (şablonun default'u)
  - Yani `prepared_by` asla boş kalmaz; ya kullanıcı değeri ya da Kerem Türkyılmaz olur

#### Ham metinden yapısal çıkarım kuralları

Kullanıcı çoğunlukla transkript veya serbest notlar yapıştırır. Bu metni JSON'a dönüştürürken şu ayrımları yap:

**1) Konu (topic) vs. İşlem Maddesi (action) ayrımı — KRİTİK:**
- **Konu (topics[].items):** Toplantıda *konuşulan, aktarılan, paylaşılan, tartışılan, karar verilen* şeyler. Geçmiş/şimdiki zaman, bilgi aktarımı, durum özeti. Örnek: "Tehlike tablosunun yapısı incelendi", "Versiyonlama mantığı aktarıldı", "Karar: Veri modeli 3NF olacak".
- **İşlem Maddesi (actions):** Toplantı **sonrası** somut bir kişi/ekip tarafından **yapılacak** iş. Gelecek zaman + sorumlu + (varsa) tarih. Örnek: "TCDD Geliştirici Ekip aktif/pasif tablo listesi hazırlayacak", "X, Y'ye raporu cuma gönderecek".
- Test: "Bu cümle toplantıdan sonra birinin yapacağı bir iş mi?" Evet → action, Hayır → topic item.

**2) Türkçe dilsel sinyaller (action tespiti için):**
- Fiil çekimleri: `-acak/-ecek` (yapılacak, hazırlanacak, teslim edilecek), `-meli/-malı` (incelenmeli), `-sın/-sin` (yapsın)
- Kalıplar: "X tarafından Y yapılacak", "X'ten Y bekleniyor", "X Y'den sorumludur", "aksiyon: ...", "TODO: ...", "to-do", "yapılacaklar"
- Pasif/belirsiz özne: "Liste hazırlanacak" → sorumluyu bağlamdan çıkar; bulunamıyorsa kullanıcıya sor (`responsible` boş bırakma).

**3) Sorumlu (responsible) atama:**
- Bir kişi adı veriliyorsa → "Ad Soyad" (registry'de varsa tam formu; yoksa geçtiği gibi)
- Bir ekip/birim veriliyorsa → kurum/ekip adı (örn. "TCDD Geliştirici Ekip", "PROLİNE-PİA")
- Birden fazla sorumlu varsa virgülle ayır: "Alper Denizeri, Eren Denli"

**4) Tarih (planned_date) çıkarımı:**
- Açık tarih → `GG.AA.YYYY` (örn. "15.05.2026")
- "Cuma", "önümüzdeki hafta", "2 hafta içinde" gibi göreli ifadeler → toplantı tarihini baz alarak mutlak tarihe çevir
- Belirsizse boş bırak (`""`) — uydurma.

**5) Aksiyon numaralandırma:**
- `no` alanı: `M01`, `M02`, `M03`... (sıralı, iki haneli). Başka numaralandırma (A01, T01) kullanma.

**6) Konu başlığı (topic.title):**
- Kısa, isim tamlaması. 3-8 kelime ideal. Örnek: "Risk (Tehlike) Veritabanı Yapısı", "Raporlama İhtiyaçları", "Açık Konular".
- Konuşmaların gidişatına göre 3-7 konu grupla; her konunun altına o konuyla ilgili bullet maddeleri topla. Aynı konu farklı yerlerde geçiyorsa birleştir.

**7) Karar maddeleri:**
- Ayrı alan yok; ilgili konunun `items` listesine **"Karar: ..."** önekiyle ekle. Örnek: `"Karar: Tüm tablolar Onay Sırası üzerinden versiyonlanacak."`

**8) Toplantı başlığı, tarih, saat, yer:**
- Kullanıcı açıkça söylemediyse, metin/bağlamdan çıkar. Şüpheli durumda kullanıcıya sor — uydurma.

### Adım 3: Markdown Önizleme (Kullanıcı Onayı)

JSON'u dosyaya yazıp docx üretmeden **önce**, yapısal çıkarımını markdown olarak sunup kullanıcıdan onay al. Amaç: LLM'in yanlış yorumlamalarını (kayıp aksiyon, yanlış sorumlu, karıştırılmış konu) docx aşamasına geçmeden düzeltmek.

Önizleme formatı:

```markdown
## 📋 Tutanak Önizlemesi

**Başlık:** {title}
**Tarih / Saat / Yer:** {date} • {time} • {location}
**Hazırlayan:** {prepared_by}

### Katılımcılar ({N} kişi)
| # | Ad Soyad | Birim | Ünvan |
|---|----------|-------|-------|
| 1 | ... | ... | ... |

### Görüşülen Konular
**1. {topic_1_title}**
- {item}
- Karar: {...}

**2. {topic_2_title}**
- ...

### İşlem Maddeleri ({M} adet)
| No | İşlem | Sorumlu | Tarih |
|----|-------|---------|-------|
| M01 | ... | ... | ... |
```

Önizlemenin altına şu soruyu ekle: **"Bu hâliyle docx'e dönüştürmemi istiyor musunuz, yoksa düzeltme var mı?"**

- Kullanıcı **onaylarsa** → Adım 4'e geç.
- Kullanıcı **düzeltme** verirse → ilgili alanları güncelle, önizlemeyi yeniden sun.
- Küçük (1-2 satır) düzeltmelerde tüm önizlemeyi tekrar yazmak yerine değişen bölümü diff-style göster.

### Adım 4: JSON Dosyası Oluştur

JSON verisini geçici bir çalışma dosyasına yaz.

- **Anthropic cloud ortamı:** `/home/claude/meeting_data.json`
- **Windows local (Claude Code):** `$env:TEMP\meeting_data.json` veya kullanıcının belirttiği yol
- **Linux/macOS local:** `/tmp/meeting_data.json`

### Adım 5: Dokümanı Üret

Skill'in kendi dizinindeki `scripts/generate_minutes.py` çağrılır. Mutlak path platformdan platforma değişir; aşağıdaki değişkenleri ortama göre doldur:

- `$SKILL_DIR` = skill'in bulunduğu dizin (örn. Windows'da `C:\Users\<kullanıcı>\.claude\skills\meeting-minutes-generator`, cloud'da `/mnt/skills/user/meeting-minutes-generator`)
- `$DATA` = Adım 3'te yazılan JSON yolu
- `$OUTPUT` = üretilecek docx yolu

```bash
python "$SKILL_DIR/scripts/generate_minutes.py" \
  --data "$DATA" \
  --template "$SKILL_DIR/assets/template.docx" \
  --output "$OUTPUT"
```

> Windows PowerShell'de `python`, Unix'te `python3` kullan. Path ayracı (`\` vs `/`) platforma uyarla.

### Adım 6: Doğrulama ve Teslim

Öncelik sırasına göre:

1. **Cloud ortamında:** `python /mnt/skills/public/docx/scripts/office/validate.py $OUTPUT` (mevcutsa).
2. **Her ortamda çalışan minimal doğrulama** (yukarıdaki yoksa):
   ```bash
   python -c "import zipfile; from xml.etree import ElementTree as ET; z=zipfile.ZipFile(r'$OUTPUT'); ET.fromstring(z.read('word/document.xml')); print('OK')"
   ```
   — zip bütünlüğünü ve `document.xml` well-formed olduğunu doğrular; başarısızlıkta hata fırlatır.

Doğrulama geçtikten sonra çıktıyı kullanıcıya teslim et:
- **Cloud:** `/mnt/user-data/outputs/` dizinine kopyala.
- **Local:** Kullanıcının istediği konuma (Desktop, proje klasörü, vb.) kopyala veya yolu raporla.

## Şablon Hakkında

Şablon (`assets/template.docx`) TCDD BVA projesi standart toplantı tutanağı formatını içerir:
- Üst bilgi: TCDD logosu ve doküman bilgileri
- TOPLANTI ADI / KONUSU tablosu
- TARİH / SAAT / YER tablosu
- KATILIMCILAR tablosu (NO / ADI SOYADI / BİRİM-KURUM / UNVAN)
- GÖRÜŞÜLEN KONULAR bölümü (numaralı başlıklar + bullet maddeler)
- İŞLEM MADDELERİ tablosu (No / İşlem Maddesi / İlgili Birim / Planlanan Tarih)
- Hazırlayan bilgisi

Font: Tahoma, A4 kağıt boyutu.

## Hata Durumları

- JSON oluşturulurken Türkçe karakterlere dikkat et (UTF-8 encoding)
- Eğer validate başarısız olursa, `unpack → düzelt → pack` döngüsüne gir (docx skill'ine bakınız)
- Şablonda olmayan alanlar eklemek gerekirse doğrudan XML manipülasyonu yap

## Bağımlılıklar

- Python 3.x (Windows: `python`, Unix: `python3`)
- **Opsiyonel:** `/mnt/skills/public/docx` (cloud ortamında unpack/pack/validate araçları). Local ortamda kullanılamaz; Adım 5'teki minimal doğrulama yeterlidir.
