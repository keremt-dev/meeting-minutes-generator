# Senaryo 01 — Ayrı katılımcı listesi verilmiş

Bu girdi, kullanıcının toplantıya gelenleri ayrı olarak tanımladığı ve hazırlayan olarak kendisi dışında birini belirttiği klasik senaryoyu temsil eder.

## Kullanıcının skill'e vereceği metin (sohbete kopyalanır)

---

**Toplantı:** BVA_KP Projesi Sprint 7 Değerlendirme
**Tarih:** 22.04.2026, 10:00, Online Toplantı-Teams
**Katılımcılar:**
- Salih Bağ
- Kübra Çınarlar
- Gizem Çamdal
- Alper Denizeri
- Eren Denli
- Merve Nur Yıldırım
- Kerem Türkyılmaz
- Ahmet Ayhan

**Hazırlayan:** Merve Nur Yıldırım

---

**Transkript:**

Salih: Sprint 7 kapanış toplantımıza hoş geldiniz. Öncelikle geliştirilen modüllerin durumunu görelim.

Eren: Geliştirici ekip olarak Risk Yönetim modülünün %80'ini tamamladık. Geri kalan %20 aksiyon onay akışı — test ortamında bazı UI bug'ları var.

Alper: UI bug'ları için Emre aksiyon alacak mı?

Eren: Evet, Emre konuşmuştuk; ben mesaj atarım, önümüzdeki hafta çarşamba gününe kadar düzeltir.

Kübra: Müşteri tarafı olarak bir geri bildirim var — raporlama ekranında tarih filtresi çalışmıyor. Kritik.

Kerem: Bu dün tespit edildi zaten. Ben hotfix hazırlayacağım, 24 Nisan Cuma'ya kadar devreye alırım.

Gizem: Sprint 8 planlaması için analiz dokümanları hazır. Backlog'a üç yeni user story ekledik.

Salih: Karar: Sprint 8 başlangıcı 28 Nisan; bu tarihe kadar hotfix ve aksiyon onay akışı kapanmış olmalı.

Merve: Tutanağı ben hazırlarım. Herkesin gözden geçirmesi için yarın paylaşırım.

Alper: Teknik borç tarafı için bir not daha — migration scriptlerini gözden geçirmemiz lazım. Bu sprint içinde planlayamadık.

Salih: Sprint 9'a alalım. Toplantıyı kapatıyorum, teşekkürler.

---

## Beklenen davranış (test kriteri)

- `participants` tam **7 kişi** (listedeki) — transkriptte geçen "Emre" veya "Emre Usta" katılımcı olarak **eklenmemeli** (liste öncelikli)
- `participants` sıralaması: TCDD (Kübra Çınarlar → Gizem Çamdal) → TÜRKSAT (Salih) → PROLİNE-PİA (Alper → Eren → Merve Nur → Kerem, ünvana göre)
- `actions` en az 2 madde (M01: Emre — UI bug düzeltme, M02: Kerem — hotfix)
- Göreli tarih: "önümüzdeki hafta çarşamba" → bugün 22.04.2026 (Çar) → 29.04.2026. "24 Nisan Cuma" → 24.04.2026 (mutlak verilmiş, aynen).
- Karar (Sprint 8 başlangıcı) topic items'a **"Karar: ..."** öneki ile
- `prepared_by` = Merve Nur Yıldırım (kullanıcı açıkça verdi)
