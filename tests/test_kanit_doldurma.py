"""Kanıt arşivi Aşama 2: tarih, atıf sayımı, ders önerisi, kanıt denetimi."""

import os
import shutil
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import tnku_atama as t  # noqa: E402
from kanit import KanitArsivi, atif, denetim, oneri, tarih  # noqa: E402
from kanit import klasor as kk  # noqa: E402
from kanit.kayit import kayit_yaz  # noqa: E402
from test_kanit import KUNYE_A, pdf_yaz  # noqa: E402


class GeciciArsiv(unittest.TestCase):
    def setUp(self):
        self.kok = Path(tempfile.mkdtemp(prefix="kanit_test2_"))

    def tearDown(self):
        shutil.rmtree(self.kok, ignore_errors=True)

    def yayin(self, kod="UM01", kunye=KUNYE_A):
        d = self.kok / kk.klasor_adi(kod, kunye)
        d.mkdir()
        kk.kunye_yaz(d, kod, kunye)
        kayit_yaz(d, kod, kunye, tur="SCI-E")
        return d


class Tarih(unittest.TestCase):
    def test_aves_ay_yil(self):
        o = tarih.aves_tarihi("X, Y, Applied Soft Computing, vol. 105, Mart, 2021.")
        self.assertEqual((o.tarih, o.kaynak), (date(2021, 3, 1), "AVES (ay)"))
        self.assertEqual(tarih.aves_tarihi("X, Y, Z, Aralık, 2019.").tarih, date(2019, 12, 1))

    def test_bildiri_gunu(self):
        o = tarih.aves_tarihi("X, Başlık, 9th Conf, 06.07.2026 - 07.07.2026.")
        self.assertEqual((o.tarih, o.kaynak), (date(2026, 7, 6), "AVES (gün)"))

    def test_yalniz_yil_ve_bos(self):
        self.assertEqual(tarih.aves_tarihi("Kitap, Yayınevi, 2023.").tarih, date(2023, 1, 1))
        self.assertIsNone(tarih.aves_tarihi("tarihsiz"))

    def test_oneri_yalniz_bos_aves_faaliyetleri(self):
        f1 = t.Faaliyet("1.1", aves_kod="UM01"); f1._kunye = "A, B, C, Mart, 2021."
        f2 = t.Faaliyet("1.1", aves_kod="UM02", yayin_tarihi=date(2020, 1, 1))
        f3 = t.Faaliyet("12.5")
        self.assertEqual([f for f, _ in tarih.oneriler([f1, f2, f3], internet=False)], [f1])


class AtifSayimi(GeciciArsiv):
    def atif(self, d, alt, dosyalar):
        for ad, metin in dosyalar.items():
            pdf_yaz(d / "atiflar" / alt / ad, metin)

    def test_endeks_oz_atif_tekrar_ve_liste(self):
        d = self.yayin()
        makale = ["Citing paper by Ahmet Brown\nabstract"] + ["body"] * 3
        self.atif(d, "A1", {"citing.pdf": makale,
                            "Web of Science Master Journal List - Search.pdf":
                                ["Web of Science Core Collection: Science Citation Index Expanded"]})
        self.atif(d, "A2 (ESCI)", {"other.pdf": ["Another citing work 2024\nx", "b", "c"]})
        self.atif(d, "A3", {"kendi.pdf": ["Self citation YILMAZ Ali 2023", "b", "c"]})
        self.atif(d, "A4", {"citing_kopya.pdf": makale})              # aynı içerik
        self.atif(d, "A5", {"FireShot Capture 1 - Citations of X - [www].pdf": ["liste"] * 4})
        self.atif(d, "A6", {"belirsiz.pdf": ["Unknown journal 2025", "b", "c"]})
        at = atif.atiflari_topla(KanitArsivi(self.kok), "Yılmaz")
        adlar = {a.yol.name: a for a in at}
        self.assertEqual(set(adlar), {"citing.pdf", "other.pdf", "kendi.pdf", "belirsiz.pdf"})
        self.assertEqual(adlar["citing.pdf"].endeks, "5.1")
        self.assertEqual(adlar["other.pdf"].endeks, "5.2")          # klasör adındaki ipucu
        self.assertTrue(adlar["kendi.pdf"].oz_atif)
        self.assertIsNone(adlar["belirsiz.pdf"].endeks)

        fl = atif.faaliyetler(at, date(2023, 1, 4), "5.4", t.Faaliyet)
        self.assertEqual(sorted((f.kod, f.adet, f.docent_sonrasi) for f in fl),
                         [("5.1", 1, False), ("5.2", 1, True), ("5.4", 1, True)])
        self.assertTrue(all(f.kimlik.startswith("atif:") for f in fl))
        # belirsizler sayılmasın
        self.assertEqual(len(atif.faaliyetler(at, date(2023, 1, 4), None, t.Faaliyet)), 2)


class DersOnerisi(GeciciArsiv):
    def test_donemler_ve_sureler(self):
        ders = self.kok / "DERS_Verilen_Dersler" / "Kaynak"
        for ad in ("2021-2022_GUZ", "2021-2022_BAHAR", "2024-2025_GUZ", "2025-2026_BAHAR"):
            pdf_yaz(ders / f"{ad}.pdf", ["ders"])
        pdf_yaz(ders / "gorev.pdf", ["2023-2024 Güz Dönemi ders görevlendirmesi"])
        a = KanitArsivi(self.kok)
        self.assertEqual([d.ad for d in oneri.ders_donemleri(a)],
                         ["2021-2022 Bahar", "2021-2022 Güz", "2023-2024 Güz",
                          "2024-2025 Güz", "2025-2026 Bahar"])
        o = oneri.ders_onerisi(a, date(2026, 9, 28), date(2023, 6, 1))
        self.assertEqual([d.ad for d in o.son_uc_yil], ["2023-2024 Güz", "2024-2025 Güz",
                                                        "2025-2026 Bahar"])
        self.assertEqual(len(o.unvan_sonrasi), 3)


class Denetim(GeciciArsiv):
    def test_uyarilar(self):
        d = self.yayin()
        pdf_yaz(d / "tam_metin.pdf", ["makale"])
        (self.kok / "PROJE_TUBITAK" / "P1").mkdir(parents=True)
        pdf_yaz(self.kok / "PROJE_TUBITAK" / "P1" / "katilim.pdf", ["x"])
        a = KanitArsivi(self.kok)
        fl = [t.Faaliyet("1.1", aves_kod="UM01", q_degeri="Q1"),
              t.Faaliyet("12.5", kimlik="klasor:PROJE_TUBITAK/P1"),
              t.Faaliyet("18.4", adet=2),
              t.Faaliyet("5.1", adet=3, kimlik="atif:5.1:sonrası")]
        u = {x.kod: x for x in denetim.denetle(fl, a)}
        self.assertTrue(any("endeks" in e for e in u["1.1"].eksikler))
        self.assertTrue(any("sonuç raporu" in e for e in u["12.5"].eksikler))
        self.assertTrue(any("bağlı değil" in e for e in u["18.4"].eksikler))
        self.assertNotIn("5.1", u)                 # atıflar atiflar\ kanıtlarından sayıldı
        self.assertEqual(denetim.denetle(fl, None), [])


if __name__ == "__main__":
    unittest.main()


class YayinDisiBaglama(GeciciArsiv):
    def test_proje_hakemlik_idari_baglanir(self):
        from kanit import bagla
        pdf_yaz(self.kok / "PROJE_BAP" / "Docentlik2023_BAP" / "sonuc.pdf",
                ["BAP Komisyonu: Goruntu Isleme ve Yapay Ogrenme Yontemleri ile Medikal Goruntulerden "
                 "Hastalik Teshisi projesinin sonuc raporu kabul edilmistir."])   # PDF yazıcısı ASCII
        pdf_yaz(self.kok / "PROJE_TUBITAK" / "Tesvik2026" / "a.pdf",
                ["TUBITAK: Medikal Goruntulerden Hastalik Teshisi yontemleri"])
        pdf_yaz(self.kok / "HAKEM_Hakemlikler" / "Atama2019" / "IEEE Access tesekkur.pdf", ["x"])
        (self.kok / "IDARI_Gorevler" / "Docentlik2023_Dekan Yardımcılığı Görevi").mkdir(parents=True)
        F = t.Faaliyet
        bap = F("12.11", aves_kod="PR01")
        bap._kunye = ("Görüntü İşleme Ve Yapay Öğrenme Yöntemleri İle Medikal Görüntülerden Hastalık "
                      "Teşhisi, Yükseköğretim Kurumları tarafından destekli, Yürütücü. 2021 - 2022.")
        eski = F("6.3", aves_kod="HK01", yayin_tarihi=date(2018, 12, 31))
        eski._kunye = "IEEE Access, 2018, Hakemlik Sayısı:2."
        yeni = F("6.3", aves_kod="HK02", yayin_tarihi=date(2025, 12, 31))
        yeni._kunye = "IEEE Access, 2025, Hakemlik Sayısı:1."        # 2019 klasörü belgeleyemez
        dekan = F("18.3", adet=5, aves_kod="IG01")
        dekan._kunye = "Dekan Yardımcısı (2019-2024)"
        a = KanitArsivi(self.kok)
        o = {x.faaliyet.aves_kod: x.klasor.name for x in bagla.oneriler(a, [bap, eski, yeni, dekan])}
        self.assertEqual(o, {"PR01": "Docentlik2023_BAP", "HK01": "Atama2019",
                             "IG01": "Docentlik2023_Dekan Yardımcılığı Görevi"})

    def test_tavan_disi_kanit_istemez(self):
        a = KanitArsivi(self.kok)
        hak = [t.Faaliyet("6.3", aves_kod=f"HK{i:02d}") for i in range(1, 8)]   # 7 × 5 = 35 > 20
        disarida = denetim.tavan_disi(hak, a)
        self.assertEqual(len(disarida), 3)
        self.assertEqual(len(denetim.denetle(hak, a)), 4)
