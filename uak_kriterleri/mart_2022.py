"""
ÜAK Mart 2022 doçentlik başvuru şartları.

Kaynak: ÜAK 2022 Mart dönemi doçentlik başvuru şartları, Tablo 9 – Mühendislik
Temel Alanı (koşul no 91; 901–931 kodlu bilim alanları).

EK-2 → ÜAK eşleştirmesinde yapılan yorumlar:
  • 1.2 / 1.3 / 1.9 / 1.11 (teknik not, derleme vb.) Madde 1'e girmez
    ("editöre mektup, özet, derleme, teknik not ve kitap kritiği hariç").
  • TR Dizin dışı ulusal makaleler (1.8, 1.10) 1c'ye girmez (ULAKBİM şartı).
  • Çeviri kitaplar (2.9–2.12) ve tahkik/neşir (2.13) Madde 3'e girmez.
  • Patent başvurusu, araştırma raporu yoksa ÜAK patent tanımını karşılamaz.
  • BAP (12.11/12.12) ve TGB projeleri (12.7/12.8) 7d'ye girmez
    ("üniversite dışındaki kamu kurumlarıyla" yapılan projeler).
  • 17.4 dersleri 9b (önlisans/lisans, 2 puan) sayılır; lisansüstü ders için
    3 puan hakkı varsa elle değerlendirilmelidir.
"""

from . import AltKosul, Bolum, Kalem, KriterSeti, kaydet

MAKALE_ULUSLARARASI = ("1.4", "1.5", "1.7")

MUHENDISLIK = kaydet(KriterSeti(
    kimlik="2022-mart/muhendislik",
    donem="Mart 2022",
    temel_alan="Mühendislik",
    tablo="Tablo 9",
    kosul_no="91",
    toplam_min=100,
    doktora_sonrasi_min=90,
    kaynak="ÜAK 2022 Mart Doçentlik Başvuru Şartları – Tablo 9",
    bolumler=(
        Bolum(1, "Makaleler", (
            Kalem("1a", "SCI/SCI-E/SSCI/AHCI makale", 20, ("1.1",),
                  yazar_dagilimi="makale"),
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
            Kalem("2a", "Tezden: SCI/SCI-E/SSCI/AHCI makale", 10, ("1.1",),
                  tez=True, yazar_dagilimi="makale"),
            Kalem("2b", "Tezden: diğer uluslararası/ulusal hakemli makale", 5,
                  MAKALE_ULUSLARARASI + ("1.6", "1.8", "1.10"),
                  tez=True, yazar_dagilimi="makale"),
            Kalem("2c", "Tezden: uluslararası kongre tam metin sözlü bildiri", 5,
                  ("3.1", "3.2"), tez=True, yazar_dagilimi="esit"),
            Kalem("2d", "Tezden: ulusal kongre tam metin sözlü bildiri", 3,
                  ("3.6",), tez=True, yazar_dagilimi="esit"),
        ), max_puan=10, min_yayin=1, profesorlukte_aranmaz=True),
        Bolum(3, "Kitap", (
            Kalem("3a", "Uluslararası yayınevi kitap", 20, ("2.1", "2.2", "2.7"),
                  yazar_dagilimi="esit"),
            Kalem("3b", "Uluslararası yayınevi kitap editörlüğü / bölüm", 10,
                  ("2.4", "2.5", "4.8", "4.9"), yazar_dagilimi="esit"),
            Kalem("3c", "Ulusal yayınevi kitap", 15, ("2.3", "2.8"),
                  yazar_dagilimi="esit"),
            Kalem("3d", "Ulusal yayınevi kitap editörlüğü / bölüm", 8,
                  ("2.6", "4.10"), yazar_dagilimi="esit"),
        ), max_puan=20,
            elle_kontrol=("Aynı kitaptaki bölümlerden en fazla ikisi dikkate alınır",)),
        Bolum(4, "Patent", (
            Kalem("4b", "Uluslararası patent", 20, ("11.1",), tez=None,
                  yazar_dagilimi="esit", patent_raporlu=True),
            Kalem("4c", "Ulusal patent", 10, ("11.2", "11.7"), tez=None,
                  yazar_dagilimi="esit", patent_raporlu=True),
        )),
        Bolum(5, "Atıflar", (
            Kalem("5a", "SCI/SCI-E/SSCI/AHCI dergi / uluslararası kitapta atıf", 3,
                  ("5.1", "5.7"), tez=None),
            Kalem("5b", "Diğer endeksli dergi / uluslararası kitap bölümünde atıf", 2,
                  ("5.2", "5.3"), tez=None),
            Kalem("5c", "Ulusal hakemli dergi / ulusal kitapta atıf", 1,
                  ("5.5", "5.6", "5.8"), tez=None),
        ), min_puan=4, max_puan=20),
        Bolum(6, "Lisansüstü Tez Danışmanlığı", (
            Kalem("6a", "Doktora tez danışmanlığı", 4, ("17.1",), tez=None,
                  ikinci_danisman_yarim=True),
            Kalem("6b", "Yüksek lisans tez danışmanlığı", 2, ("17.2",), tez=None,
                  ikinci_danisman_yarim=True),
        ), max_puan=10),
        Bolum(7, "Bilimsel Araştırma Projesi", (
            Kalem("7a", "AB Çerçeve programı koordinatör / baş araştırmacı", 15,
                  ("12.1",), tez=None),
            Kalem("7b", "AB Çerçeve programı ortak araştırmacı", 10,
                  ("12.2",), tez=None),
            Kalem("7c", "Diğer uluslararası destekli projede görev", 6,
                  ("12.9", "12.10"), tez=None),
            Kalem("7d", "Üniversite dışı kamu kurumu projesinde görev", 4,
                  ("12.3", "12.4", "12.5", "12.6", "12.13", "12.14"), tez=None),
        ), max_puan=20),
        Bolum(8, "Bilimsel Toplantı Faaliyeti", (
            Kalem("8a", "Uluslararası toplantıda bildiri (poster hariç)", 3,
                  ("3.1", "3.2", "3.3"), yazar_dagilimi="esit"),
            Kalem("8b", "Ulusal toplantıda bildiri (poster hariç)", 2,
                  ("3.5", "3.6", "3.7"), yazar_dagilimi="esit"),
        ), min_puan=5, max_puan=10,
            elle_kontrol=("Aynı toplantıda sunulan en fazla bir bildiri puanlanır",)),
        Bolum(9, "Eğitim-Öğretim Faaliyeti", (
            Kalem("9b", "Bir dönem önlisans / lisans dersi", 2, ("17.4",), tez=None),
        ), min_puan=2, max_puan=4, iki_yil_egitim_puani=2,
            elle_kontrol=("Lisansüstü dersler dönem başına 3 puandır (9a); "
                          "program tüm dersleri 9b olarak sayar",)),
    ),
))
