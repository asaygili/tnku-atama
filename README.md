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
