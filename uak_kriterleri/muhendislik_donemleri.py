"""
ÜAK doçentlik başvuru şartları – Mühendislik Temel Alanı (Tablo 9), Mart 2022 dışındaki dönemler.

Kaynak: https://www.uak.gov.tr/page/docentlik-basvuru-sartlari-kLPHX (dönem PDF'leri).
Metinler karşılaştırıldığında içerik şu gruplarda aynıdır:
  • 2016 Nisan                    → koşul sistemi (puan yok)            NISAN_2016
  • 2016 Aralık – 2017 Aralık     → eski puan tablosu                   ARALIK_2016
  • 2018 Nisan – 2023 Ekim        → mart_2022.py (MUHENDISLIK)
  • 2024 Mart – 2026 Ekim         → yeni puan tablosu (Q'ya göre)       MART_2024
    (2024 Ekim: eğitim kaleminde "ön lisans" eklendi; 2025 Mart: ulusal makalede editöre
     mektup vb. "diğer" hakemli dergiden "hakemli" dergiye – puanlamayı değiştirmez.
     2026 Ekim için ayrı Mühendislik tablosu yayımlanmadı; 2026 Mart tablosu esas alındı.)

EK-2 → ÜAK eşleştirmesinde yapılan yorumlar dosya içinde not edilmiştir.
"""

from . import AltKosul, Bolum, Kalem, KriterSeti, kaydet

Q_2024 = (("Q1", 30), ("Q2", 20), ("Q3", 15), ("Q4", 10))

# ── 2024 Mart – 2026 Ekim ───────────────────────────────────────────────────
MART_2024 = kaydet(KriterSeti(
    kimlik="2024-mart/muhendislik",
    donem="Mart 2024 – Ekim 2026",
    temel_alan="Mühendislik",
    tablo="Tablo 9",
    kosul_no="91",
    toplam_min=100,
    doktora_sonrasi_min=90,
    doktora_sonrasi_haric=(3,),          # tezden üretilmiş yayın puanları hariç
    kaynak="ÜAK 2024 Mart – 2026 Mart Doçentlik Başvuru Şartları – Tablo 9",
    bolumler=(
        Bolum(1, "Uluslararası Makale", (
            # SCIE/SSCI makale (derleme dahil); Q girilmemişse Q4 sayılır. AHCI (20 p)
            # EK-2'de SCI ile aynı kodda olduğundan ayrılamaz.
            Kalem("1a", "SCIE/SSCI dergide makale (Q1 30, Q2 20, Q3 15, Q4 10)", 30,
                  ("1.1", "1.3"), yazar_dagilimi="makale", q_puanlari=Q_2024),
            Kalem("1c", "ESCI veya Scopus dergide makale", 10, ("1.4",), yazar_dagilimi="makale"),
            Kalem("1d", "Diğer uluslararası indeksli dergide makale", 5, ("1.5",),
                  yazar_dagilimi="makale"),
            Kalem("1e", "Editöre mektup, araştırma notu, özet, kitap kritiği", 3,
                  ("1.2", "1.9"), yazar_dagilimi="makale"),
        ), alt_kosullar=(
            AltKosul("1a kapsamında doktora sonrası ≥40 puan (Q1–Q3 dergide en az bir "
                     "makalede başlıca yazar)", ("1a",), 40, baslica_yazar_gerekli=True,
                     baslica_q=("Q1", "Q2", "Q3"), doktora_sonrasi=True),
        )),
        Bolum(2, "Ulusal Makale", (
            Kalem("2a", "TR Dizin dergide makale", 10, ("1.6",), yazar_dagilimi="makale"),
            Kalem("2b", "Diğer hakemli dergide makale", 4, ("1.7", "1.8", "1.10"),
                  yazar_dagilimi="makale"),
            Kalem("2c", "Hakemli dergide editöre mektup, araştırma notu, özet, kitap kritiği", 2,
                  ("1.11",), yazar_dagilimi="makale"),
        ), alt_kosullar=(
            AltKosul("2a kapsamında doktora sonrası ≥10 puan", ("2a",), 10, doktora_sonrasi=True),
        )),
        Bolum(3, "Lisansüstü Tezlerden Üretilmiş Yayın", (
            Kalem("3a", "Tezden: SCIE/SSCI/AHCI makale", 20, ("1.1", "1.3"), tez=True,
                  yazar_dagilimi="makale"),
            Kalem("3b", "Tezden: ESCI/Scopus makale", 10, ("1.4",), tez=True,
                  yazar_dagilimi="makale"),
            Kalem("3c", "Tezden: diğer uluslararası indeksli makale", 5, ("1.5",), tez=True,
                  yazar_dagilimi="makale"),
            Kalem("3d", "Tezden: TR Dizin makale", 8, ("1.6",), tez=True, yazar_dagilimi="makale"),
            Kalem("3e", "Tezden: BKCI kitap", 20, ("2.1",), tez=True, yazar_dagilimi="esit"),
            Kalem("3f", "Tezden: BKCI kitapta bölüm", 10, ("2.4",), tez=True, yazar_dagilimi="esit"),
            Kalem("3g", "Tezden: diğer uluslararası/ulusal kitap", 5, ("2.2", "2.3"), tez=True,
                  yazar_dagilimi="esit"),
            Kalem("3h", "Tezden: diğer kitapta bölüm", 3, ("2.5", "2.6"), tez=True,
                  yazar_dagilimi="esit"),
            Kalem("3ı", "Tezden: CPCI'da yayımlanmış bildiri", 5, ("3.1",), tez=True,
                  yazar_dagilimi="esit"),
            Kalem("3i", "Tezden: diğer bilimsel toplantı bildirisi", 2,
                  ("3.2", "3.3", "3.4", "3.5", "3.6", "3.7", "3.8"), tez=True,
                  yazar_dagilimi="esit"),
        ), max_puan=20, min_yayin=1, profesorlukte_aranmaz=True,
            min_yayin_kalemleri=("3a", "3b", "3c", "3d", "3e", "3f", "3g", "3h")),
        Bolum(4, "Kitap", (
            Kalem("4a", "BKCI kapsamında kitap", 20, ("2.1",), yazar_dagilimi="esit"),
            Kalem("4b", "BKCI kapsamında kitapta bölüm", 10, ("2.4",), yazar_dagilimi="esit"),
            Kalem("4c", "Diğer uluslararası/ulusal kitap", 5, ("2.2", "2.3"), yazar_dagilimi="esit"),
            Kalem("4d", "Diğer kitapta bölüm", 3, ("2.5", "2.6"), yazar_dagilimi="esit"),
        ), max_puan=20, alt_sinirlar=((("4c", "4d"), 5),),
            elle_kontrol=("Ders kitabı puanlanmaz; aynı kitaptaki bölümlerden yalnızca biri "
                          "puanlanır",)),
        Bolum(5, "Atıf", (
            Kalem("5a", "SCIE/SSCI/AHCI/ESCI/Scopus kapsamında atıf", 3, ("5.1", "5.2"), tez=None),
            Kalem("5b", "BKCI kapsamındaki kitapta atıf", 2, ("5.7",), tez=None),
            Kalem("5c", "TR Dizin dergide atıf", 2, ("5.5",), tez=None),
            Kalem("5d", "Diğer uluslararası/ulusal kitap veya dergide atıf", 1,
                  ("5.3", "5.4", "5.6", "5.8"), tez=None),
        ), max_puan=10, alt_kosullar=(
            AltKosul("5. Atıf: doktora sonrası yayınlardan ≥5 puan",
                     ("5a", "5b", "5c", "5d"), 5, doktora_sonrasi=True),
        )),
        Bolum(6, "Lisansüstü Tez Danışmanlığı", (
            Kalem("6a", "Tamamlanmış doktora tezi danışmanlığı", 5, ("17.1",), tez=None,
                  ikinci_danisman_yarim=True),
            Kalem("6b", "Tamamlanmış yüksek lisans tezi danışmanlığı", 3, ("17.2",), tez=None,
                  ikinci_danisman_yarim=True),
        ), max_puan=10,
            elle_kontrol=("Yalnızca tamamlanmış tezlerin danışmanlığı puanlanır",)),
        Bolum(7, "Bilimsel Araştırma Projesi", (
            Kalem("7a1", "AB Çerçeve Programı/TÜBİTAK projesinde koordinatör/yürütücü", 15,
                  ("12.1", "12.3", "12.5"), tez=None, tamamlanmis=True),
            Kalem("7a2", "AB Çerçeve Programı/TÜBİTAK projesinde araştırmacı", 10,
                  ("12.2", "12.4", "12.6"), tez=None, tamamlanmis=True),
            Kalem("7b", "Uluslararası destekli projede yürütücü/araştırmacı", 10,
                  ("12.9", "12.10"), tez=None, tamamlanmis=True),
            Kalem("7c", "Üniversite dışı kamu/özel kuruluşla Ar-Ge/Ür-Ge projesi", 5,
                  ("12.7", "12.8", "12.13", "12.14"), tez=None, tamamlanmis=True),
            Kalem("7d", "Üniversite BAP projesinde yürütücü", 3, ("12.11",), tez=None,
                  tamamlanmis=True),
        ), max_puan=30,
            elle_kontrol=("Yalnızca başarıyla tamamlanmış projeler; TÜBİTAK öğrenci projeleri ve "
                          "BAP tez/uzmanlık projeleri hariç; danışmanlık (5 p) programda ayrı "
                          "girilmez", "Erasmus+, IPA vb. AB Çerçeve dışı AB projeleri 7b'dir")),
        Bolum(8, "Bilimsel Toplantı", (
            Kalem("8a", "CPCI'da yayımlanmış bildiri", 5, ("3.1",), yazar_dagilimi="esit"),
            Kalem("8b", "Diğer uluslararası/ulusal bilimsel toplantı bildirisi", 3,
                  ("3.2", "3.3", "3.4", "3.5", "3.6", "3.7", "3.8"), yazar_dagilimi="esit"),
        ), max_puan=10, alt_kosullar=(
            AltKosul("8. Bilimsel toplantı: doktora sonrası ≥5 puan", ("8a", "8b"), 5,
                     doktora_sonrasi=True),
        ), elle_kontrol=("Aynı bilimsel toplantıda en fazla bir çalışma puanlanır",
                         "8b'de toplantının düzenleme komitesinde görevlendirilmiş akademisyen "
                         "temsilci bulunmalıdır; CPCI'da yayımlanan uluslararası bildiriler 8a'dır")),
        Bolum(9, "Eğitim-Öğretim", (), min_puan=2, max_puan=6, egitim_sayimi=True,
              iki_yil_egitim_puani=2,
              elle_kontrol=("Doktora sonrası yükseköğretimde en az 2 yıl kadrolu görev de 2 puan "
                            "sayılır",)),
        Bolum(10, "Patent / Faydalı Model", (
            Kalem("10a", "Tescil edilmiş uluslararası patent", 20, ("11.1",), tez=None,
                  yazar_dagilimi="esit", patent_durumlari=("tescilli",)),
            Kalem("10b", "Tescil edilmiş ulusal patent", 10, ("11.2", "11.7"), tez=None,
                  yazar_dagilimi="esit", patent_durumlari=("tescilli",)),
            Kalem("10c", "Tescil edilmiş faydalı model", 5, ("11.3", "11.4"), tez=None,
                  yazar_dagilimi="esit"),
            Kalem("10d", "Değerlendirmeye alınmış patent başvurusu", 2, ("11.1", "11.2", "11.7"),
                  tez=None, yazar_dagilimi="esit",
                  patent_durumlari=("basvuru", "arastirma_raporu")),
        )),
        Bolum(11, "Ödül", (), max_puan=25,
              elle_kontrol=("YÖK Yılın Doktora Tezi / Üstün Başarı, TÜBİTAK Bilim / Teşvik, TÜBA "
                            "GEBİP / TESEP ödülleri 25 puan – programda ayrı girilmez",)),
        Bolum(12, "Editörlük", (
            Kalem("12a", "SCIE/SSCI/AHCI/ESCI/Scopus dergide editörlük", 2, ("4.1", "4.2"),
                  tez=None),
            Kalem("12b", "BKCI/Scopus kitapta editörlük", 1, ("4.8",), tez=None),
            Kalem("12c", "TR Dizin dergide editörlük", 1, ("4.6",), tez=None),
        ), max_puan=4),
        Bolum(13, "Diğer", (
            Kalem("13a", "Web of Science h-indeksi en az 5", 5, ("5.9",), tez=None, esik_adet=5),
        ), max_puan=10,
            elle_kontrol=("İlk 300 üniversitede kesintisiz en az 6 ay yurt dışı araştırma/öğretim "
                          "5 puan – programda ayrı girilmez",)),
    ),
))

# ── 2016 Aralık – 2017 Aralık ───────────────────────────────────────────────
MAKALE_ULUSLARARASI = ("1.4", "1.5", "1.7")

ARALIK_2016 = kaydet(KriterSeti(
    kimlik="2016-aralik/muhendislik",
    donem="Aralık 2016 – Aralık 2017",
    temel_alan="Mühendislik",
    tablo="Tablo 9",
    kosul_no="91",
    toplam_min=100,
    doktora_sonrasi_min=90,
    ilk_yazar_baslica=True,       # bu dönemde ilk yazar da başlıca yazar sayılır
    kaynak="ÜAK 2016 Aralık – 2017 Aralık Doçentlik Başvuru Şartları – Tablo 9",
    bolumler=(
        Bolum(1, "Makaleler", (
            Kalem("1a", "SCI/SCI-E/SSCI/AHCI makale", 20, ("1.1",), yazar_dagilimi="makale"),
            Kalem("1b", "Diğer uluslararası hakemli dergide makale", 8,
                  MAKALE_ULUSLARARASI, yazar_dagilimi="makale"),
            Kalem("1c", "ULAKBİM ulusal hakemli dergide makale", 8, ("1.6",),
                  yazar_dagilimi="makale"),
        ), alt_kosullar=(
            AltKosul("1a kapsamında ≥40 puan (en az bir makalede başlıca yazar)",
                     ("1a",), 40, baslica_yazar_gerekli=True),
            AltKosul("1c kapsamında ≥8 puan", ("1c",), 8),
        )),
        Bolum(2, "Lisansüstü Tezlerden Üretilmiş Yayınlar", (
            Kalem("2a", "Tezden: SCI/SCI-E/SSCI/AHCI makale", 10, ("1.1",), tez=True,
                  yazar_dagilimi="makale"),
            Kalem("2b", "Tezden: diğer uluslararası hakemli makale", 5, MAKALE_ULUSLARARASI,
                  tez=True, yazar_dagilimi="makale"),
            Kalem("2c", "Tezden: uluslararası kongre tam metin sözlü bildiri", 5, ("3.1", "3.2"),
                  tez=True, yazar_dagilimi="esit"),
            Kalem("2d", "Tezden: ulusal kongre tam metin sözlü bildiri", 3, ("3.6",), tez=True,
                  yazar_dagilimi="esit"),
        ), max_puan=10),
        Bolum(3, "Kitap", (
            Kalem("3a", "Tanınmış uluslararası yayınevi özgün bilimsel kitap", 15,
                  ("2.1", "2.2"), yazar_dagilimi="esit"),
            Kalem("3b", "Tanınmış uluslararası yayınevi kitap editörlüğü", 10, ("4.8", "4.9"),
                  yazar_dagilimi="esit"),
            Kalem("3c", "Tanınmış uluslararası yayınevi kitapta bölüm", 10, ("2.4", "2.5"),
                  yazar_dagilimi="esit"),
            Kalem("3d", "Tanınmış ulusal yayınevi özgün bilimsel kitap", 10, ("2.3",),
                  yazar_dagilimi="esit"),
        ), max_puan=15,
            elle_kontrol=("Kitap üst sınırı (15) PDF metninin sırasından çıkarıldı; "
                          "kılavuzla doğrulayın",)),
        Bolum(4, "Patent", (
            Kalem("4b", "Uluslararası patent", 20, ("11.1",), tez=None, yazar_dagilimi="esit",
                  patent_raporlu=True),
            Kalem("4c", "Ulusal patent", 10, ("11.2", "11.7"), tez=None, yazar_dagilimi="esit",
                  patent_raporlu=True),
        )),
        Bolum(5, "Atıflar", (
            Kalem("5a", "SCI/SCI-E/SSCI/AHCI dergi / uluslararası kitapta atıf", 3,
                  ("5.1", "5.7"), tez=None),
            Kalem("5b", "Diğer endeksli dergi / uluslararası kitap bölümünde atıf", 2,
                  ("5.2", "5.3"), tez=None),
            Kalem("5c", "Ulusal hakemli dergi / ulusal kitapta atıf", 1, ("5.5", "5.6", "5.8"),
                  tez=None),
        ), min_puan=6),
        Bolum(6, "Lisansüstü Tez Danışmanlığı", (
            Kalem("6a", "Doktora tez danışmanlığı", 4, ("17.1",), tez=None,
                  ikinci_danisman_yarim=True),
            Kalem("6b", "Yüksek lisans tez danışmanlığı", 2, ("17.2",), tez=None,
                  ikinci_danisman_yarim=True),
        ), max_puan=10,
            elle_kontrol=("Yalnızca tamamlanan lisansüstü tezlerin danışmanlığı puanlanır",)),
        Bolum(7, "Bilimsel Araştırma Projesi", (
            Kalem("7a", "AB Çerçeve programı koordinatör / baş araştırmacı", 15, ("12.1",),
                  tez=None),
            Kalem("7b", "AB Çerçeve programı ortak araştırmacı", 10, ("12.2",), tez=None),
            Kalem("7c", "Diğer uluslararası destekli projede yürütücü", 8, ("12.9",), tez=None),
            Kalem("7d", "Üniversite dışı kamu kurumu projesinde yürütücü", 6,
                  ("12.3", "12.5", "12.13"), tez=None),
        ), elle_kontrol=("7c ve 7d'de yalnızca yürütücülük puanlanır",)),
        Bolum(8, "Bilimsel Toplantı", (
            Kalem("8a", "Uluslararası toplantıda sözlü bildiri", 3, ("3.1", "3.2", "3.3"),
                  yazar_dagilimi="esit"),
            Kalem("8b", "Ulusal toplantıda sözlü bildiri", 2, ("3.5", "3.6", "3.7"),
                  yazar_dagilimi="esit"),
        ), min_puan=5, max_puan=10,
            elle_kontrol=("Aynı toplantıda sunulan yalnız bir bildiri puanlanır",)),
        Bolum(9, "Eğitim-Öğretim Faaliyeti", (
            Kalem("9a", "Bir dönem yüksek lisans / doktora dersi", 3, (), tez=None),
            Kalem("9b", "Bir dönem önlisans / lisans dersi", 1, ("17.4",), tez=None),
        ), min_puan=2, max_puan=4, iki_yil_egitim_puani=2,
            elle_kontrol=("En az 2 yıl öğretim elemanı olarak çalışmış olmak da şartı sağlar",)),
    ),
))

# ── 2016 Nisan: koşul sistemi ───────────────────────────────────────────────
NISAN_2016 = kaydet(KriterSeti(
    kimlik="2016-nisan/muhendislik",
    donem="Nisan 2016",
    temel_alan="Mühendislik",
    tablo="Tablo 9",
    kosul_no="91",
    toplam_min=3,                 # kosul_sistemi: en az üç özgün makale
    doktora_sonrasi_min=0,
    kosul_sistemi=True,
    kaynak="ÜAK 2016 Nisan Doçentlik Başvuru Koşulları – Tablo 9",
    bolumler=(
        Bolum(1, "SCI-Expanded / SSCI özgün makale", (
            Kalem("1a", "SCI-E/SSCI dergide özgün makale (derleme, mektup vb. hariç)", 1,
                  ("1.1",), tez=None),
        ), alt_kosullar=(
            AltKosul("En az biri tezden üretilmemiş ve başlıca yazar olarak SCI-E dergide",
                     ("1a",), 0, baslica_yazar_gerekli=True),
        ), elle_kontrol=("Başlıca yazar olunan makalenin lisansüstü tezden üretilmemiş olması "
                         "elle doğrulanmalıdır",)),
    ),
))
