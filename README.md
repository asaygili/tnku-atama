# 🎓 TNKÜ Öğretim Üyeliği Atama Puanlama Sistemi

Bu proje, **Tekirdağ Namık Kemal Üniversitesi** bünyesinde görev yapan veya başvuruda bulunacak olan akademisyenlerin, güncel atama ve yükseltme kriterlerine (EYS-YNG-129) göre puanlarını hesaplamalarını sağlayan bir araçtır.

## 📋 Proje Hakkında
Akademik kadro başvurularında (Doktor Öğretim Üyesi, Doçent, Profesör) adayların faaliyetlerini sisteme girerek puanlarını hızlı ve hatasız bir şekilde hesaplamalarına yardımcı olur. Sistem, üniversitenin belirlediği güncel yönerge ve katsayıları baz almaktadır.

### Desteklenen Kadrolar:
* **Dr. Öğretim Üyesi** (İlk Atanma / Yeniden Atanma)
* **Doçent**
* **Profesör**

---

## 🛠 Temel Özellikler
* **Akademik Alan Seçimi:** Fen, Sağlık, Mühendislik, Matematik ve Sosyal Bilimler gibi farklı alanlara özgü katsayı hesaplamaları.
* **Faaliyet Yönetimi:** Yayınlar, bildiriler, projeler ve eğitim-öğretim faaliyetlerinin kolayca eklenmesi.
* **Genel Koşul Kontrolü:** YÖKDİL/YDS puanı, ders saati ve kıdem yılı gibi ön koşulların doğrulanması.
* **Otomatik Hesaplama:** Girilen verilere göre toplam puanın anlık olarak çıkarılması.

---

## 🚀 Kullanım
1.  **Kimlik Bilgileri:** Ad-Soyad ve Akademik Alan seçimini yapın.
2.  **Kadro Türü:** Başvuru yapacağınız kadroyu seçin.
3.  **Sayısal Bilgiler:** Dil puanı, verilen ders sayısı ve kıdem süresi gibi verileri girin.
4.  **Faaliyetler:** "Faaliyet Ekle" sekmesinden akademik çalışmalarınızı listeleyin.
5.  **Hesapla:** Tüm bilgileri girdikten sonra toplam puanınızı görüntüleyin.

---

## 📑 ÜAK Doçentlik Kriterleri (Profesörlük Md. 11(2))
Profesörlük başvurusunda, doçentlik başvuru dönemindeki ÜAK kriterlerinin doçentlik başvurusu sonrası çalışmalarla yeniden sağlanması gerekir. **Aday Bilgileri → Doçentlik başvurusundaki ÜAK kriteri** alanından dönem seçildiğinde, doçentlik başvurusu sonrası faaliyetler ÜAK tablosuna göre otomatik puanlanır. Lisansüstü tezlerden üretilmiş yayın şartı profesörlükte aranmaz. Sonuç ekranda ve PDF'te bölüm bölüm gösterilir.

Tanımlı kriter setleri:
* ÜAK Mart 2022 – Mühendislik (Tablo 9, koşul 91)

**Yeni dönem / temel alan eklemek:** `uak_kriterleri/mart_2022.py` örnek alınarak `uak_kriterleri/` klasöründe bir `KriterSeti` tanımlanır ve `kaydet()` ile kaydedilir. Yeni dosya ise `uak_kriterleri/__init__.py` dosyasının en altındaki içe aktarma listesine eklenir. Her kalemde puan, eşlenen EK-2 kodları, tezden üretilmiş olma koşulu ve yazar paylaşım kuralı; her bölümde asgari/azami puan ve özel koşullar veri olarak yazılır, hesaplama koduna dokunulmaz.

---

## ✅ Testler
Yönerge kurallarının (Madde 8, Madde 11, EK-1) doğru uygulandığını denetleyen testler `tests/` klasöründedir. Ek kurulum gerektirmez:
```bash
python -m unittest discover -s tests -v
```

---

## 📂 Dosya Yapısı
```text
├── src/                # Kaynak kodlar
├── data/               # Atama kriterleri ve katsayı tabloları
├── docs/               # EYS-YNG-129 yönergesi ve dokümanlar
└── README.md           # Proje tanıtım dosyası
```

## ⚖️ Yasal Uyarı
Bu araç bilgilendirme amaçlıdır. Nihai puanlama ve değerlendirme süreci **TNKÜ Rektörlüğü ve ilgili komisyonlar** tarafından yürütülmektedir. Oluşabilecek hesaplama hatalarından geliştirici sorumlu tutulamaz.

## 🤝 Katkıda Bulunma
Eğer bir hata fark ederseniz veya güncel yönerge değişikliklerini sisteme yansıtmak isterseniz lütfen bir **Issue** açın veya **Pull Request** gönderin.

---
**Geliştirici:** Ahmet SAYGILI
**Son Güncelleme:** 16.04.2026
