"""ÜAK doçentlik kriterleri (Md. 11(2)) testleri."""

import os
import sys
import unittest
from dataclasses import replace
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import tnku_atama as t        # noqa: E402
import uak_kriterleri as uak  # noqa: E402

F = t.Faaliyet
SET = "2022-mart/muhendislik"
MUH = uak.getir(SET)


def yeterli_faaliyetler() -> list:
    """Mart 2022 Mühendislik koşullarını sağlayan doçentlik sonrası set (106 puan)."""
    return [
        F("1.1", adet=4),                                  # 1a: 80 (tek yazar)
        F("1.6"),                                          # 1c: 8
        F("5.1", adet=3),                                  # 5a: 9
        F("3.2", adet=2, toplam_yazar=2),                  # 8a: 3 × 0.5 × 2 = 3
        F("3.6", adet=2),                                  # 8b: 4 → bölüm 7
    ]                                                      # 9: 2 yıl eğitim → 2


def degerlendir(faaliyetler, **kw):
    kw.setdefault("egitim_yari_yil", 4)
    return uak.degerlendir(MUH, faaliyetler, **kw)


def kontrol(sonuc, parca):
    eslesen = [k for k in sonuc["kontroller"] if parca in k["kriter"]]
    assert len(eslesen) == 1, [k["kriter"] for k in sonuc["kontroller"]]
    return eslesen[0]["saglandi"]


def bolum(sonuc, no):
    return next(b for b in sonuc["bolumler"] if b["no"] == no)


class KayitDefteri(unittest.TestCase):
    def test_set_kayitli(self):
        self.assertIn(SET, [s.kimlik for s in uak.setler()])
        self.assertEqual((MUH.toplam_min, MUH.doktora_sonrasi_min), (100, 90))

    def test_bilinmeyen_set(self):
        with self.assertRaises(KeyError):
            uak.getir("1999-mart/yok")

    def test_ayni_set_iki_kez_kaydedilemez(self):
        with self.assertRaises(ValueError):
            uak.kaydet(MUH)


class YazarPayi(unittest.TestCase):
    def test_makale_paylari(self):
        beklenen = {(1, None): 1, (2, True): 0.8, (2, False): 0.5, (2, None): 0.5,
                    (3, True): 0.5, (3, False): 0.25, (5, False): 0.125,
                    (4, None): 0.25}
        for (n, baslica), pay in beklenen.items():
            with self.subTest(n=n, baslica=baslica):
                self.assertEqual(uak.makale_yazar_payi(n, baslica), pay)

    def test_bildiri_ve_patent_esit_bolunur(self):
        s = degerlendir([F("3.2", toplam_yazar=4, uak_baslica_yazar=True),
                         F("11.1", toplam_yazar=4)])
        self.assertEqual([r["puan"] for r in s["satirlar"]], [0.75, 5])


class Eslestirme(unittest.TestCase):
    def kalem(self, f):
        bk = uak.kalem_bul(MUH, f)
        return bk[1].kod if bk else None

    def test_eslestirme_tablosu(self):
        beklenen = [
            (F("1.1"), "1a"), (F("1.1", tezden_uretilmis=True), "2a"),
            (F("1.3"), None),                     # derleme hariç
            (F("1.4"), "1b"), (F("1.6"), "1c"), (F("1.8"), None),
            (F("1.8", tezden_uretilmis=True), "2b"),
            (F("3.2"), "8a"), (F("3.2", tezden_uretilmis=True), "2c"),
            (F("3.4"), None),                     # poster hariç
            (F("2.4"), "3b"), (F("2.9"), None),   # çeviri hariç
            (F("11.1", patent_durum="arastirma_raporu"), "4b"),
            (F("11.1", patent_durum="basvuru"), None),
            (F("12.5"), "7d"), (F("12.11"), None),  # BAP hariç
            (F("17.1"), "6a"), (F("17.4"), "9b"),
        ]
        for f, kod in beklenen:
            with self.subTest(kod=f.kod, tez=f.tezden_uretilmis):
                self.assertEqual(self.kalem(f), kod)

    def test_eslesmeyenler_raporlanir(self):
        s = degerlendir([F("1.3"), F("18.4")])
        self.assertEqual([f.kod for f in s["eslesmeyen"]], ["1.3", "18.4"])


class Kosullar(unittest.TestCase):
    def test_yeterli_set_saglar(self):
        s = degerlendir(yeterli_faaliyetler())
        self.assertEqual([k["kriter"] for k in s["kontroller"] if not k["saglandi"]], [])
        self.assertEqual(s["toplam"], 106)

    def test_1a_40_puan(self):
        f = yeterli_faaliyetler()
        f[0] = F("1.1", adet=1)                            # 1a: 20
        f.append(F("1.4", adet=10))                        # toplam için 1b
        self.assertFalse(kontrol(degerlendir(f), "1a kapsamında"))

    def test_1a_baslica_yazar_gerekli(self):
        f = yeterli_faaliyetler()
        # 2 yazarlı, aday başlıca değil: 20 × 0.5 = 10 → 8 makale = 80 puan
        f[0] = F("1.1", adet=8, toplam_yazar=2, uak_baslica_yazar=False)
        self.assertFalse(kontrol(degerlendir(f), "1a kapsamında"))
        f[0] = replace(f[0], uak_baslica_yazar=True)
        self.assertTrue(kontrol(degerlendir(f), "1a kapsamında"))

    def test_1c_8_puan(self):
        f = [x for x in yeterli_faaliyetler() if x.kod != "1.6"] + [F("1.4", adet=2)]
        self.assertFalse(kontrol(degerlendir(f), "1c kapsamında"))

    def test_tez_yayini_sarti_profesorlukte_aranmaz(self):
        s = degerlendir(yeterli_faaliyetler(), profesorluk=True)
        self.assertTrue(kontrol(s, "en az 1 yayın"))
        s = degerlendir(yeterli_faaliyetler(), profesorluk=False)
        self.assertFalse(kontrol(s, "en az 1 yayın"))

    def test_bolum_tavanlari(self):
        s = degerlendir([F("5.1", adet=30), F("1.1", adet=3, tezden_uretilmis=True),
                         F("17.1", adet=5)])
        self.assertEqual((bolum(s, 5)["ham"], bolum(s, 5)["puan"]), (90, 20))
        self.assertEqual(bolum(s, 2)["puan"], 10)
        self.assertEqual(bolum(s, 6)["puan"], 10)

    def test_atif_ve_toplanti_asgarileri(self):
        f = [x for x in yeterli_faaliyetler() if x.kod not in ("5.1", "3.6")]
        s = degerlendir(f)
        self.assertFalse(kontrol(s, "5. Atıflar"))
        self.assertFalse(kontrol(s, "8. Bilimsel Toplantı"))

    def test_iki_yil_egitim_kurali(self):
        self.assertEqual(bolum(degerlendir([], egitim_yari_yil=4), 9)["puan"], 2)
        self.assertEqual(bolum(degerlendir([], egitim_yari_yil=3), 9)["puan"], 0)
        s = degerlendir([F("17.4", adet=5)], egitim_yari_yil=0)
        self.assertEqual(bolum(s, 9)["puan"], 4)             # tavan 4

    def test_ikinci_danisman_yari_puan(self):
        s = degerlendir([F("17.1", ikinci_danisман=True)])
        self.assertEqual(s["satirlar"][0]["puan"], 2)

    def test_toplam_100(self):
        f = yeterli_faaliyetler()
        f[0] = F("1.1", adet=3)                             # −20 → 86
        self.assertFalse(kontrol(degerlendir(f), "Toplam ≥100"))


class ProfesorlukEntegrasyonu(unittest.TestCase):
    BASVURU = date(2022, 3, 15)

    def aday(self, faaliyetler, **kw):
        ozellik = dict(kadro_turu="profesor", uak_kriter_seti=SET,
                       docent_basvuru_tarihi=self.BASVURU,
                       doktora_sonrasi_ders_yari_yil=4, faaliyetler=faaliyetler)
        ozellik.update(kw)
        return t.AdayBilgi(**ozellik)

    def md112(self, aday):
        return [k for k in t.kriter_kontrol(aday)["kriterler"]
                if k["kriter"].startswith("Md. 11(2) ÜAK")]

    def test_kriterler_rapora_eklenir(self):
        sonrasi = [replace(f, docent_sonrasi=True) for f in yeterli_faaliyetler()]
        satirlar = self.md112(self.aday(sonrasi))
        self.assertTrue(satirlar)
        self.assertTrue(all("✓" in k["durum"] for k in satirlar))
        self.assertIsNotNone(t.kriter_kontrol(self.aday(sonrasi))["uak"])

    def test_basvuru_oncesi_faaliyetler_sayilmaz(self):
        once = [replace(f, yayin_tarihi=date(2021, 12, 1)) for f in yeterli_faaliyetler()]
        satirlar = self.md112(self.aday(once))
        self.assertTrue(any("✗" in k["durum"] and "Toplam" in k["kriter"]
                            for k in satirlar))

    def test_set_secilmezse_beyan_kullanilir(self):
        aday = self.aday([], uak_kriter_seti="")
        adlar = [k["kriter"] for k in t.kriter_kontrol(aday)["kriterler"]]
        self.assertTrue(any("(beyan)" in a for a in adlar))
        self.assertIsNone(t.kriter_kontrol(aday)["uak"])


if __name__ == "__main__":
    unittest.main()
