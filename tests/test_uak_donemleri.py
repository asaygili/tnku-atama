"""ÜAK Mühendislik kriterleri: 2016 Nisan, 2016 Aralık – 2017 Aralık, 2024 Mart – 2026 Ekim
ve Dr. Öğr. Üyesi için doçentlik başvurusu ön kontrolü."""

import os
import sys
import unittest
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import tnku_atama as t        # noqa: E402
import uak_kriterleri as uak  # noqa: E402

F = t.Faaliyet
YENI = uak.getir("2024-mart/muhendislik")


def puan(kset, *fl, **kw):
    return uak.degerlendir(kset, list(fl), **kw)


def kalem_puani(sonuc, kalem):
    return sum(s["puan"] for s in sonuc["satirlar"] if s["kalem"] == kalem)


def kontrol(sonuc, metin):
    return next(k["saglandi"] for k in sonuc["kontroller"] if metin in k["kriter"])


class Donemler2024(unittest.TestCase):
    def test_q_puani(self):
        s = puan(YENI, F("1.1", q_degeri="Q1"), F("1.1", q_degeri="Q3"), F("1.1"))
        self.assertEqual([x["puan"] for x in s["satirlar"]], [30, 15, 10])   # Q yoksa Q4

    def test_baslica_q1_q3_ve_doktora_sonrasi(self):
        dr = date(2020, 1, 1)
        oncesi = F("1.1", q_degeri="Q1", yayin_tarihi=date(2019, 1, 1))     # sayılmaz
        q4 = F("1.1", q_degeri="Q4", yayin_tarihi=date(2021, 1, 1))
        s = puan(YENI, oncesi, oncesi, q4, profesorluk=False, doktora_tarihi=dr)
        self.assertFalse(kontrol(s, "1a kapsamında doktora sonrası"))
        q2 = [F("1.1", q_degeri="Q2", yayin_tarihi=date(2022, 1, 1)) for _ in range(2)]
        s = puan(YENI, *q2, profesorluk=False, doktora_tarihi=dr)
        self.assertTrue(kontrol(s, "1a kapsamında doktora sonrası"))

    def test_kitap_alt_siniri(self):
        s = puan(YENI, F("2.2"), F("2.3"))                                 # 5 + 5, c+d ≤ 5
        self.assertEqual(next(b["puan"] for b in s["bolumler"] if b["no"] == 4), 5)

    def test_egitim_sayimi(self):
        s = puan(YENI, egitim_yari_yil=4, egitim_yil=2)
        self.assertEqual(next(b["puan"] for b in s["bolumler"] if b["no"] == 9), 4)

    def test_h_indeks_esigi(self):
        self.assertEqual(kalem_puani(puan(YENI, F("5.9", adet=7)), "13a"), 5)
        self.assertEqual(kalem_puani(puan(YENI, F("5.9", adet=4)), "13a"), 0)

    def test_devam_eden_proje_ve_patent(self):
        s = puan(YENI, F("12.5", devam_ediyor=True), F("12.5"),
                 F("11.2", patent_durum="basvuru"), F("11.2", patent_durum="tescilli"))
        self.assertEqual(kalem_puani(s, "7a1"), 15)                        # yalnızca tamamlanan
        self.assertEqual((kalem_puani(s, "10d"), kalem_puani(s, "10b")), (2, 10))

    def test_tezden_puanlar_doktora_sonrasina_girmez(self):
        s = puan(YENI, *[F("1.1", q_degeri="Q1") for _ in range(3)],
                 *[F("1.1", tezden_uretilmis=True) for _ in range(5)], profesorluk=False)
        self.assertEqual(s["toplam"], 110)                                 # 90 + 20 (tez, tavan)
        self.assertTrue(kontrol(s, "Doktora sonrası"))
        self.assertIn("90", next(k["notlar"] for k in s["kontroller"] if "Doktora sonrası" in k["kriter"]))


class EskiDonemler(unittest.TestCase):
    def test_2016_aralik_ilk_yazar_baslica(self):
        eski = uak.getir("2016-aralik/muhendislik")
        s = puan(eski, F("1.1", toplam_yazar=3, yazar_sirasi=1))
        self.assertEqual(s["satirlar"][0]["pay"], 0.5)                     # başlıca: yarısı
        s22 = puan(uak.getir("2022-mart/muhendislik"), F("1.1", toplam_yazar=3, yazar_sirasi=1))
        self.assertAlmostEqual(s22["satirlar"][0]["pay"], 1 / 3)            # 2018 sonrası: eşit

    def test_2016_nisan_kosul_sistemi(self):
        nisan = uak.getir("2016-nisan/muhendislik")
        self.assertTrue(puan(nisan, *[F("1.1") for _ in range(3)])["saglandi"])
        self.assertFalse(puan(nisan, F("1.1"), F("1.1"))["saglandi"])


class DrOnKontrol(unittest.TestCase):
    def test_on_kontrol_atama_sonucunu_etkilemez(self):
        fl = [F("1.1", q_degeri="Q1", toplam_yazar=1), F("1.6"), F("18.4", adet=10)]
        a = t.AdayBilgi(kadro_turu="dr_ilk", doktora_var=True, yabanci_dil_puani=70,
                        ornek_ders_basarili=True, faaliyetler=fl)
        once = t.kriter_kontrol(a)
        a.uak_kriter_seti = "2024-mart/muhendislik"
        sonra = t.kriter_kontrol(a)
        self.assertIsNone(once["uak_on_kontrol"])
        self.assertIsNotNone(sonra["uak_on_kontrol"])
        self.assertFalse(sonra["uak_on_kontrol"]["saglandi"])
        self.assertEqual(once["genel_sonuc"], sonra["genel_sonuc"])
        self.assertEqual(once["kriterler"], sonra["kriterler"])


if __name__ == "__main__":
    unittest.main()
