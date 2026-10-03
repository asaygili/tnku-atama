"""Kanıt arşivi Aşama 3: başvuru dosyası (USB klasörü + birleşik PDF)."""

import os
import shutil
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import fitz  # noqa: E402

import tnku_atama as t  # noqa: E402
from kanit import KanitArsivi, atif, paket  # noqa: E402
from kanit import klasor as kk  # noqa: E402
from kanit.kayit import kayit_yaz  # noqa: E402
from kanit.ortak import birincil_kimlik  # noqa: E402
from test_kanit import KUNYE_A, pdf_yaz  # noqa: E402

KUNYE_C = ("YILMAZ ALİ, Hybrid Transformer Models for Lesion Segmentation, Journal W, vol. 1, "
           "pp. 5-9, Mayıs, 2024.")


def rapor_pdf(sayfa=2) -> bytes:
    d = fitz.open()
    for _ in range(sayfa):
        d.new_page()
    return d.tobytes()


class Paket(unittest.TestCase):
    def setUp(self):
        self.kok = Path(tempfile.mkdtemp(prefix="kanit_paket_"))
        self.cikti = Path(tempfile.mkdtemp(prefix="kanit_cikti_"))
        # UM01: tam metin, endeks kanıtı, kopya sürüm, yanlış yerdeki UM02 makalesi
        self.um01 = self._yayin("UM01", KUNYE_A)
        self.um02 = self._yayin("UM02", KUNYE_C)
        baslik_a = "Deep Learning for Retinal Image Analysis"
        pdf_yaz(self.um01 / "tam_metin.pdf", [baslik_a + " full text"] + ["body"] * 4)
        pdf_yaz(self.um01 / "arsiv" / "k" / "Web of Science Master Journal List - Search.pdf",
                ["Master Journal List Science Citation Index Expanded"])
        pdf_yaz(self.um01 / "arsiv" / "k" / "baska_indirme.pdf", [baslik_a + " full text"] + ["body"] * 4)
        pdf_yaz(self.um01 / "arsiv" / "k" / "arabic.pdf",
                ["Hybrid Transformer Models for Lesion Segmentation", "x"])
        pdf_yaz(self.um02 / "tam_metin.pdf", ["Hybrid Transformer Models for Lesion Segmentation"] * 4)
        # UM01'e atıf: başlık 3. sayfada geçiyor
        pdf_yaz(self.um01 / "atiflar" / "A1 (SCI)" / "citing.pdf",
                ["Citing Article by Brown 2024", "method", "references: " + baslik_a, "end"])
        # Proje klasörü
        pdf_yaz(self.kok / "PROJE_TUBITAK" / "P1" / "sonuc_raporu.pdf", ["rapor"])
        self.arsiv = KanitArsivi(self.kok)

    def tearDown(self):
        shutil.rmtree(self.kok, ignore_errors=True)
        shutil.rmtree(self.cikti, ignore_errors=True)

    def _yayin(self, kod, kunye):
        d = self.kok / kk.klasor_adi(kod, kunye)
        d.mkdir()
        kk.kunye_yaz(d, kod, kunye)
        kayit_yaz(d, kod, kunye, tur="SCI-E")
        return d

    def _aday(self):
        fl = [t.Faaliyet("1.1", q_degeri="Q1", aves_kod="UM01",
                         kimlik=birincil_kimlik("", KUNYE_A, "UM01")),
              t.Faaliyet("1.1", aves_kod="UM02", kimlik=birincil_kimlik("", KUNYE_C, "UM02")),
              t.Faaliyet("12.5", kimlik="klasor:PROJE_TUBITAK/P1"),
              t.Faaliyet("18.4", adet=2)]
        fl[0]._kunye = KUNYE_A
        at = atif.atiflari_topla(self.arsiv, "Yılmaz")
        fl += atif.faaliyetler(at, date(2023, 1, 1), None, t.Faaliyet)
        return t.AdayBilgi(ad_soyad="Deneme Aday", kadro_turu="profesor",
                           docent_basvuru_tarihi=date(2023, 1, 1), faaliyetler=fl)

    def test_usb_ve_birlesik_pdf(self):
        aday = self._aday()
        ps = paket.paket_olustur(aday, t.kriter_kontrol(aday), self.arsiv, self.cikti,
                                 rapor_pdf(2), paket.PaketAyarlari())
        k = ps.klasor
        self.assertTrue((k / "00_Puanlama_Raporu.pdf").exists())
        self.assertTrue((k / "00_Liste.xlsx").exists())
        # EK-2 sırası: makaleler, atıflar, projeler, idari görevler
        self.assertEqual(sorted(p.name for p in k.iterdir() if p.is_dir()),
                         ["11_Makaleler", "15_Atiflar", "22_Projeler", "28_Idari_Gorevler"])
        um01 = next((k / "11_Makaleler").glob("*_UM01_*"))
        adlar = sorted(p.name for p in um01.iterdir())
        self.assertEqual(adlar[0], "01_tam_metin.pdf")
        self.assertIn("02_Web of Science Master Journal List - Search.pdf", adlar)
        # aynı makalenin başka indirmesi ve UM02'ye ait dosya dahil edilmedi
        self.assertFalse(any("baska_indirme" in a or "arabic" in a for a in adlar))
        kalem = next(x for x in ps.kalemler if getattr(x.faaliyet, "aves_kod", "") == "UM01")
        self.assertTrue(any("UM02" in y for y in kalem.yanlis_yer))
        # bağlı olmayan idari görev için EKSIK.txt
        idari = next((k / "28_Idari_Gorevler").iterdir())
        self.assertTrue((idari / "EKSIK.txt").exists())

        d = fitz.open(ps.pdf)
        toc = d.get_toc()
        self.assertEqual([x[1] for x in toc[:3]], ["Kapak", "Puanlama raporu", "İçindekiler"])
        self.assertEqual(toc[1][2], 2)                       # rapor kapaktan hemen sonra
        self.assertIn("Makaleler", [x[1] for x in toc if x[0] == 1])
        um01_ayrac = next(s for lv, ad, s in toc if lv == 2 and ad.startswith("UM01"))
        # metin geri okunurken boşluklar bölünmez boşluk ( ) olarak gelir
        ayrac = d[um01_ayrac - 1].get_text().replace(" ", " ").replace("­", "-")
        self.assertIn("UM01", ayrac)
        self.assertIn("Deep Learning for Retinal", ayrac)
        self.assertIn("UM02 yayınına ait", ayrac)
        # Birleşik PDF'te yayının yalnızca ilk sayfası; USB'de tam metnin tamamı
        metin = "".join(s.get_text() for s in d)
        self.assertIn("full text", metin)
        self.assertNotIn("body", metin)
        self.assertEqual(fitz.open(um01 / "01_tam_metin.pdf").page_count, 5)

    def test_tam_metin_secenegi(self):
        aday = self._aday()
        ps = paket.paket_olustur(aday, t.kriter_kontrol(aday), self.arsiv, self.cikti, rapor_pdf(1),
                                 paket.PaketAyarlari(calisma_ilk_sayfa=False))
        self.assertIn("body", "".join(s.get_text() for s in fitz.open(ps.pdf)))

    def test_atif_belgeleri(self):
        pdf_yaz(self.um01 / "wos_atif.pdf", ["WoS citing articles"])
        aday = self._aday()
        ps = paket.paket_olustur(aday, t.kriter_kontrol(aday), self.arsiv, self.cikti,
                                 rapor_pdf(1), paket.PaketAyarlari())
        atif_d = ps.klasor / "15_Atiflar"
        # Atıflar klasöründe yalnızca özet, WoS ekran görüntüsü ve atıf listesi
        self.assertEqual(sorted(p.name for p in atif_d.iterdir()),
                         ["00_Atif_Ozeti.pdf", "UM01_atif_listesi.pdf", "UM01_wos_atif.pdf"])
        liste = fitz.open(atif_d / "UM01_atif_listesi.pdf")[0].get_text().replace(" ", " ")
        self.assertIn("Sonrası", liste)                    # 2024 atıfı, başvuru 01.01.2023
        # Yayın klasöründe atiflar\ alt klasörü aynen; wos_atif yayın klasörüne girmez
        um01 = next((ps.klasor / "11_Makaleler").glob("*_UM01_*"))
        # her atıf ayrı, listedeki sırayla numaralı klasörde (kaynak klasör adı görünmez)
        self.assertEqual([p.name for p in (um01 / "atiflar").iterdir()], ["UM01_1"])
        self.assertTrue((um01 / "atiflar" / "UM01_1" / "citing.pdf").exists())
        self.assertIn("UM01_1", liste)                    # listede Klasör sütunu
        self.assertFalse(any("wos_atif" in p.name for p in um01.iterdir()))
        # Birleşik PDF'e atıf yapan yayının sayfaları girmez
        metin = "".join(s.get_text() for s in fitz.open(ps.pdf))
        self.assertNotIn("references:", metin)          # atıf yapan yayının sayfaları yok
        self.assertIn("Atıf belgeleri", metin.replace(" ", " "))

    def test_esci_haric(self):
        a = [atif.Atif("UM01", Path("a.pdf"), "5.1", False, "", 2024),
             atif.Atif("UM01", Path("b.pdf"), "5.2", False, "", 2024),
             atif.Atif("UM01", Path("c.pdf"), "5.1", True, "", 2024)]
        self.assertEqual([x.yol.name for x in atif.sayilan(a, haric=("5.2",))], ["a.pdf"])
        fl = atif.faaliyetler(a, date(2023, 1, 1), None, t.Faaliyet, haric=("5.2",))
        self.assertEqual([(f.kod, f.adet) for f in fl], [("5.1", 1)])

    def test_docent_oncesi_haric(self):
        aday = self._aday()
        aday.faaliyetler[0].yayin_tarihi = date(2020, 1, 1)
        kalemler = paket.kalemleri_hazirla(aday, self.arsiv, paket.PaketAyarlari(docent_oncesi=False))
        self.assertNotIn("UM01", [getattr(k.faaliyet, "aves_kod", "") for k in kalemler])


if __name__ == "__main__":
    unittest.main()
