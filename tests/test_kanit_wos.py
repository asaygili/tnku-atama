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
from test_kanit import KUNYE_A, pdf_yaz  # noqa: E402

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


if __name__ == "__main__":
    unittest.main()
