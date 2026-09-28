"""
Başvuru dosyası: USB klasörü + birleştirilmiş PDF (EYS-YNG-129 Md. 6(1): başvuru
bir fiziksel dosya ve dijital (USB) olarak teslim edilir).

Yapı:
  <çıktı>\\TNKU_<Kadro>_Basvurusu_<Ad>_<tarih>\\
      00_Puanlama_Raporu.pdf
      00_Liste.xlsx
      00_Basvuru_Dosyasi_Birlesik.pdf
      01_Genel_Belgeler\\                   seçilen genel belgeler
      10_Makaleler\\01_UM22_1.1_<ad>\\       her faaliyetin tam metni ve kanıtları
      ...
Faaliyetler EK-2 grubuna, sonra koda ve AVES koduna göre sıralanır; yalnızca puan
alanlar dahil edilir. Kanıtı olmayan faaliyetin klasörüne EKSIK.txt yazılır.
"""

from __future__ import annotations

import math
import shutil
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import tnku_atama as t

from .kayit import KanitArsivi, KanitKaydi
from .ortak import md5, slug

GRUP_ADI = {1: "Makaleler", 2: "Kitap_ve_Kitap_Bolumleri", 3: "Bildiriler", 4: "Editorluk",
            5: "Atiflar", 6: "Hakemlik", 7: "Panelist_ve_Juri", 8: "TV_Sinema_Tasarim",
            9: "Sanat_ve_Tasarim", 10: "Sportif_Etkinlikler", 11: "Patent_ve_Girisimler",
            12: "Projeler", 13: "Calistay_Kongre", 14: "Oduller", 15: "Kazi_Calismalari",
            16: "Yurt_Disi_Deneyimi", 17: "Egitim_Ogretim", 18: "Idari_Gorevler", 19: "Diger"}
GOSTERIM = {1: "Makaleler", 2: "Kitap ve Kitap Bölümleri", 3: "Bildiriler", 4: "Editörlük",
            5: "Atıflar", 6: "Hakemlik", 7: "Panelist ve Jüri Üyeliği", 8: "TV-Sinema-Tasarım",
            9: "Sanat ve Tasarım", 10: "Sportif Etkinlikler", 11: "Patentler ve Girişimler",
            12: "Projeler", 13: "Çalıştay, Kongre, Sempozyum", 14: "Ödüller",
            15: "Kazı Çalışmaları", 16: "Yurt Dışı Deneyimi ve Burslar",
            17: "Eğitim-Öğretim Faaliyetleri", 18: "İdari Görevler", 19: "Diğer Faaliyetler"}
PDF_GOMULEBILIR = {".pdf"}
RESIM = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tif", ".tiff"}
ATLANAN_ADLAR = {"kunye.txt", "kayit.json", "Kaynak.url", "desktop.ini", "Thumbs.db"}
KADRO_ADI = {"dr_ilk": "Dr_Ogr_Uyesi", "dr_yeniden": "Dr_Ogr_Uyesi_Yeniden",
             "docent": "Docentlik", "profesor": "Profesorluk"}


@dataclass
class PaketAyarlari:
    atif_kanitlari: bool = True          # atıf yapan yayınları ve endeks kanıtlarını ekle
    docent_oncesi: bool = True           # doçentlik başvurusu öncesi faaliyetleri de ekle
    tam_bildiri_kitabi: bool = False     # bildiri kitaplarının tamamı (yoksa kesilmiş sayfalar)
    # birleşik PDF'te tam metin dışındaki görüntü ağırlıklı belgeleri 110 dpi JPEG'e çevir
    # (USB klasöründeki dosyalar özgün kalır)
    hafiflet: bool = True
    pdf_dosya_siniri_mb: float = 15.0  # birleşik PDF'e alınacak en büyük dosya
    genel_belgeler: list[Path] = field(default_factory=list)


@dataclass
class PaketKalemi:
    sira: int
    faaliyet: object
    grup: int
    puan: float
    klasor_adi: str
    dosyalar: list[Path] = field(default_factory=list)
    eksikler: list[str] = field(default_factory=list)
    kayit: KanitKaydi | None = None
    baslik: str = ""
    ozet_sayfalar: dict = field(default_factory=dict)   # Path → birleşik PDF'e girecek sayfalar
    yanlis_yer: list[str] = field(default_factory=list)  # başka yayına ait görünen dosyalar


@dataclass
class PaketSonucu:
    klasor: Path
    pdf: Path
    sayfa: int
    boyut_mb: float
    kalemler: list[PaketKalemi]
    pdf_disi: list[str] = field(default_factory=list)   # yalnızca USB'de kalanlar


# ── Kalemler ───────────────────────────────────────────────────────────────
def _kod_sirasi(kod: str):
    return [int(x) if x.isdigit() else x for x in kod.replace("a", ".1").replace("b", ".2")
            .replace("c", ".3").split(".")]


def _kanit_dosyalari(k: KanitKaydi, ayar: PaketAyarlari) -> list[Path]:
    """Bir yayın klasöründen pakete girecek dosyalar (tam metin önce)."""
    sirali, gorulen = [], set()

    def ekle(p: Path):
        if p.name in ATLANAN_ADLAR or not p.is_file():
            return
        h = md5(p)
        if h not in gorulen:
            gorulen.add(h)
            sirali.append(p)

    if k.tam_metin:
        ekle(k.tam_metin)
    for ad in ("tam_metin.pdf", "bildiri_sayfalari.pdf", "bildiri_kitabi_kapak_kunye.pdf"):
        ekle(k.klasor / ad)
    for p in sorted(k.klasor.iterdir()):
        if p.is_file():
            ekle(p)
    for p in k.arsiv_dosyalari():
        # Bildiri kitabının tamamı yerine kesilmiş sayfalar yeterlidir
        if not ayar.tam_bildiri_kitabi and k.tam_metin and p.stat().st_size > 20e6:
            continue
        ekle(p)
    return sirali


def kalemleri_hazirla(aday, arsiv: KanitArsivi, ayar: PaketAyarlari) -> list[PaketKalemi]:
    from .atif import atiflari_topla
    from .denetim import denetle

    import aves_yardimci as ay
    from .arsivden import Eslestirici

    uyarilar = {id(u.faaliyet): u.eksikler for u in denetle(aday.faaliyetler, arsiv)}
    es = Eslestirici(arsiv)
    basliklar = {k.aves_kod: ay.baslik_cikar(k.kunye) for k in arsiv.kayitlar if k.aves_kod}
    atiflar = None
    atif_yollari: set = set()
    kalemler = []
    for f in aday.faaliyetler:
        if f.kod not in t.EK2_PUANLAR:
            continue
        puan = t.faaliyet_puan_hesapla(f)[0]
        if puan <= 0:
            continue
        if not ayar.docent_oncesi and aday.kadro_turu == "profesor" and \
                not t.docent_basvuru_sonrasi_mi(f, aday):
            continue
        grup = t.EK2_PUANLAR[f.kod]["grup"]
        kalem = PaketKalemi(0, f, grup, puan, "", eksikler=list(uyarilar.get(id(f), [])))
        if f.kimlik.startswith("atif:"):
            if ayar.atif_kanitlari:
                if atiflar is None:
                    atiflar = atiflari_topla(arsiv, (aday.ad_soyad.split() or [""])[-1])
                    atif_yollari = {x.yol for x in atiflar}
                _, kod, zaman = f.kimlik.split(":", 2)
                basvuru = aday.docent_basvuru_tarihi
                bilinen = ("5.1", "5.2", "5.5")
                for a in atiflar:
                    a_zaman = ("sonrası" if a.yil > basvuru.year else "öncesi") \
                        if (basvuru and a.yil) else "bilinmiyor"
                    # endeksi belirsiz atıflar yalnızca kullanıcının onlara verdiği koda girer
                    ayni_kod = a.endeks == kod if a.endeks else kod not in bilinen
                    if not a.oz_atif and ayni_kod and a_zaman == zaman:
                        kalem.dosyalar.append(a.yol)
                        # birleşik PDF'e atıf yapan yayının yalnızca ilk sayfası ve
                        # atıf yapılan eserin geçtiği sayfalar girer (tamamı USB'de)
                        if (hk := basliklar.get(a.atif_yapilan)):
                            kalem.ozet_sayfalar[a.yol] = _atif_sayfalari(a.yol, hk)
                        # aynı klasördeki endeks/dizin kanıtları (atıf yapılan kendi
                        # yayınımızın kopyası atıf kanıtı değildir)
                        kalem.dosyalar += [p for p in a.yol.parent.iterdir()
                                           if p.is_file() and p != a.yol and p.suffix.lower() == ".pdf"
                                           and p.name not in ATLANAN_ADLAR
                                           and p not in atif_yollari        # başka bir atıf
                                           and (p.name == "endeks_bilgisi.pdf"
                                                or not es.ilk_sayfa_eslesme(p))][:4]
        else:
            k = arsiv.bul(f)
            kalem.kayit = k
            if k is not None:
                kalem.dosyalar = (_kanit_dosyalari(k, ayar) if k.aves_kod else
                                  [p for p in k.dosyalar() if p.name not in ATLANAN_ADLAR])
                if k.aves_kod:
                    # İlk sayfası açıkça başka bir yayınımıza ait dosya bu faaliyete girmez
                    yanlis = [p for p in kalem.dosyalar if p.suffix.lower() == ".pdf"
                              and p != k.tam_metin and "atiflar" not in p.parts
                              and (e := es.ilk_sayfa_eslesme(p)) and e != k.aves_kod]
                    for p in yanlis:
                        kalem.dosyalar.remove(p)
                        kalem.yanlis_yer.append(f"{p.relative_to(arsiv.kok)} "
                                                f"({es.ilk_sayfa_eslesme(p)} yayınına ait görünüyor)")
                    # Tam metin varken aynı yayının başka kopyaları (farklı indirmeler,
                    # "ilk sayfa" çıktıları) iki kez eklenmez
                    if k.tam_metin:
                        kalem.dosyalar = [p for p in kalem.dosyalar if p == k.tam_metin
                                          or p.name == "bildiri_kitabi_kapak_kunye.pdf"
                                          or p.suffix.lower() != ".pdf"
                                          or es.ilk_sayfa_eslesme(p) != k.aves_kod]
        # aynı içerik bir kalemde bir kez (ayrı kaydedilmiş sürümler dahil)
        gorulen, tekil = set(), []
        for p in kalem.dosyalar:
            if (h := _icerik_izi(p)) not in gorulen:
                gorulen.add(h)
                tekil.append(p)
        kalem.dosyalar = tekil
        kalemler.append(kalem)
    kalemler.sort(key=lambda k: (k.grup, _kod_sirasi(k.faaliyet.kod),
                                 getattr(k.faaliyet, "aves_kod", "") or "~"))
    for i, k in enumerate(kalemler, 1):
        f = k.faaliyet
        etiket = getattr(f, "aves_kod", "") or f"F{i:02d}"
        ad = t.EK2_PUANLAR[f.kod]["ad"]
        if k.kayit is not None and k.kayit.aves_kod:
            ad = k.kayit.klasor.name.split("_", 2)[-1]
            k.baslik = ay.baslik_cikar(k.kayit.kunye)
        elif f.kimlik.startswith("atif:"):
            zaman = f.kimlik.split(":")[-1]
            k.baslik = f"{f.adet} atıf (doçentlik başvurusu {zaman})"
        elif k.kayit is not None:
            k.baslik = k.kayit.klasor.name
        k.sira = i
        k.klasor_adi = f"{i:02d}_{etiket}_{f.kod}_{slug(ad, 40)}"
    return kalemler


def _goruntu_agirlikli(p: Path, doc) -> bool:
    """Sayfa başına ortalama 400 KB'tan büyük PDF (taranmış / ekran görüntüsü ağırlıklı)."""
    return p.stat().st_size / max(1, doc.page_count) > 400_000


def _raster_ekle(hedef, src, sayfalar, dpi: int = 110, kalite: int = 70) -> None:
    """Sayfaları JPEG görüntüsü olarak ekler (boyut için; metin katmanı korunmaz)."""
    for i in sayfalar:
        s = src[i]
        pix = s.get_pixmap(dpi=dpi)
        yeni = hedef.new_page(width=s.rect.width, height=s.rect.height)
        yeni.insert_image(yeni.rect, stream=pix.tobytes("jpeg", jpg_quality=kalite))


def _icerik_izi(p: Path) -> str:
    """Aynı belgenin ayrı kaydedilmiş sürümlerini tanıyan iz: PDF'te sayfa sayısı +
    ilk ve son sayfa metni; metni olmayan (taranmış) PDF'te ve diğer dosyalarda MD5."""
    import hashlib
    if p.suffix.lower() == ".pdf":
        import fitz
        from .ortak import norm
        try:
            doc = fitz.open(p)
            metin = norm(doc[0].get_text() + " " + doc[-1].get_text())[:3000]
            if len(metin) > 50:
                return "pdf:" + hashlib.sha1(f"{doc.page_count}|{metin}".encode()).hexdigest()
        except Exception:  # noqa: BLE001
            pass
    return "md5:" + md5(p)


def _atif_sayfalari(pdf: Path, baslik: str) -> list[int]:
    """Atıf yapan yayında ilk sayfa + atıf yapılan eserin başlığının geçtiği sayfalar."""
    import fitz
    from .ortak import norm
    kelime = norm(baslik).split()
    ifadeler = [" ".join(kelime[i:i + 4]) for i in range(0, max(1, len(kelime) - 3), 2)]
    sayfalar = [0]
    try:
        doc = fitz.open(pdf)
        for i in range(1, doc.page_count):
            m = norm(doc[i].get_text())
            if sum(x in m for x in ifadeler) >= max(1, len(ifadeler) // 2):
                sayfalar.append(i)
    except Exception:  # noqa: BLE001
        pass
    return sayfalar


# ── USB klasörü ────────────────────────────────────────────────────────────
def usb_klasoru(kalemler: list[PaketKalemi], hedef: Path, rapor_pdf: bytes,
                ayar: PaketAyarlari) -> None:
    hedef.mkdir(parents=True, exist_ok=True)
    (hedef / "00_Puanlama_Raporu.pdf").write_bytes(rapor_pdf)
    if ayar.genel_belgeler:
        gd = hedef / "01_Genel_Belgeler"
        gd.mkdir(exist_ok=True)
        for i, p in enumerate(ayar.genel_belgeler, 1):
            shutil.copy2(p, gd / f"{i:02d}_{p.name}")
    for k in kalemler:
        d = hedef / f"{10 + k.grup:02d}_{GRUP_ADI[k.grup]}" / k.klasor_adi
        d.mkdir(parents=True, exist_ok=True)
        for i, p in enumerate(k.dosyalar, 1):
            ad = "tam_metin.pdf" if (i == 1 and k.kayit is not None and p == k.kayit.tam_metin) \
                else p.name
            shutil.copy2(p, d / f"{i:02d}_{ad}")
        if not k.dosyalar or k.eksikler:
            (d / "EKSIK.txt").write_text(
                "Bu faaliyet için eksik görünen kanıtlar:\n"
                + "\n".join(f"- {e}" for e in (k.eksikler or ["Kanıt belgesi yok"])) + "\n",
                encoding="utf-8")
    _liste_yaz(kalemler, hedef / "00_Liste.xlsx")


def _liste_yaz(kalemler, yol: Path):
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill
    wb = Workbook()
    ws = wb.active
    ws.title = "Başvuru dosyası"
    ws.append(["#", "Grup", "AVES", "EK-2", "Faaliyet", "Adet", "Puan", "Dosya", "Eksik", "Klasör"])
    for k in kalemler:
        f = k.faaliyet
        ws.append([k.sira, GOSTERIM[k.grup], getattr(f, "aves_kod", ""), f.kod,
                   t.EK2_PUANLAR[f.kod]["ad"], f.adet, k.puan, len(k.dosyalar),
                   "; ".join(k.eksikler), k.klasor_adi])
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="2E5DA3")
    for col, w in zip("ABCDEFGHIJ", (5, 24, 7, 6, 50, 6, 7, 6, 50, 45)):
        ws.column_dimensions[col].width = w
    wb.save(yol)


# ── Birleşik PDF ───────────────────────────────────────────────────────────
def _font_yolu() -> str | None:
    import os
    adaylar = [r"C:\Windows\Fonts\arial.ttf", r"C:\Windows\Fonts\segoeui.ttf",
               "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
               "/System/Library/Fonts/Supplemental/Arial.ttf"]
    return next((p for p in adaylar if os.path.exists(p)), None)


class _Yazici:
    """Türkçe karakter destekli metin sayfaları (kapak, ayraç, içindekiler)."""

    def __init__(self, doc):
        self.doc = doc
        self.font = _font_yolu()

    def sayfa(self, satirlar: list[tuple[str, float, bool]], index: int | None = None):
        import fitz
        p = self.doc.new_page(pno=-1 if index is None else index, width=595, height=842)
        if self.font:
            p.insert_font(fontname="tr", fontfile=self.font)
        y = 60
        for metin, boyut, kalin in satirlar:
            if not metin or y > 780:
                continue
            kutu = fitz.Rect(50, y, 545, 800)
            renk = (0.1, 0.17, 0.29) if kalin else (0.15, 0.15, 0.15)
            font = "tr" if self.font else "helv"
            satir = metin.split("\n")
            # insert_textbox sığmayan metni hiç yazmaz (negatif döner): sığana kadar kısalt
            while True:
                kalan = p.insert_textbox(kutu, "\n".join(satir), fontsize=boyut,
                                         fontname=font, color=renk)
                if kalan >= 0 or len(satir) <= 1:
                    break
                satir = satir[:max(1, len(satir) * 3 // 4)]
                if satir[-1] != "…":
                    satir.append("…")
            # kalan: kutuda kullanılmayan yükseklik → bir sonraki blok bunun altına
            y = 800 - kalan + boyut * 0.6 if kalan >= 0 else 800
        return p


def birlesik_pdf(kalemler: list[PaketKalemi], aday, sonuc, rapor_pdf: bytes, hedef: Path,
                 ayar: PaketAyarlari) -> tuple[int, list[str]]:
    import fitz
    fitz.TOOLS.mupdf_display_errors(False)
    govde = fitz.open()
    yaz = _Yazici(govde)
    toc_govde, icindekiler, pdf_disi = [], [], []
    son_grup = None
    for k in kalemler:
        f = k.faaliyet
        bas = govde.page_count
        if k.grup != son_grup:
            toc_govde.append([1, GOSTERIM[k.grup], bas + 1])
            son_grup = k.grup
        kunye = getattr(f, "_kunye", "") or (k.kayit.kunye if k.kayit else "")
        dosya_satir = []
        gomulecek = []
        for p in k.dosyalar:
            mb = p.stat().st_size / 1e6
            if p in k.ozet_sayfalar:
                gomulecek.append(p)
                dosya_satir.append(f"• {p.name}  (ilk sayfa ve atıf yapılan sayfalar; "
                                   f"tamamı USB klasöründe)")
            elif p.suffix.lower() in PDF_GOMULEBILIR | RESIM and mb <= ayar.pdf_dosya_siniri_mb:
                gomulecek.append(p)
                dosya_satir.append(f"• {p.name}")
            else:
                neden = "büyük dosya" if mb > ayar.pdf_dosya_siniri_mb else p.suffix.lower()
                dosya_satir.append(f"• {p.name}  (yalnızca USB klasöründe – {neden})")
                pdf_disi.append(f"{k.klasor_adi}/{p.name}")
        yaz.sayfa([
            (f"{GOSTERIM[k.grup]}  ·  {k.sira}. faaliyet", 10, False),
            (f"{getattr(f, 'aves_kod', '') or '—'}   EK-2 {f.kod} – {t.EK2_PUANLAR[f.kod]['ad']}",
             14, True),
            (kunye or "", 10, False),
            (f"Adet: {f.adet}    Puan: {k.puan:g}"
             + ("    Doçentlik başvurusu sonrası" if t.docent_basvuru_sonrasi_mi(f, aday) else ""),
             10, False),
            ("Kanıt belgeleri:\n" + ("\n".join(dosya_satir) or "• (yok)"), 10, False),
            (("Eksik görünen kanıtlar:\n" + "\n".join(f"• {e}" for e in k.eksikler))
             if k.eksikler else "", 10, True),
            (("Başka bir yayına ait göründüğü için dahil edilmeyen dosyalar:\n"
              + "\n".join(f"• {e}" for e in k.yanlis_yer)) if k.yanlis_yer else "", 9, False),
        ])
        alt_toc = []
        for p in gomulecek:
            sayfa_no = govde.page_count + 1
            try:
                if p.suffix.lower() == ".pdf":
                    src = fitz.open(p)
                    if src.needs_pass:
                        raise ValueError("şifreli")
                    sayfalar = k.ozet_sayfalar.get(p, range(src.page_count))
                    tam_metin_mi = k.kayit is not None and p == k.kayit.tam_metin
                    if ayar.hafiflet and not tam_metin_mi and _goruntu_agirlikli(p, src):
                        _raster_ekle(govde, src, sayfalar)
                    elif p in k.ozet_sayfalar:
                        for i in sayfalar:
                            govde.insert_pdf(src, from_page=i, to_page=i)
                    else:
                        govde.insert_pdf(src)
                else:
                    img = fitz.open(p)
                    govde.insert_pdf(fitz.open("pdf", img.convert_to_pdf()))
                alt_toc.append([3, p.name[:80], sayfa_no])
            except Exception as e:  # noqa: BLE001
                pdf_disi.append(f"{k.klasor_adi}/{p.name} (açılamadı: {e})")
        baslik = f"{getattr(f, 'aves_kod', '') or '#' + str(k.sira)} · {f.kod} · " \
                 f"{(k.baslik or t.EK2_PUANLAR[f.kod]['ad'])[:70]}"
        toc_govde.append([2, baslik, bas + 1])
        toc_govde += alt_toc
        icindekiler.append((k.sira, baslik, bas))

    # Kapak + rapor + içindekiler
    rapor = fitz.open("pdf", rapor_pdf)
    satir_sayfa = 38
    n_icindekiler = max(1, math.ceil((len(icindekiler) + 2) / satir_sayfa))
    on = 1 + rapor.page_count + n_icindekiler
    son = fitz.open()
    y2 = _Yazici(son)
    kadro = {"dr_ilk": "Dr. Öğretim Üyesi (İlk Atanma)", "dr_yeniden": "Dr. Öğretim Üyesi "
             "(Yeniden Atanma)", "docent": "Doçent", "profesor": "Profesör"}.get(aday.kadro_turu, "")
    puanlar = sonuc.get("puanlar", {}) if sonuc else {}
    y2.sayfa([
        ("TEKİRDAĞ NAMIK KEMAL ÜNİVERSİTESİ", 16, True),
        ("Öğretim Üyeliği Kadrosuna Başvuru Dosyası", 13, False),
        (f"\n\n{aday.ad_soyad}", 18, True),
        (f"Kadro: {kadro}", 12, False),
        (f"Toplam puan: {puanlar.get('toplam', 0):g}   (PUAN-1: {puanlar.get('puan1', 0):g} · "
         f"PUAN-2: {puanlar.get('puan2', 0):g})", 12, False),
        (f"Faaliyet sayısı: {len(kalemler)}", 12, False),
        (f"Hazırlanma tarihi: {date.today():%d.%m.%Y}", 11, False),
        ("\nEYS-YNG-129 Öğretim Üyeliği Kadrolarına Başvuru İçin Gerekli Koşullar ve Uygulama "
         "Esasları Yönergesi kapsamında hazırlanmıştır.", 10, False),
    ])
    son.insert_pdf(rapor)
    for i in range(n_icindekiler):
        parca = icindekiler[i * satir_sayfa:(i + 1) * satir_sayfa]
        y2.sayfa([("İÇİNDEKİLER" if i == 0 else "İÇİNDEKİLER (devam)", 14, True),
                  ("\n".join(f"{s:>3}. {b[:85]}{'.' * max(2, 90 - len(b[:85]))} {g + on + 1}"
                             for s, b, g in parca), 9, False)])
    son.insert_pdf(govde)
    toc = [[1, "Kapak", 1], [1, "Puanlama raporu", 2], [1, "İçindekiler", 2 + rapor.page_count]]
    toc += [[lv, ad, s + on] for lv, ad, s in toc_govde]
    try:
        son.set_toc(toc)
    except Exception:  # noqa: BLE001 – yer imi hatası PDF'i bozmasın
        pass
    son.save(hedef, garbage=3, deflate=True)
    return son.page_count, pdf_disi


# ── Tümü ───────────────────────────────────────────────────────────────────
def paket_olustur(aday, sonuc, arsiv: KanitArsivi, cikti_kok: Path, rapor_pdf: bytes,
                  ayar: PaketAyarlari | None = None) -> PaketSonucu:
    ayar = ayar or PaketAyarlari()
    kalemler = kalemleri_hazirla(aday, arsiv, ayar)
    ad = slug(aday.ad_soyad or "Aday", 30)
    hedef = Path(cikti_kok) / f"TNKU_{KADRO_ADI.get(aday.kadro_turu, 'Kadro')}_Basvurusu_" \
                              f"{ad}_{date.today():%Y%m%d}"
    if hedef.exists():
        shutil.rmtree(hedef)
    usb_klasoru(kalemler, hedef, rapor_pdf, ayar)
    pdf = hedef / "00_Basvuru_Dosyasi_Birlesik.pdf"
    sayfa, pdf_disi = birlesik_pdf(kalemler, aday, sonuc, rapor_pdf, pdf, ayar)
    return PaketSonucu(hedef, pdf, sayfa, pdf.stat().st_size / 1e6, kalemler, pdf_disi)
