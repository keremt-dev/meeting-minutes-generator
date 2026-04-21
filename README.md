# Meeting Docx Generator

TCDD BVA projesi için toplantı notlarından resmi Word (.docx) formatında toplantı tutanağı üreten Claude skill'i.

## Ne yapar

Kullanıcı toplantı metnini ve (opsiyonel) katılımcı listesini paylaştığında:
- Katılımcıları kayıtlı profilden çözer (isim → birim/ünvan)
- Ham metinden konuşulan konuları ve aksiyon maddelerini yapısal olarak çıkarır
- Göreli tarihleri ("önümüzdeki hafta cuma") mutlak tarihe çevirir
- Markdown önizleme sunup onay ister
- TCDD BVA şablonuna uyumlu .docx üretir ve doğrular

## Çalışma akışı (6 adım)

```
Kullanıcı girdisi (metin + opsiyonel katılımcı listesi)
        │
        ▼
[1] Katılımcıları çözümle ──► data/participants.json kayıt defterinde ara
        │                      bulamazsa kullanıcıya sor ve ekle
        ▼
[2] Konu/aksiyon çıkarımı ──► Türkçe dilsel kurallara göre topic vs action ayır
        │                      göreli tarihleri mutlaklaştır
        ▼
[3] Markdown önizleme ──────► kullanıcı onayı bekle; düzeltme varsa dön
        │
        ▼
[4] JSON dosyası yaz
        │
        ▼
[5] generate_minutes.py ───► template.docx üzerinden XML manipülasyonu
        │
        ▼
[6] Doğrula ve teslim ─────► .docx çıktısı kullanıcıya
```

Detaylı kurallar: [SKILL.md](SKILL.md)

## Kurulum

Skill bir klasördür; tek yapılması gereken, kullandığınız agent'ın skill dizinine kopyalamak. Üç platform için de adımlar aşağıda.

### Claude Code

```powershell
# Windows (PowerShell)
Copy-Item -Recurse -Force meeting-minutes-generator $env:USERPROFILE\.claude\skills\

# Linux / macOS
cp -r meeting-minutes-generator ~/.claude/skills/
```

Yeni bir sohbet başlattığınızda skill otomatik listelenir. Tetikleyici ifadelerden biri (örn. *"tutanak oluştur"*) veya `/meeting-minutes-generator` ile devreye girer.

### Gemini CLI

Gemini CLI oturum başında skill metadata'sını okur, tam içeriği `activate_skill` tool'u ile çağrı anında yükler.

```powershell
# Windows (PowerShell)
Copy-Item -Recurse -Force meeting-minutes-generator $env:USERPROFILE\.gemini\skills\

# Linux / macOS
cp -r meeting-minutes-generator ~/.gemini/skills/
```

Kullanım: sohbette tetikleyici ifadeyi kullanın; Gemini ilgili skill'i `activate_skill meeting-minutes-generator` ile yükleyecektir. Skill'deki `Skill` / `Read` / `Write` tool referansları Gemini'nin eşdeğerlerine otomatik eşlenir (bkz. Anthropic `references/gemini-tools.md` rehberi).

### OpenAI Codex CLI / ChatGPT Agent

Codex CLI'de native "skill" kavramı yoktur; skill'i `AGENTS.md` üzerinden referanslarız.

1. Dosyaları kopyalayın:

    ```powershell
    # Windows (PowerShell)
    Copy-Item -Recurse -Force meeting-minutes-generator $env:USERPROFILE\.codex\skills\

    # Linux / macOS
    cp -r meeting-minutes-generator ~/.codex/skills/
    ```

2. Projenin (veya global `~/.codex/AGENTS.md`) dosyasına şunu ekleyin:

    ```markdown
    ## Meeting Minutes Generator

    Kullanıcı toplantı tutanağı / meeting minutes oluşturmak istediğinde:
    `~/.codex/skills/meeting-minutes-generator/SKILL.md` dosyasındaki 6 adımlı akışı
    (katılımcı çözümleme → konu/aksiyon çıkarımı → markdown önizleme → JSON → docx üretim → doğrulama) aynen uygula.
    Python 3.x gerekir; `scripts/generate_minutes.py` JSON + `assets/template.docx` üzerinden çıktıyı üretir.
    ```

ChatGPT web arayüzü (Projects / Custom GPT) için: `SKILL.md` içeriğini Custom Instructions kutusuna yapıştırın, `scripts/generate_minutes.py` ve `assets/template.docx` dosyalarını Project Files'a yükleyin.

## Dosya yapısı

```
meeting-minutes-generator/
├── SKILL.md                    # Ana yönerge (Claude'un okuduğu)
├── README.md                   # Bu dosya
├── assets/
│   └── template.docx           # TCDD BVA resmi şablon (Tahoma, A4)
├── scripts/
│   └── generate_minutes.py     # JSON + template → docx üretici
├── data/
│   └── participants.json       # Kayıtlı katılımcı profili (sık katılımcılar)
├── references/
│   └── data-schema.md          # JSON şema referansı
└── examples/                   # Test senaryoları
    ├── README.md
    ├── 01_with_participant_list/input.md
    └── 02_transcript_only/input.md
```

## Kilit davranış kuralları

| Konu | Kural |
|------|-------|
| **Katılımcı kaynağı** | Kullanıcı ayrı liste verdiyse → liste öncelikli (transkriptteki ek isimler eklenmez). Liste yoksa → konuşmalardan çıkar. |
| **Registry lookup** | İsim `participants.json`'da (name + aliases, TR-karakter/case duyarsız) aranır. Bulunamazsa kullanıcıya sorulur, cevap registry'e eklenir. |
| **Sıralama** | Firma öncelik: TCDD → UDHAM → TÜRKSAT → PROLİNE-PİA → PROLINE → PIA GRUP. Firma içinde ünvan kıdemi (Direktör > Daire Başkanı > ... > Mühendis). |
| **Konu vs aksiyon** | Konu = toplantıda konuşulan/aktarılan şey (geçmiş/şimdiki). Aksiyon = toplantı sonrası yapılacak iş (gelecek zaman + sorumlu). |
| **Karar maddeleri** | İlgili topic'in `items`'ına `"Karar: ..."` öneki ile eklenir (ayrı alan yok). |
| **Aksiyon numaralandırma** | `M01`, `M02`... sıralı, iki haneli. |
| **Tarih çıkarımı** | Göreli ifadeler ("cuma", "2 hafta içinde") toplantı tarihine göre mutlak `GG.AA.YYYY`'ye çevrilir. Belirsizse boş bırakılır — uydurma yapılmaz. |
| **Hazırlayan** | Kullanıcı verdiyse onu yaz. Vermediyse → varsayılan **Kerem Türkyılmaz**. |

## Şablon hakkında

`assets/template.docx` TCDD BVA standart tutanak formatı:
- Üst bilgi: TCDD logosu + doküman bilgileri
- TOPLANTI ADI / TARİH / SAAT / YER blokları
- KATILIMCILAR tablosu (NO / ADI SOYADI / BİRİM-KURUM / UNVAN)
- GÖRÜŞÜLEN KONULAR (numaralı başlıklar + bullet maddeler)
- İŞLEM MADDELERİ tablosu (No / İşlem / İlgili Birim / Planlanan Tarih)
- Hazırlayan hücresi
- Font: Tahoma, Kağıt: A4

### Şablon güncellenirse dikkat

`scripts/generate_minutes.py` içinde `TEMPLATE_MARKERS` dict'i var — şablondaki sabit metinleri (başlık anchor'ı, tarih etiketi, mevcut saat/yer/hazırlayan değerleri) anchor olarak kullanıyor. Şablonda bu değerlerden biri değişirse ilgili `TEMPLATE_MARKERS` girdisini de güncellemek gerekir, yoksa ilgili alan sessizce doldurulmayabilir.

## Katılımcı kayıt defteri

Repo yalnızca `data/participants.example.json` dosyasını içerir — içinde mock isim/firma/ünvanlar vardır. Skill **gerçek** kayıt defteri olarak `data/participants.json` dosyasını okur; bu dosya kişisel/kurumsal veri barındırdığı için `.gitignore`'a eklenmiştir.

İlk kurulumda:

```bash
# skill dizinine girdikten sonra
cp data/participants.example.json data/participants.json
# ardından kendi ekibinizle doldurun
```

Yeni bir katılımcı ilk defa bir toplantıda geçtiğinde skill otomatik olarak kullanıcıya firma/ünvan sorar ve `data/participants.json`'a ekler. Manuel ekleme için:

```json
{
  "name": "Ad Soyad",
  "unit": "Kurum Adı",
  "title": "Ünvan",
  "aliases": ["Ad"]
}
```

`_unit_order` ve `_title_rank` meta alanları çıktı sıralamasını yönetir; yeni kurum/ünvan eklenecekse bu listelere de eklenmelidir.

## Bağımlılıklar

- Python 3.x (Windows: `python`, Unix: `python3`)
- Standart kütüphane (`zipfile`, `re`, `xml.etree`) — ek paket yok
- Opsiyonel: `/mnt/skills/public/docx` (cloud doğrulama aracı); local'de inline zipfile+XML parse ile minimal doğrulama yapılır

## Test

`examples/` altındaki senaryoları ayrı bir Claude sohbetine yapıştırıp beklenen davranışla karşılaştırın. Detay: [examples/README.md](examples/README.md).

Skriptin kendisini hızlıca doğrulamak için:

```bash
python -c "import py_compile; py_compile.compile(r'scripts/generate_minutes.py', doraise=True); print('OK')"
```

## Tetikleyici ifadeler

Skill şu ifadelerle tetiklenir: *"toplantı tutanağı oluştur"*, *"meeting minutes"*, *"tutanak yaz"*, *"toplantı raporu hazırla"*, veya bir toplantı metni + katılımcı listesi paylaşıldığında.
