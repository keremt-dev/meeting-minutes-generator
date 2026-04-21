# Meeting Data JSON Schema

The `generate_minutes.py` script accepts a JSON file with the following structure.

## Full Schema

```json
{
  "meeting": {
    "title": "BVA_KP PROJESİ ÇÖZÜM MERKEZİ VERİ ANALİZ TOPLANTISI",
    "date": "10.02.2026",
    "time": "10.00",
    "location": "Online Toplantı-Teams"
  },
  "participants": [
    {
      "name": "Salih Bağ",
      "unit": "TÜRKSAT",
      "title": "Proje Yöneticisi"
    }
  ],
  "topics": [
    {
      "title": "Risk (Tehlike) Veritabanı Yapısı",
      "items": [
        "Tehlike tablosunun yapısı incelendi; onay durumu, tehlike kodu (ID) ve lokasyon bilgilerinin nasıl tutulduğu aktarıldı.",
        "Verilerde versiyonlama mantığı Onay Sırası üzerinden yürütülüyor."
      ]
    }
  ],
  "actions": [
    {
      "no": "M01",
      "text": "Geliştirici ekip aktif/pasif tablo listesi hazırlayacak.",
      "responsible": "TCDD Geliştirici Ekip",
      "planned_date": ""
    }
  ],
  "prepared_by": "Merve Nur Yıldırım"
}
```

## Field Descriptions

### meeting (required)
| Field | Type | Description |
|-------|------|-------------|
| title | string | Meeting title shown at the top of the document |
| date | string | Date in DD.MM.YYYY format |
| time | string | Time in HH.MM format |
| location | string | Meeting location or "Online Toplantı-Teams" |

### participants (required, array)
Each participant object:
| Field | Type | Description |
|-------|------|-------------|
| name | string | Full name |
| unit | string | Company/organization (e.g. "TÜRKSAT", "TCDD Taşımacılık A.Ş.", "PROLİNE-PİA") |
| title | string | Job title/role (e.g. "Proje Yöneticisi", "İş Analisti", "Veri Mühendisi") |

### topics (required, array)
Each topic object:
| Field | Type | Description |
|-------|------|-------------|
| title | string | Topic heading (auto-numbered: "1. Title", "2. Title", ...) |
| items | array of strings | Bullet points under this topic |

### actions (required, array)
Each action item object:
| Field | Type | Description |
|-------|------|-------------|
| no | string | Action item number (e.g. "M01", "M02") |
| text | string | Description of the action item |
| responsible | string | Responsible unit/person |
| planned_date | string | Target date (can be empty string) |

### prepared_by (optional)
| Field | Type | Description |
|-------|------|-------------|
| prepared_by | string | Name of the person who prepared the minutes |
