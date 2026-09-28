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

## 🗂️ Kanıt Arşivi ve Başvuru Dosyası (yalnızca yerelde)
Program kendi bilgisayarınızda çalıştırıldığında faaliyetlerin kanıt klasörleriyle bütünleşir. Kanıt klasörü bulunamazsa (örn. Streamlit Cloud) bu bölümler görünmez ve program eskisi gibi çalışır. Kanıt dosyaları ve kişisel bilgiler hiçbir zaman buluta ya da repoya gönderilmez.

**Kanıt klasörü düzeni** (örn. `E:\Kanit_Dosyalari`):
```text
UM22_2021_<kısa başlık>\      kayit.json, kunye.txt, tam_metin.pdf, arsiv\, atiflar\
UB03_2025_<kısa başlık>\      bildiri_sayfalari.pdf, bildiri_kitabi_kapak_kunye.pdf, ...
DERS_Verilen_Dersler\ PROJE_TUBITAK\ HAKEM_Hakemlikler\ IDARI_Gorevler\ ...
_Genel_Belgeler\ _Docentlik_Basvuru_Belgeleri\ ...   (yardımcı klasörler)
aday.json                     aday bilgileri ve faaliyet listesi (Kaydet / Yükle)
_eslestirme_kurallari.json    bu arşive özgü eşleştirme kuralları (isteğe bağlı)
```

**Programda:**
1. *Aday Bilgileri → Kanıt klasörü:* klasörü seçin; **Kaydet / Yükle** ile faaliyet listesi kalıcı olur (program açılışta kayıtlı listeyi yükler).
2. *AVES'ten yükleme sonrası:* kanıt klasörü olmayan yayınlar için klasör açılabilir; AVES'teki sıra değişmişse klasörler yeni kodlarla yeniden adlandırılır (eşleştirme DOI / başlık kimliğiyle yapılır).
3. *Faaliyetler → Kanıt klasöründen doldur:* yayın tarihleri (Crossref / AVES), `atiflar\` klasörlerinden kanıtlı atıf sayımı (endeks ve doçentlik başvurusu öncesi/sonrası ayrımıyla), ders dönemleri (EK-2 17.4 ve Md. 11(7)), klasörden faaliyet ekleme.
4. *Faaliyet tablosu:* her faaliyetin kanıt durumu; düzenleme panelinde klasörü / tam metni açma ve klasörü elle bağlama.
5. *Sonuç ekranı:* **Kanıt denetimi** (puan alan faaliyetlerde eksik belgeler, Md. 7) ve **Başvuru dosyası**: EK-2 sırasıyla USB klasörü + kapaklı, içindekilerli, yer imli birleşik PDF (atıf yapan yayınlardan yalnızca ilk sayfa ve atıf sayfası; taranmış belgeler hafifletilir, USB'deki dosyalar özgün kalır).

**Komut satırı:**
```bash
python -m kanit durum                       # arşivin özeti ve eksik kanıtlar
python -m kanit ozet                        # kunye.txt kontrol listeleri + Excel özeti
python -m kanit kimlik-yaz                  # eski klasörlere kayit.json yazar
python -m kanit arsivden-ekle --kaynak Tesvik2024="G:\Akademik Teşvik\Akademik Teşvik 2024" [--kopyala]
```
**Web of Science atıfları:** WoS'ta yayınlarınız → *Create Citation Report* → *Citing articles* (*Without self-citations*) → sol panelde *Web of Science Index*: SCI-EXPANDED, SSCI, A&HCI → *Export* → *Tab delimited file*, *Record content: Full Record and Cited References*. Dosyayı programda *Kanıt klasöründen doldur → 2b* ile yükleyin ya da:
```bash
python -m kanit wos-atif savedrecs.txt --soyad Saygılı            # plan
python -m kanit wos-atif savedrecs.txt --soyad Saygılı --uygula   # klasörleri oluştur
```
Her atıf yapan yayın, kaynakçasından bulunan yayınınızın `atiflar\WoS_<yıl>_<yazar>_<başlık> (SCI-E)\` klasörüne; WoS kaydından üretilen `endeks_bilgisi.pdf` ve (açık erişimliyse) tam metniyle konur. Öz atıflar ve arşivde zaten bulunan atıflar atlanır; ücretli tam metinler `_indirilecek_atiflar.xlsx` listesinde toplanır.

`arsivden-ekle`, eski teşvik / doçentlik / atama klasörlerindeki belgeleri faaliyet klasörlerine eşler; `--kopyala` verilmezse yalnızca plan çıkarır. Aynı içerik ikinci kez eklenmez; kaynak klasörlere dokunulmaz.

---

## 🔢 AVES Kodları
AVES'ten aktarılan her faaliyet, AVES'teki bölümünü ve sırasını gösteren bir kod alır. Bu kod faaliyet tablosunda (**AVES** sütunu) ve PDF raporunda (**#** sütunu) görünür; kanıt klasörleri de aynı kodlarla adlandırılabilir.

| Kod | Anlamı |
|---|---|
| UM | Uluslararası hakemli dergi makalesi |
| UL | Ulusal hakemli dergi makalesi |
| KB | Kitap / kitap bölümü |
| UB | Uluslararası bildiri |
| NB | Ulusal bildiri |

Sayı, AVES'teki sıradır (UM01 = AVES'teki ilk uluslararası makale). AVES'te aynı eser iki kez kayıtlıysa (aynı başlık, yıl ve sayfa) yalnızca bir kez alınır ve uyarı gösterilir. Künyesinde "Bölüm:" geçen kayıtlar kitap bölümü (EK-2 2.5 / 2.6) olarak aktarılır.

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
├── tnku_atama.py       # Puanlama motoru (EK-1, EK-2, kriter kontrolü)
├── tnku_streamlit.py   # Web arayüzü
├── kanit/              # Kanıt arşivi ve başvuru dosyası (yerel)
├── kanit_arayuz.py     # Arayüzün kanıt bölümleri
├── uak_kriterleri/     # ÜAK doçentlik kriter setleri
├── aves_yardimci.py    # AVES aktarım yardımcıları
├── tests/              # Testler
└── README.md           # Proje tanıtım dosyası
```

## ⚖️ Yasal Uyarı
Bu araç bilgilendirme amaçlıdır. Nihai puanlama ve değerlendirme süreci **TNKÜ Rektörlüğü ve ilgili komisyonlar** tarafından yürütülmektedir. Oluşabilecek hesaplama hatalarından geliştirici sorumlu tutulamaz.

## 🤝 Katkıda Bulunma
Eğer bir hata fark ederseniz veya güncel yönerge değişikliklerini sisteme yansıtmak isterseniz lütfen bir **Issue** açın veya **Pull Request** gönderin.

---
**Geliştirici:** Ahmet SAYGILI
**Son Güncelleme:** 16.04.2026
