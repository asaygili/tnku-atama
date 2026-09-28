"""AVES aktarım yardımcıları: kod, kitap bölümü ve tekrar ayıklama testleri."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import aves_yardimci as ay  # noqa: E402
import tnku_atama as t      # noqa: E402

# AVES'teki gerçek künyeler (asaygili.cv.nku.edu.tr, 2026)
DERLEME_1 = ("SAYGILI AHMET,ALBAYRAK SONGÜL, Knee Meniscus Segmentation and Tear Detection "
             "from MRI: A Review, Current Medical Imaging, vol. 16, pp. 2-15, Ocak, 2020.")
DERLEME_2 = ("SAYGILI AHMET,VARLI SONGÜL, Knee Meniscus Segmentation and Tear Detection from "
             "MRI: A Review, Current Medical Imaging Formerly Current Medical Imaging Reviews, "
             "vol. 16, pp. 2-15, Ocak, 2020.")
BASKA = ("SAYGILI AHMET,VARLI SONGÜL, Automated Diagnosis of Meniscus Tears from MRI of the "
         "Knee, International Scientific and Vocational Studies Journal, vol. 3, pp. 92-104, "
         "Aralık, 2019.")
BOLUM = ("ÖZKAN Emine Gül,SAYGILI AHMET, MÜHENDİSLİKTE MODERN VE ÇAĞDAŞ ARAŞTIRMALAR, "
         "Bölüm: Medikal Görüntü Analizinde Açıklanabilir Yapay Zeka (XAI): Yöntemler, "
         "Değerlendirme Metrikleri ve Klinik Perspektifler. Sayfa:-, Yayın Yeri: All Sciences "
         "Academy, 2026.")


class AvesKodu(unittest.TestCase):
    def test_onekler(self):
        self.assertEqual(ay.aves_kodu("ulusl_makale", 1), "UM01")
        self.assertEqual(ay.aves_kodu("ulusal_makale", 3), "UL03")
        self.assertEqual(ay.aves_kodu("kitap_ulusl", 2), "KB02")
        self.assertEqual(ay.aves_kodu("ulusl_bildiri", 14), "UB14")
        self.assertEqual(ay.aves_kodu("ulusal_bildiri", 5), "NB05")
        self.assertEqual(ay.aves_kodu("proje", 1), "")

    def test_kod_detaylara_tasinir(self):
        aday = t.AdayBilgi(faaliyetler=[t.Faaliyet("1.1", aves_kod="UM22"), t.Faaliyet("12.5")])
        self.assertEqual([d["aves_kod"] for d in t.puan_hesapla(aday)["detaylar"]], ["UM22", ""])


class KitapBolumu(unittest.TestCase):
    def test_uluslararasi_bolum_2_5(self):
        # AVES başlığı "Uluslararası Kitaplar veya Kitap Bölümleri" → kitap_ulusl
        self.assertEqual(ay.kitap_ek2_kodu("kitap_ulusl", BOLUM), "2.5")

    def test_uluslararasi_kitap_2_2(self):
        self.assertEqual(ay.kitap_ek2_kodu(
            "kitap_ulusl", "SAYGILI AHMET, Derin Öğrenme, Springer, 2024."), "2.2")

    def test_ulusal(self):
        self.assertEqual(ay.kitap_ek2_kodu("kitap_ulusal", BOLUM), "2.6")
        self.assertEqual(ay.kitap_ek2_kodu("kitap_ulusal", "SAYGILI AHMET, Kitap, 2024."), "2.3")

    def test_kitap_bolumu_paneli(self):
        # Eski kodda "bölüm" in "kitap_bolum" hiç doğru olmuyordu
        self.assertEqual(ay.kitap_ek2_kodu("kitap_bolum", "SAYGILI AHMET, X, 2024."), "2.6")

    def test_puan_farki(self):
        bolum = t.faaliyet_puan_hesapla(t.Faaliyet("2.5", toplam_yazar=2, yazar_sirasi=2))[0]
        kitap = t.faaliyet_puan_hesapla(t.Faaliyet("2.2", toplam_yazar=2, yazar_sirasi=2))[0]
        self.assertEqual((bolum, kitap), (18, 36))


class TekrarAyiklama(unittest.TestCase):
    def test_baslik_cikar(self):
        self.assertEqual(ay.baslik_cikar(DERLEME_1),
                         "Knee Meniscus Segmentation and Tear Detection from MRI: A Review")
        self.assertTrue(ay.baslik_cikar(BOLUM).startswith("Medikal Görüntü Analizinde"))
        self.assertTrue(ay.baslik_cikar(
            "CİHAN PINAR, SAYGILI AHMET, Özmen Nihat Eren, Akyüzlü Muhammed, Identification "
            "and Recognition of Animals, Kafkas, 2023.").startswith("Identification"))

    def test_ayni_eser_tek_kez_alinir(self):
        ogeler = [{"metin": BASKA}, {"metin": DERLEME_1, "link": "https://x/cv/yayinlar/[{"},
                  {"metin": DERLEME_2, "link": "http://dx.doi.org/10.2174/1573405614666181017122109"}]
        kalan, atilan = ay.tekrarlari_ayikla(ogeler)
        # DOI bağlantısı olan (3. sıradaki) tutulur; AVES sırası korunur
        self.assertEqual([s for s, _ in kalan], [1, 3])
        self.assertEqual([(s, tut) for s, _, tut in atilan], [(2, 3)])

    def test_baglanti_yoksa_ilki_tutulur(self):
        kalan, atilan = ay.tekrarlari_ayikla([{"metin": DERLEME_1}, {"metin": DERLEME_2}])
        self.assertEqual(([s for s, _ in kalan], [(s, tut) for s, _, tut in atilan]),
                         ([1], [(2, 1)]))

    def test_farkli_sayfa_farkli_eser(self):
        a = DERLEME_1
        b = DERLEME_1.replace("pp. 2-15", "pp. 20-35")
        self.assertEqual(len(ay.tekrarlari_ayikla([{"metin": a}, {"metin": b}])[0]), 2)

    def test_tekrarsiz_liste_degismez(self):
        kalan, atilan = ay.tekrarlari_ayikla([{"metin": DERLEME_1}, {"metin": BASKA}])
        self.assertEqual((len(kalan), atilan), (2, []))


if __name__ == "__main__":
    unittest.main()
