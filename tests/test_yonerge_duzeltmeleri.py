"""Yönerge denetiminde bulunan hataların düzeltmeleri (EYS-YNG-129 Rev. 2, ÜAK Mart 2022)."""

import os
import sys
import unittest
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import aves_yardimci as ay   # noqa: E402
import tnku_atama as t       # noqa: E402
import uak_kriterleri as uak  # noqa: E402

F = t.Faaliyet


def puan(*faaliyetler, **aday):
    return t.puan_hesapla(t.AdayBilgi(faaliyetler=list(faaliyetler), **aday))["toplam"]


def kriter(aday, metin):
    return next(k for k in t.kriter_kontrol(aday)["kriterler"] if metin in k["kriter"])


class Ek2Kalemleri(unittest.TestCase):
    def test_kod_sirasi_alt_kalemler(self):
        kodlar = sorted([k for k in t.EK2_PUANLAR if k.startswith("9.")], key=t.kod_sirasi)
        self.assertLess(kodlar.index("9.16"), kodlar.index("9.17a"))
        self.assertLess(kodlar.index("9.17c"), kodlar.index("9.18a"))

    def test_18_8_en_fazla_10(self):
        self.assertEqual(puan(F("18.8", adet=8)), 10)
        self.assertEqual(puan(F("18.8", adet=3), F("18.8", adet=4)), 10)

    def test_17_3_yuksek_lisans_yari(self):
        self.assertEqual(puan(F("17.3")), 2)
        self.assertEqual(puan(F("17.3", yuksek_lisans=True)), 1)

    def test_11_10_uluslararasi_iki_kat(self):
        self.assertEqual(puan(F("11.10", uluslararasi=True)), 4)

    def test_14_9_ekip_paylasir(self):
        self.assertEqual(puan(F("14.9", ekip_sayisi=4)), 10)

    def test_11_2_yalniz_kayitli(self):
        self.assertEqual(puan(F("11.2", patent_durum="tescilli")), 35)
        self.assertEqual(puan(F("11.2", patent_durum="basvuru")), 0)


class Ek1Kurallari(unittest.TestCase):
    def test_d_bir_yillik_atamada_uygulanmaz(self):
        a = t.AdayBilgi(kadro_turu="dr_yeniden", yeniden_sure=1,
                        faaliyetler=[F("2.2"), F("18.4")])
        self.assertIn("✓", kriter(a, "PUAN-1 ≥20")["durum"])
        a.bir_yil_atama_sayisi = 3                       # iki kezden fazla → sınır geçerli
        self.assertIn("✗", kriter(a, "PUAN-1 ≥20")["durum"])

    def test_guzel_sanatlar_docent_12_5(self):
        a = t.AdayBilgi(kadro_turu="docent", guzel_sanat=True,
                        faaliyetler=[F("1.6", toplam_yazar=1)])     # 13 puan
        self.assertIn("PUAN-1 ≥12.5", kriter(a, "PUAN-1")["kriter"])

    def test_bilinmeyen_kadro_uygun_sayilmaz(self):
        self.assertFalse(t.kriter_kontrol(t.AdayBilgi(kadro_turu="profesör"))["genel_sonuc"])

    def test_docent_doktora_oncesi_sayilmaz(self):
        a = t.AdayBilgi(kadro_turu="docent", doktora_tarihi=date(2015, 1, 1), faaliyetler=[
            F("1.1", yayin_tarihi=date(2014, 5, 1)), F("1.1", yayin_tarihi=date(2016, 5, 1)),
            F("1.1")])
        self.assertEqual(t.kriter_kontrol(a)["puanlar"]["puan1"], 50)

    def test_dr_yeniden_puan_muafiyeti(self):
        a = t.AdayBilgi(kadro_turu="dr_yeniden", yeniden_sure=3,
                        yeniden_puan_muafiyeti="docent_ilk_uzatim")
        k = t.kriter_kontrol(a)["kriterler"]
        self.assertFalse(any("PUAN" in x["kriter"] for x in k))
        self.assertTrue(all("✓" in x["durum"] for x in k))
        a.yeniden_sure = 2                                # bu uzatım 3 yıllık yapılır
        self.assertFalse(t.kriter_kontrol(a)["genel_sonuc"])

    def test_yillik_program_iki_yil(self):
        a = t.AdayBilgi(kadro_turu="docent", ders_yillik_program_yil=2)
        self.assertIn("✓", kriter(a, "Md. 10(3)")["durum"])
        a.ders_yillik_program_yil = 1
        self.assertIn("✗", kriter(a, "Md. 10(3)")["durum"])


class AvesKodlari(unittest.TestCase):
    def test_makale_turu_ve_endeks(self):
        k = ay.makale_ek2_kodu
        self.assertEqual(k(["SCI"], tip="Özgün Makale"), "1.1")
        self.assertEqual(k(["SCI-Expanded"], "European Review for Medical", tip="Özgün Makale"),
                         "1.1")
        self.assertEqual(k(["SCI-Expanded"], tip="Derleme Makale"), "1.3")
        self.assertEqual(k(["SCI-Expanded"], tip="Editöre Mektup"), "1.2")
        self.assertEqual(k(["Alan Endeksleri"], tip="Özgün Makale"), "1.4")
        self.assertEqual(k(["ESCI: Emerging Sources Citation Index"], tip="Derleme Makale"), "1.9")
        self.assertEqual(k(["Diğer Endeksler"], tip="Özgün Makale"), "1.5")
        self.assertEqual(k(["Endekste Taranmıyor"], tip="Özgün Makale"), "1.7")
        self.assertEqual(k(["TR DİZİN"], ulusal=True, tip="Derleme Makale"), "1.9")
        self.assertEqual(k(["Endekste Taranmıyor"], ulusal=True, tip="Özgün Makale"), "1.8")
        self.assertEqual(k(["SCI-Expanded"], ulusal=True, tip="Özgün Makale"), "1.1")

    def test_bildiri_turu(self):
        self.assertEqual(ay.bildiri_ek2_kodu("Özet bildiri", "", True), "3.3")
        self.assertEqual(ay.bildiri_ek2_kodu("Poster", "", True), "3.4")
        self.assertEqual(ay.bildiri_ek2_kodu("Tam metin bildiri", "", False), "3.6")
        self.assertEqual(ay.bildiri_ek2_kodu("Poster", "", False), "3.8")

    def test_kitap_turu(self):
        self.assertEqual(ay.kitap_ek2_kodu("kitap_ulusl", "x", "Kitap Tercümesi"), "2.9")
        self.assertEqual(ay.kitap_ek2_kodu("kitap_ulusal", "x", "Ansiklopedi Maddesi"), "3.10")
        self.assertEqual(ay.kitap_ek2_kodu("kitap_ulusal", "x", "Ders Kitabı"), "2.8")
        self.assertEqual(ay.kitap_ek2_kodu("kitap_ulusl", "x", "Bilimsel Kitap"), "2.2")


class UakKalemi(unittest.TestCase):
    def test_uak_kalem_zorlamasi(self):
        kset = uak.setler()[0]
        self.assertEqual(uak.kalem_bul(kset, F("12.1"))[1].kod, "7a")
        self.assertEqual(uak.kalem_bul(kset, F("12.1", uak_kalem="7c"))[1].kod, "7c")
        self.assertEqual(uak.kalem_bul(kset, F("17.4"))[1].kod, "9b")
        self.assertEqual(uak.kalem_bul(kset, F("17.4", uak_kalem="9a"))[1].kod, "9a")


if __name__ == "__main__":
    unittest.main()
