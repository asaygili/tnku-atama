"""
EYS-YNG-129 kural testleri.

Çalıştırmak için (proje kök dizininde):
    python -m unittest discover -s tests -v
"""

import os
import sys
import unittest
from dataclasses import replace
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import tnku_atama as t  # noqa: E402

F = t.Faaliyet
BASVURU = date(2019, 3, 1)
UNVAN = date(2020, 6, 1)
BUGUN = date(2026, 9, 24)


def baslica_eser(**kw) -> t.Faaliyet:
    """Tek yazarlı, unvan sonrası Q1 SCI makale: 25 × 2 = 50 puan (PUAN-1)."""
    ozellik = dict(kod="1.1", q_degeri="Q1", yayin_tarihi=date(2021, 5, 1),
                   baslica_eser=True)
    ozellik.update(kw)
    return F(**ozellik)


def gecerli_profesor(**kw) -> t.AdayBilgi:
    """Tüm profesörlük kriterlerini tam sınırda sağlayan aday (toplam 550)."""
    ozellik = dict(
        alan="ALAN-1", kadro_turu="profesor",
        uak_docent=True, sifahi_sinav_basarili=True,
        yabanci_dil_puani=70,
        doktora_sonrasi_ders_yari_yil=4, docent_sonrasi_sure_yil=3,
        docent_basvuru_tarihi=BASVURU, docent_unvan_tarihi=UNVAN,
        degerlendirme_tarihi=BUGUN,
        uak_kriterleri_yeniden_saglandi=True,
        faaliyetler=[
            baslica_eser(),
            F("12.1", adet=10, docent_sonrasi=True),   # 500 puan, PUAN-2
        ],
    )
    ozellik.update(kw)
    return t.AdayBilgi(**ozellik)


def kriter(sonuc: dict, parca: str) -> dict:
    eslesen = [k for k in sonuc["kriterler"] if parca in k["kriter"]]
    if len(eslesen) != 1:
        raise AssertionError(f"'{parca}' için {len(eslesen)} kriter bulundu: "
                             f"{[k['kriter'] for k in sonuc['kriterler']]}")
    return eslesen[0]


def saglaniyor(aday: t.AdayBilgi, parca: str) -> bool:
    return "✓" in kriter(t.kriter_kontrol(aday), parca)["durum"]


class TemelAday(unittest.TestCase):
    def test_gecerli_profesor_tum_kriterleri_saglar(self):
        sonuc = t.kriter_kontrol(gecerli_profesor())
        basarisiz = [k for k in sonuc["kriterler"] if "✗" in k["durum"]]
        self.assertEqual(basarisiz, [])
        self.assertTrue(sonuc["genel_sonuc"])
        self.assertEqual(sonuc["puanlar"]["toplam"], 550)


# 1 ─ Madde 8: sorumlu / senyör yazar puanı değiştirmez ─────────────────────
class YazarCarpani(unittest.TestCase):
    def test_sorumlu_yazar_carpani_degistirmez(self):
        normal = F("1.1", toplam_yazar=6, yazar_sirasi=6, q_degeri="Q1")
        sorumlu = replace(normal, sorumlu_veya_senyör=True)
        self.assertEqual(t.faaliyet_puan_hesapla(normal)[0], 12.5)
        self.assertEqual(t.faaliyet_puan_hesapla(sorumlu)[0], 12.5)

    def test_madde8_tablosu(self):
        beklenen = {(1, 1): 1.0, (2, 2): 0.9, (3, 3): 0.7, (4, 4): 0.55,
                    (5, 5): 0.4, (6, 1): 0.75, (6, 6): 0.25, (8, 8): 0.25}
        for (toplam, sira), carpan in beklenen.items():
            with self.subTest(toplam=toplam, sira=sira):
                self.assertEqual(t.yazar_carpani_hesapla(toplam, sira), carpan)

    def test_dr_b_kurali_sorumlu_yazari_hala_tanir(self):
        aday = t.AdayBilgi(kadro_turu="dr_ilk", faaliyetler=[
            F("1.1", toplam_yazar=5, yazar_sirasi=3, q_degeri="Q2",
              sorumlu_veya_senyör=True)])
        self.assertTrue(t.puan_hesapla(aday)["puan1_b_kural_var"])


# 2 ─ EK-1 (g): doçentlik sonrası puana grup tavanları uygulanır ────────────
class DocentSonrasiPuan(unittest.TestCase):
    def test_atif_tavani_g_kuralinda_da_gecerli(self):
        # Başvuru sonrası tek faaliyet 100 atıf (ham 500) → tavan 50
        aday = gecerli_profesor(faaliyetler=[
            baslica_eser(yayin_tarihi=None, docent_sonrasi=False),
            F("12.1", adet=10),
            F("5.1", adet=100, docent_sonrasi=True),
        ], docent_unvan_tarihi=None)
        k = kriter(t.kriter_kontrol(aday), "(g)")
        self.assertIn("✗", k["durum"])
        self.assertIn("50", k["notlar"])

    def test_tarih_isaretin_yerine_gecer(self):
        # docent_sonrasi=False olsa da tarih başvurudan sonraysa sayılır
        f = F("12.1", docent_sonrasi=False, yayin_tarihi=date(2020, 1, 1))
        self.assertTrue(t.docent_basvuru_sonrasi_mi(f, gecerli_profesor()))
        # docent_sonrasi=True olsa da tarih başvurudan önceyse sayılmaz
        f = F("12.1", docent_sonrasi=True, yayin_tarihi=date(2018, 12, 31))
        self.assertFalse(t.docent_basvuru_sonrasi_mi(f, gecerli_profesor()))

    def test_tarih_yoksa_isaret_kullanilir(self):
        aday = gecerli_profesor(docent_basvuru_tarihi=None)
        self.assertTrue(t.docent_basvuru_sonrasi_mi(
            F("12.1", docent_sonrasi=True, yayin_tarihi=date(2020, 1, 1)), aday))

    def test_g_esigi_yarim_asgari_puan(self):
        aday = gecerli_profesor(faaliyetler=[
            baslica_eser(), F("12.1", adet=10),                      # 550 toplam
            F("12.2", adet=5, docent_sonrasi=True),                  # 175
        ])
        # başvuru sonrası: 50 (başlıca eser, tarihli) + 175 = 225 < 275
        self.assertFalse(saglaniyor(aday, "(g)"))

    def test_sinavsiz_basvuruda_esikler_yuzde_20_fazla(self):
        aday = gecerli_profesor(sifahi_sinav_basarili=False,
                                ornek_ders_basarili=True)
        sonuc = t.kriter_kontrol(aday)
        self.assertIn("✗", kriter(sonuc, "Toplam ≥660")["durum"])
        self.assertIn("≥330", kriter(sonuc, "(g)")["kriter"])


# 3 ─ Md. 11(5): Başlıca Araştırma Eseri ───────────────────────────────────
class BaslicaEser(unittest.TestCase):
    ANAHTAR = "Başlıca Araştırma Eseri"

    def denetle(self, faaliyetler, **kw):
        return saglaniyor(gecerli_profesor(faaliyetler=faaliyetler, **kw),
                          self.ANAHTAR)

    def test_eser_isaretlenmemis(self):
        self.assertFalse(self.denetle([baslica_eser(baslica_eser=False)]))

    def test_birden_fazla_eser(self):
        self.assertFalse(self.denetle([baslica_eser(), baslica_eser()]))

    def test_alan1_yalnizca_1_1(self):
        self.assertFalse(self.denetle([baslica_eser(kod="1.4", q_degeri=None)]))

    def test_alan2_kitap_bolumu_kabul(self):
        self.assertTrue(self.denetle([baslica_eser(kod="2.4", q_degeri=None)],
                                     alan="ALAN-2"))

    def test_alan2_bildiri_reddedilir(self):
        self.assertFalse(self.denetle([baslica_eser(kod="3.2", q_degeri=None)],
                                      alan="ALAN-2"))

    def test_ikinci_yazar_reddedilir(self):
        self.assertFalse(self.denetle([baslica_eser(toplam_yazar=3,
                                                    yazar_sirasi=2)]))

    def test_sorumlu_yazar_baslica_yazar_sayilmaz(self):
        self.assertFalse(self.denetle([baslica_eser(
            toplam_yazar=3, yazar_sirasi=3, sorumlu_veya_senyör=True)]))

    def test_ilk_yazar_kabul(self):
        self.assertTrue(self.denetle([baslica_eser(toplam_yazar=4,
                                                   yazar_sirasi=1)]))

    def test_unvandan_once_yayimlanan_reddedilir(self):
        self.assertFalse(self.denetle([baslica_eser(yayin_tarihi=UNVAN)]))

    def test_yayin_tarihi_zorunlu(self):
        self.assertFalse(self.denetle([baslica_eser(yayin_tarihi=None)]))


# 4 ─ Tarihler: 5 yıllık süre ve iki ayrı referans tarihi ──────────────────
class Tarihler(unittest.TestCase):
    ANAHTAR = "5 yıl dolmuş"

    def test_unvan_tarihi_yoksa_saglanmaz(self):
        self.assertFalse(saglaniyor(gecerli_profesor(docent_unvan_tarihi=None),
                                    self.ANAHTAR))

    def test_yil_farki_degil_tam_tarih(self):
        # Eski kod: 2026 - 2021 = 5 → geçiyordu; gerçekte 4 yıl 9 ay
        aday = gecerli_profesor(docent_unvan_tarihi=date(2021, 12, 1))
        self.assertFalse(saglaniyor(aday, self.ANAHTAR))
        aday = replace(aday, degerlendirme_tarihi=date(2026, 12, 1))
        self.assertTrue(saglaniyor(aday, self.ANAHTAR))

    def test_artik_gun(self):
        self.assertEqual(t.yil_ekle(date(2020, 2, 29), 5), date(2025, 2, 28))

    def test_g_basvuru_eser_unvan_tarihine_bakar(self):
        # Başvuru ile unvan arasında yayımlanan eser: (g)'ye sayılır,
        # ama Başlıca Araştırma Eseri olamaz.
        arada = date(2019, 10, 1)
        aday = gecerli_profesor(faaliyetler=[
            baslica_eser(yayin_tarihi=arada), F("12.1", adet=10, docent_sonrasi=True)])
        self.assertTrue(t.docent_basvuru_sonrasi_mi(aday.faaliyetler[0], aday))
        self.assertFalse(saglaniyor(aday, "Başlıca Araştırma Eseri"))


# 5 ─ Md. 11(2) beyanı ─────────────────────────────────────────────────────
class UakKriterBeyani(unittest.TestCase):
    def test_beyan_yoksa_saglanmaz(self):
        aday = gecerli_profesor(uak_kriterleri_yeniden_saglandi=False)
        self.assertFalse(saglaniyor(aday, "Md. 11(2)"))
        self.assertFalse(t.kriter_kontrol(aday)["genel_sonuc"])


# 6 ─ Yabancı dil: yabancı dil bölümlerinde ikinci dil ────────────────────
class YabanciDil(unittest.TestCase):
    def test_ikinci_dil_esik_alti(self):
        aday = gecerli_profesor(calisma_alani_yabanci_dil_bolumu=True,
                                yabanci_dil_puani=90,
                                ikinci_yabanci_dil_puani=60)
        self.assertTrue(saglaniyor(aday, "çalışma alanı dili ≥85"))
        self.assertFalse(saglaniyor(aday, "ikinci yabancı dil ≥65"))

    def test_ikinci_dil_esikte(self):
        aday = gecerli_profesor(calisma_alani_yabanci_dil_bolumu=True,
                                yabanci_dil_puani=85,
                                ikinci_yabanci_dil_puani=65)
        self.assertTrue(t.kriter_kontrol(aday)["genel_sonuc"])

    def test_dr_ikinci_dil_esigi_60(self):
        aday = t.AdayBilgi(kadro_turu="dr_ilk",
                           calisma_alani_yabanci_dil_bolumu=True,
                           yabanci_dil_puani=85, ikinci_yabanci_dil_puani=60)
        self.assertTrue(saglaniyor(aday, "ikinci yabancı dil ≥60"))

    def test_docent_ikinci_dil_esigi_65(self):
        aday = t.AdayBilgi(kadro_turu="docent",
                           calisma_alani_yabanci_dil_bolumu=True,
                           yabanci_dil_puani=85, ikinci_yabanci_dil_puani=64)
        self.assertFalse(saglaniyor(aday, "ikinci yabancı dil ≥65"))

    def test_yabanci_dil_bolumu_disinda_tek_esik(self):
        aday = gecerli_profesor(yabanci_dil_puani=64)
        self.assertFalse(saglaniyor(aday, "YÖKDİL/YDS) ≥65"))


# ─ Puan dökümü (PDF faaliyet tablosu) ────────────────────────────────────
class PuanDokumu(unittest.TestCase):
    def test_makale_dokumu(self):
        d = t.puan_dokumu(F("1.1", adet=2, toplam_yazar=5, yazar_sirasi=3,
                            q_degeri="Q2"))
        self.assertEqual(d["taban"], 25)
        self.assertEqual(d["carpanlar"], [("Q2", 1.5)])
        self.assertEqual(d["tam_puan"], 37.5)
        self.assertEqual(d["yazar_carpani"], 0.6)
        self.assertEqual(d["birim_puan"], 22.5)
        self.assertEqual(d["ham_puan"], 45)

    def test_yayin_disi_faaliyette_yazar_payi_uygulanmaz(self):
        d = t.puan_dokumu(F("12.1", toplam_yazar=4, yazar_sirasi=4))
        self.assertFalse(d["yazar_uygulanir"])
        self.assertEqual(d["ham_puan"], 50)

    def test_patent_ve_danisman_carpanlari(self):
        self.assertEqual(t.puan_dokumu(F("11.1", patent_durum="basvuru"))["carpanlar"],
                         [("Başvuru", 0.25)])
        d = t.puan_dokumu(F("17.1", ikinci_danisман=True))
        self.assertEqual((d["carpanlar"], d["tam_puan"]), ([("2. danışman", 0.5)], 6))

    def test_detaylarda_tavan_kesintisi(self):
        aday = t.AdayBilgi(kadro_turu="profesor", faaliyetler=[
            F("5.1", adet=8), F("5.2", adet=5)])      # 40 + 15 ham, tavan 50
        dt = t.puan_hesapla(aday)["detaylar"]
        self.assertEqual([(d["ham_puan"], d["puan"], d["tavan_kesinti"]) for d in dt],
                         [(40, 40, 0), (15, 10, 5)])

    def test_dokum_ile_faaliyet_puani_ayni(self):
        f = F("1.3", adet=3, toplam_yazar=7, yazar_sirasi=7, q_degeri="Q3")
        self.assertEqual(t.faaliyet_puan_hesapla(f)[0], t.puan_dokumu(f)["ham_puan"])


if __name__ == "__main__":
    unittest.main()
