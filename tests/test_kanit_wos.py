"""WoS 'atıf yapan yayınlar' dışa aktarımından atıf klasörleri (sahte veriyle)."""

import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from kanit import KanitArsivi, atif, wos  # noqa: E402
from kanit import klasor as kk  # noqa: E402
from kanit.kayit import kayit_yaz  # noqa: E402
from test_kanit import KUNYE_A, KUNYE_B, pdf_yaz  # noqa: E402

ETIKETLER = ["PT", "AU", "AF", "TI", "SO", "SN", "EI", "PY", "DI", "WE", "CR", "UT", "DT"]
SCIE = "Science Citation Index Expanded (SCI-EXPANDED)"


def kayit(ut, au, ti, cr, we=SCIE, di="", py="2024"):
    return {"PT": "J", "AU": au, "AF": au, "TI": ti, "SO": "JOURNAL Q", "SN": "1234-5678",
            "EI": "", "PY": py, "DI": di, "WE": we, "CR": cr, "UT": ut, "DT": "Article"}


class Wos(unittest.TestCase):
    def setUp(self):
        self.kok = Path(tempfile.mkdtemp(prefix="kanit_wos_"))
        d = self.kok / kk.klasor_adi("UM01", KUNYE_A)          # vol. 3, pp. 1-9, 2024
        d.mkdir()
        kk.kunye_yaz(d, "UM01", KUNYE_A, "10.1000/xyz")
        kayit_yaz(d, "UM01", KUNYE_A, "10.1000/xyz", tur="SCI-E")
        # Arşivde zaten bulunan bir atıf (ilk sayfasında DOI'si yazıyor)
        pdf_yaz(d / "atiflar" / "Tesvik_eski" / "eski.pdf",
                ["Old citing paper doi:10.5555/eski", "b", "c"])
        self.um01 = d
        ref = "Yilmaz A, 2024, J X, V3, P1, DOI 10.1000/xyz"
        satirlar = [
            kayit("WOS:1", "Brown, B; Green, C", "A new citing study of retinal images", ref, di="10.9/a"),
            kayit("WOS:2", "Kim, D", "Second citing study without doi reference",
                  "Yilmaz A, 2024, JOURNAL X, V3, P1; Other X, 2020, Y, V1, P2", di="10.9/b"),
            kayit("WOS:3", "Yilmaz, A; Brown, B", "Self citation paper", ref, di="10.9/c"),
            kayit("WOS:4", "Lee, E", "Esci indexed citing paper", ref,
                  we="Emerging Sources Citation Index (ESCI)", di="10.9/d"),
            kayit("WOS:5", "Poe, F", "Unrelated paper", "Other X, 2020, Y, V1, P2", di="10.9/e"),
            kayit("WOS:6", "Old, G", "Old citing paper", ref, di="10.5555/eski"),
            kayit("WOS:1", "Brown, B; Green, C", "A new citing study of retinal images", ref,
                  di="10.9/a"),                                         # aynı kayıt iki kez
        ]
        self.dosya = self.kok / "savedrecs.txt"
        metin = "\t".join(ETIKETLER) + "\n" + "\n".join(
            "\t".join(s[e] for e in ETIKETLER) for s in satirlar)
        self.dosya.write_text(metin, encoding="utf-8-sig")

    def tearDown(self):
        shutil.rmtree(self.kok, ignore_errors=True)

    def test_plan(self):
        kayitlar = wos.oku(self.dosya)
        self.assertEqual(len(kayitlar), 7)
        self.assertEqual(kayitlar[0].endeks_kodu, "5.1")
        self.assertEqual(kayitlar[3].endeks_kodu, "5.2")
        plan = wos.plan_olustur(KanitArsivi(self.kok), kayitlar, "Yılmaz")
        durum = {p.wos.ut: p.durum for p in plan}
        self.assertEqual(durum, {"WOS:1": "yeni", "WOS:2": "yeni", "WOS:3": "öz atıf",
                                 "WOS:4": "kapsam dışı", "WOS:5": "eşleşmedi",
                                 "WOS:6": "zaten var"})
        self.assertEqual(len(plan), 6)                  # tekrar eden kayıt bir kez
        esci = wos.plan_olustur(KanitArsivi(self.kok), kayitlar, "Yılmaz", ("5.1", "5.2"))
        self.assertEqual({p.wos.ut: p.durum for p in esci}["WOS:4"], "yeni")

    def test_uygula_ve_sayim(self):
        a = KanitArsivi(self.kok)
        plan = wos.plan_olustur(a, wos.oku(self.dosya), "Yılmaz")
        sayac = wos.uygula(plan, a, indir=False)
        self.assertEqual(sayac["tam metin indirilecek"], 2)
        klasorler = sorted(p.name for p in (self.um01 / "atiflar").iterdir() if p.name.startswith("WoS_"))
        self.assertEqual(len(klasorler), 2)
        self.assertTrue(all(k.endswith("(SCI-E)") for k in klasorler))
        k1 = self.um01 / "atiflar" / klasorler[0]
        self.assertEqual({p.name for p in k1.iterdir()},
                         {"kayit.json", "endeks_bilgisi.pdf", "INDIRILECEK.txt"})
        self.assertEqual(json.loads((k1 / "kayit.json").read_text(encoding="utf-8"))["kaynak"], "wos")
        self.assertTrue((self.kok / wos.INDIRILECEK_LISTESI).exists())

        # Sayım: 2 WoS atıfı (5.1) + eski atıf; tam metin olmasa da WoS kaydıyla sayılır
        at = atif.atiflari_topla(KanitArsivi(self.kok), "Yılmaz")
        wos_at = [x for x in at if x.yol.parent.name.startswith("WoS_")]
        self.assertEqual(len(wos_at), 2)
        self.assertTrue(all(x.endeks == "5.1" and x.yil == 2024 for x in wos_at))
        self.assertEqual(len(at), 3)

        # İkinci çalıştırma: artık hepsi "zaten var"
        plan2 = wos.plan_olustur(KanitArsivi(self.kok), wos.oku(self.dosya), "Yılmaz")
        self.assertEqual(sum(p.durum == "yeni" for p in plan2), 0)

        # Tam metin konunca indirme listesinden düşer
        for k in klasorler:
            pdf_yaz(self.um01 / "atiflar" / k / "makale.pdf", ["x", "y", "z"])
        self.assertIsNone(wos.indirilecek_listesi(KanitArsivi(self.kok)))
        self.assertFalse((k1 / "INDIRILECEK.txt").exists())

    def test_bkci_ve_kisaltmali_kaynak(self):
        d = self.kok / kk.klasor_adi("NB01", KUNYE_B)
        d.mkdir()
        kk.kunye_yaz(d, "NB01", KUNYE_B, "")
        kayit_yaz(d, "NB01", KUNYE_B, "", tur="bildiri")
        satirlar = [kayit("WOS:7", "Park, H", "Book chapter citing the conference paper",
                          "Yilmaz A, 2023, CONF Y; Other X, 2020, Y, V1, P2",
                          we="Book Citation Index – Science (BKCI-S)", di="10.9/f")]
        f = self.kok / "bkci.txt"
        f.write_text("\t".join(ETIKETLER) + "\n" + "\n".join(
            "\t".join(s[e] for e in ETIKETLER) for s in satirlar), encoding="utf-8-sig")
        k = wos.oku(f)[0]
        self.assertEqual((k.endeks_kodu, k.endeks_kisa), ("5.7", "BKCI"))
        a = KanitArsivi(self.kok)
        self.assertEqual([x.aves_kod for x in wos.atif_yapilan_yayinlar(k, a, "Yılmaz")], ["NB01"])
        self.assertEqual(wos.plan_olustur(a, [k], "Yılmaz")[0].durum, "kapsam dışı")
        plan = wos.plan_olustur(a, [k], "Yılmaz", ("5.1", "5.2", "5.7"))
        self.assertEqual(plan[0].durum, "yeni")
        wos.uygula(plan, a, indir=False)
        at = [x for x in atif.atiflari_topla(KanitArsivi(self.kok), "Yılmaz")
              if x.yol.parent.name.startswith("WoS_")]
        self.assertEqual([x.endeks for x in at], ["5.7"])
    def test_ay_tarihi_ve_zaman(self):
        from datetime import date
        self.assertEqual(wos.ay_tarihi("MAR 2023"), date(2023, 3, 1))
        self.assertEqual(wos.ay_tarihi("DEC 15", 2022), date(2022, 12, 1))
        self.assertEqual(wos.ay_tarihi("SPR", 2024), date(2024, 3, 1))
        self.assertIsNone(wos.ay_tarihi("", 2024))
        basvuru = date(2023, 1, 4)
        A = atif.Atif
        z = lambda **k: atif.zaman(A("UM01", Path("x.pdf"), "5.1", False, "", **k), basvuru)  # noqa: E731
        self.assertEqual(z(yil=2023), "öncesi")                          # yalnız yıl: temkinli
        self.assertEqual(z(yil=2023, ay=date(2023, 2, 1)), "sonrası")
        self.assertEqual(z(yil=2023, ay=date(2023, 1, 1)), "öncesi")     # başvuru ayı: temkinli
        self.assertEqual(z(yil=2024), "sonrası")
        self.assertEqual(atif.zaman(A("UM01", Path("x"), "5.1", False, "", 2024), None), "bilinmiyor")

    def test_kitap_bolumu_uak_5b(self):
        from datetime import date
        import tnku_atama as t
        import uak_kriterleri as uk
        at = [atif.Atif("UM01", Path("a.pdf"), "5.7", False, "", 2025, date(2025, 3, 1), True),
              atif.Atif("UM01", Path("b.pdf"), "5.7", False, "", 2025, date(2025, 3, 1), False),
              atif.Atif("UM01", Path("c.pdf"), "5.1", False, "", 2023, date(2023, 6, 1))]
        fl = atif.faaliyetler(at, date(2023, 1, 4), None, t.Faaliyet)
        self.assertEqual(sorted(f.kimlik for f in fl),
                         ["atif:5.1:sonrası", "atif:5.7:sonrası", "atif:5.7:sonrası:bolum"])
        self.assertEqual(atif.kimlik_coz("atif:5.7:sonrası:bolum"), ("5.7", "sonrası", True))
        kset = uk.setler()[0]
        kalem = {f.kimlik: uk.kalem_bul(kset, f)[1].kod for f in fl}
        self.assertEqual(kalem["atif:5.7:sonrası:bolum"], "5b")
        self.assertEqual(kalem["atif:5.7:sonrası"], "5a")

    def test_indirilenleri_yerlestir_ve_desen(self):
        from kanit import indir
        a = KanitArsivi(self.kok)
        wos.uygula(wos.plan_olustur(a, wos.oku(self.dosya), "Yılmaz"), a, indir=False)
        ind = self.kok / "_indirilen"
        pdf_yaz(ind / "makale1.pdf", ["A new citing study of retinal images", "b", "c"])
        pdf_yaz(ind / "ilgisiz.pdf", ["Başka bir yayın doi:10.1/zzz", "b", "c"])
        sayac = wos.indirilenleri_yerlestir(KanitArsivi(self.kok), ind)
        self.assertEqual((sayac["yerleştirildi"], sayac["eşleşmedi"]), (1, 1))
        yerlesen = list((self.um01 / "atiflar").glob("WoS_*/atif_yapan.pdf"))
        self.assertEqual(len(yerlesen), 1)
        self.assertFalse((yerlesen[0].parent / "INDIRILECEK.txt").exists())
        self.assertTrue((ind / "makale1.pdf").exists())                    # kopyalanır
        self.assertEqual(indir.yayinci_pdf_deseni("10.3390/app1", "https://www.mdpi.com/2076-3417/15/5/2752"),
                         ["https://www.mdpi.com/2076-3417/15/5/2752/pdf"])
        self.assertEqual(indir.yayinci_pdf_deseni("10.7717/peerj-cs.3530", "https://peerj.com/articles/cs-3530/"),
                         ["https://peerj.com/articles/cs-3530.pdf"])

    def test_kayitlari_guncelle(self):
        a = KanitArsivi(self.kok)
        plan = wos.plan_olustur(a, wos.oku(self.dosya), "Yılmaz")
        wos.uygula(plan, a, indir=False)
        kj = next((self.um01 / "atiflar").glob("WoS_*/kayit.json"))
        v = json.loads(kj.read_text(encoding="utf-8"))
        v.pop("tarih"), v.pop("kitap_bolumu")
        kj.write_text(json.dumps(v), encoding="utf-8")
        kayitlar = wos.oku(self.dosya)
        for w in kayitlar:
            w.tur = "Article; Book Chapter"
        self.assertEqual(wos.kayitlari_guncelle(KanitArsivi(self.kok), kayitlar), 2)
        self.assertTrue(json.loads(kj.read_text(encoding="utf-8"))["kitap_bolumu"])


if __name__ == "__main__":
    unittest.main()
