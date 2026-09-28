"""Kanıt arşivi (kanit paketi) testleri – geçici klasörlerde sahte verilerle."""

import json
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
from kanit import KanitArsivi, aday_dosyasi  # noqa: E402
from kanit import arsivden, bildiri, klasor as kk, kontrol  # noqa: E402
from kanit.kayit import kayit_yaz  # noqa: E402
from kanit.ortak import birincil_kimlik, kimlikler  # noqa: E402

KUNYE_A = "YILMAZ ALİ,KAYA AYŞE, Deep Learning for Retinal Image Analysis, Journal X, vol. 3, pp. 1-9, Mart, 2024."
KUNYE_B = "YILMAZ ALİ, Fuzzy Clustering of Knee MR Images in Practice, Conf Y, 01.05.2023 - 02.05.2023."


def pdf_yaz(yol: Path, sayfalar: list[str]):
    doc = fitz.open()
    for metin in sayfalar:
        sayfa = doc.new_page()
        sayfa.insert_textbox(fitz.Rect(40, 40, 560, 800), metin, fontsize=10)
    yol.parent.mkdir(parents=True, exist_ok=True)
    doc.save(yol)


class GeciciArsiv(unittest.TestCase):
    def setUp(self):
        self.kok = Path(tempfile.mkdtemp(prefix="kanit_test_"))

    def tearDown(self):
        shutil.rmtree(self.kok, ignore_errors=True)

    def yayin(self, kod, kunye, doi=""):
        d = self.kok / kk.klasor_adi(kod, kunye)
        d.mkdir()
        kk.kunye_yaz(d, kod, kunye, doi)
        kayit_yaz(d, kod, kunye, doi, tur="SCI-E" if kod.startswith("UM") else "")
        return d


class Kimlik(unittest.TestCase):
    def test_yazar_degisse_de_ayni(self):
        a = birincil_kimlik("", KUNYE_A, "UM01")
        b = birincil_kimlik("", KUNYE_A.replace("KAYA AYŞE", "DEMİR AYŞE"), "UM05")
        self.assertEqual(a, b)

    def test_tur_farkli_kimlik_farkli(self):
        # Aynı başlık ve yıl: dergi makalesi ile kongre bildirisi farklı eserdir
        self.assertNotEqual(birincil_kimlik("", KUNYE_A, "UM01"), birincil_kimlik("", KUNYE_A, "UB01"))

    def test_doi_oncelikli(self):
        k = kimlikler("10.1000/ABC.1", KUNYE_A, "UM01")
        self.assertEqual(k[0], "doi:10.1000/abc.1")
        self.assertTrue(k[1].startswith("baslik:"))


class Eslestirme(GeciciArsiv):
    def test_kimlik_ve_kod_ile_bulma(self):
        self.yayin("UM01", KUNYE_A, "10.1000/x")
        (self.kok / "DERS_Verilen_Dersler" / "2021").mkdir(parents=True)
        a = KanitArsivi(self.kok)
        self.assertEqual(len(a.kayitlar), 1)
        # DOI kimliğiyle
        self.assertIsNotNone(a.bul(t.Faaliyet("1.1", kimlik="doi:10.1000/x")))
        # Kimlik yok → AVES kodu
        self.assertIsNotNone(a.bul(t.Faaliyet("1.1", aves_kod="UM01")))
        # Yayın dışı klasöre elle bağlama
        k = a.bul(t.Faaliyet("17.4", kimlik="klasor:DERS_Verilen_Dersler/2021"))
        self.assertEqual(k.klasor.name, "2021")
        self.assertIsNone(a.bul(t.Faaliyet("1.1", aves_kod="UM09")))

    def test_eski_klasor_kunye_txtden_okunur(self):
        d = self.kok / "UM03_2024_Eski"
        d.mkdir()
        (d / "kunye.txt").write_text(f"Faaliyet     : UM03 – x\nKünye (AVES) : {KUNYE_A}\n"
                                     "DOI          : 10.1000/eski\n", encoding="utf-8")
        a = KanitArsivi(self.kok)
        self.assertEqual(a.kayitlar[0].aves_kod, "UM03")
        self.assertEqual(kk.kimlikleri_yaz(a), 1)
        self.assertTrue((d / "kayit.json").exists())


class AdayDosyasi(GeciciArsiv):
    def test_gidis_donus(self):
        f = t.Faaliyet("1.1", q_degeri="Q1", yayin_tarihi=date(2024, 3, 1), aves_kod="UM01",
                       kimlik="doi:10.1/x", baslica_eser=True)
        f._kunye = KUNYE_A
        aday = t.AdayBilgi(ad_soyad="Deneme", kadro_turu="profesor",
                           docent_basvuru_tarihi=date(2022, 3, 15), faaliyetler=[f])
        aday_dosyasi.kaydet(self.kok, aday, {"aves_url": "x.cv"})
        yuklenen, ek = aday_dosyasi.yukle(self.kok)
        g = yuklenen.faaliyetler[0]
        self.assertEqual((yuklenen.ad_soyad, yuklenen.docent_basvuru_tarihi, ek["aves_url"]),
                         ("Deneme", date(2022, 3, 15), "x.cv"))
        self.assertEqual((g.yayin_tarihi, g.kimlik, g.baslica_eser, g._kunye),
                         (date(2024, 3, 1), "doi:10.1/x", True, KUNYE_A))

    def test_yedek_ve_bilinmeyen_alan(self):
        aday_dosyasi.kaydet(self.kok, t.AdayBilgi(ad_soyad="A"))
        aday_dosyasi.kaydet(self.kok, t.AdayBilgi(ad_soyad="B"))
        self.assertTrue((self.kok / "aday.json.bak").exists())
        v = json.loads((self.kok / "aday.json").read_text(encoding="utf-8"))
        v["aday"]["gelecekte_eklenecek_alan"] = 1
        v["faaliyetler"] = [{"kod": "1.1", "bilinmeyen": 2}]
        (self.kok / "aday.json").write_text(json.dumps(v), encoding="utf-8")
        aday, _ = aday_dosyasi.yukle(self.kok)
        self.assertEqual((aday.ad_soyad, aday.faaliyetler[0].kod), ("B", "1.1"))


class Numaralama(GeciciArsiv):
    def test_yer_degisimi(self):
        self.yayin("UM01", KUNYE_A)
        self.yayin("UM02", KUNYE_B.replace("Conf Y", "Journal Z"))
        a = KanitArsivi(self.kok)
        # AVES'e yeni yayın eklendi: iki eserin sırası kaydı ve yer değiştirdi
        fa = t.Faaliyet("1.1", aves_kod="UM02", kimlik=birincil_kimlik("", KUNYE_A, "UM"))
        fb = t.Faaliyet("1.1", aves_kod="UM01",
                        kimlik=birincil_kimlik("", KUNYE_B.replace("Conf Y", "Journal Z"), "UM"))
        plan = kk.numara_plani(a, [fa, fb])
        self.assertEqual(sorted(p.yeni_kod for p in plan), ["UM01", "UM02"])
        kk.numara_uygula(a, plan)
        a2 = KanitArsivi(self.kok)
        self.assertEqual(a2.bul(fa).aves_kod, "UM02")
        self.assertTrue(a2.bul(fa).klasor.name.startswith("UM02_2024_Deep-Learning"))
        self.assertIn("UM02 –", (a2.bul(fa).klasor / "kunye.txt").read_text(encoding="utf-8"))

    def test_eksik_klasor_olusturma(self):
        a = KanitArsivi(self.kok)
        f = t.Faaliyet("1.1", aves_kod="UM07", kimlik=birincil_kimlik("10.9/z", KUNYE_A, "UM07"))
        f._kunye = KUNYE_A
        self.assertEqual(kk.eksik_klasorler(a, [f]), [f])
        k = kk.klasor_olustur(a, f)
        self.assertTrue((k.klasor / "Kaynak.url").exists())
        self.assertEqual(kk.eksik_klasorler(KanitArsivi(self.kok), [f]), [])


class Kontrol(GeciciArsiv):
    def test_bildiri_kanitlari(self):
        d = self.yayin("UB01", KUNYE_B)
        pdf_yaz(d / "bildiri_sayfalari.pdf", ["x"])
        pdf_yaz(d / "arsiv" / "k" / "Katılım Belgesi.pdf", ["x"])
        durum = kontrol.durum(KanitArsivi(self.kok).kayitlar[0])
        self.assertIn("katilim", durum.bulunan)
        self.assertEqual(sorted(durum.eksik), ["kapak", "program"])

    def test_makale_endeks_kaniti_metinden(self):
        d = self.yayin("UM01", KUNYE_A)
        pdf_yaz(d / "tam_metin.pdf", ["makale"])
        pdf_yaz(d / "arsiv" / "a" / "ekran.pdf", ["Web of Science Master Journal List  Search"])
        durum = kontrol.durum(KanitArsivi(self.kok).kayitlar[0])
        self.assertIn("endeks", durum.bulunan)
        self.assertEqual(durum.eksik, ["q"])          # SCI-E makalede JCR kanıtı da gerekir


class Arsivden(GeciciArsiv):
    def test_eslestirme_tekrar_ve_tam_metin(self):
        self.yayin("UM01", KUNYE_A)
        kaynak = self.kok.parent / (self.kok.name + "_kaynak")
        try:
            baslik = "Deep Learning for Retinal Image Analysis"
            pdf_yaz(kaynak / "Makale 1" / "makale.pdf", [baslik + "\nabstract"] + ["metin"] * 5)
            pdf_yaz(kaynak / "Makale 1" / "Katılım Belgesi.pdf", [baslik + " certificate"] * 5)
            shutil.copy(kaynak / "Makale 1" / "makale.pdf", kaynak / "kopya.pdf")
            pdf_yaz(kaynak / "Verilen Dersler" / "2021_GUZ.pdf", ["ders"])
            a = KanitArsivi(self.kok)
            plan = arsivden.plan_olustur(a, {"K": kaynak}, {})
            tam = [s for s in plan if s.ad == "tam_metin.pdf"]
            # Birebir aynı iki makale PDF'inden biri; 5 sayfalık katılım belgesi değil
            self.assertEqual(len(tam), 1)
            self.assertIn(tam[0].kaynak.name, ("makale.pdf", "kopya.pdf"))
            sayac = arsivden.uygula(a, plan, kopyala=True)
            k = KanitArsivi(self.kok).kayitlar[0]
            self.assertIsNotNone(k.tam_metin)
            # makale.pdf'in kopyası (kopya.pdf) ikinci kez eklenmedi; arsiv\'de tam metin yok
            self.assertGreaterEqual(sayac["aynısı bu klasöre eklendi"] + sayac["aynısı zaten var"], 1)
            self.assertFalse({"makale.pdf", "kopya.pdf"} & {p.name for p in k.arsiv_dosyalari()})
            self.assertTrue((self.kok / "DERS_Verilen_Dersler").exists())
            # Aynı kaynak tekrar işlenince hiçbir şey eklenmez
            sayac2 = arsivden.uygula(KanitArsivi(self.kok),
                                     arsivden.plan_olustur(KanitArsivi(self.kok), {"K": kaynak}, {}),
                                     kopyala=True)
            self.assertEqual(sayac2.get("eklenir", 0), 0)
        finally:
            shutil.rmtree(kaynak, ignore_errors=True)


class BildiriSayfalari(GeciciArsiv):
    def test_icindekiler_elenir_ve_bitis_bulunur(self):
        kitap = self.kok / "kitap.pdf"
        baslik = "Fuzzy Clustering of Knee MR Images in Practice"
        pdf_yaz(kitap, [
            "Kapak",
            f"İçindekiler\nBaşka bildiri ... 3\n{baslik} – YILMAZ ... 4",
            "Başka Bildiri\nAbstract x Keywords y",
            f"{baslik}\nAli YILMAZ\nAbstract ... Keywords ...",
            "2 devam sayfası",
            "3 kaynaklar",
            "Sonraki Bildiri Başlığı\nÖzet ... Anahtar Kelimeler ...",
        ])
        d = self.kok / "hedef"
        d.mkdir()
        sonuc = bildiri.bildiri_sayfalari(kitap, baslik, d, yazar="YILMAZ")
        self.assertIn("4–6", sonuc)
        self.assertEqual(fitz.open(d / "bildiri_sayfalari.pdf").page_count, 3)


if __name__ == "__main__":
    unittest.main()
