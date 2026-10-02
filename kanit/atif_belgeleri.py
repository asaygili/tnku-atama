"""
Başvuru dosyasının Atıflar bölümü: WoS ekran görüntüleri + atıf listeleri.

Her yayın klasöründeki ``wos_atif*.pdf`` (kullanıcının Web of Science'tan aldığı "atıf yapan
yayınlar" ekran görüntüsü) olduğu gibi alınır. Ekran görüntüsü resim olduğundan doçentlik
başvurusu öncesi/sonrası ayrımını göstermez; bu yüzden her yayın için programın atiflar\\
klasöründeki kayıtlardan ürettiği bir atıf listesi (atıf yapan yayın, dergi, tarih, endeks,
öncesi/sonrası) ve tüm yayınları özetleyen tek sayfalık bir tablo eklenir.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from . import atif as ka_atif
from .kayit import KanitArsivi

ENDEKS_ADI = {"5.1": "SCI/SSCI/AHCI", "5.2": "ESCI/Scopus", "5.5": "TR Dizin", "5.7": "Kitap (BKCI)"}
ZAMAN_ADI = {"sonrası": "Sonrası", "öncesi": "Öncesi", "bilinmiyor": "Bilinmiyor"}


@dataclass
class AtifBelgeleri:
    dosyalar: list[tuple[Path, str]] = field(default_factory=list)   # (kaynak, hedef adı)
    eksikler: list[str] = field(default_factory=list)
    ozet: dict = field(default_factory=dict)          # aves_kod → Counter(zaman)


def wos_goruntuleri(klasor: Path) -> list[Path]:
    """Yayın klasöründeki WoS atıf ekran görüntüleri (wos_atif.pdf, wos_atif (2).pdf …)."""
    return sorted(p for p in klasor.iterdir()
                  if p.is_file() and p.suffix.lower() == ".pdf"
                  and p.stem.lower().replace(" ", "_").startswith("wos_atif"))


def _stiller():
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    fr, fb = "Helvetica", "Helvetica-Bold"
    for ad, dosya in (("Arial_TR", r"C:\Windows\Fonts\arial.ttf"),
                      ("Arial_TR_B", r"C:\Windows\Fonts\arialbd.ttf"),
                      ("DejaVu_TR", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
                      ("DejaVu_TR_B", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")):
        if Path(dosya).exists():
            try:
                pdfmetrics.registerFont(TTFont(ad, dosya))
                fr, fb = (fr, ad) if ad.endswith("_B") else (ad, fb)
            except Exception:  # noqa: BLE001
                pass
    return {
        "fr": fr, "fb": fb, "colors": colors,
        "b": ParagraphStyle("b", fontName=fb, fontSize=13, leading=16, spaceAfter=4,
                            textColor=colors.HexColor("#16325C")),
        "a": ParagraphStyle("a", fontName=fr, fontSize=8.5, leading=11, spaceAfter=6,
                            textColor=colors.HexColor("#475569")),
        "h": ParagraphStyle("h", fontName=fr, fontSize=7.8, leading=9.6),
        "hb": ParagraphStyle("hb", fontName=fb, fontSize=7.8, leading=9.6),
    }


def _tablo_pdf(hedef: Path, baslik: str, aciklama: str, basliklar: list[str], satirlar: list[list],
               genislikler: list[float], vurgulu: set[int] = frozenset()) -> None:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    s = _stiller()
    renk = s["colors"]
    veri = [[Paragraph(f"<b>{x}</b>", s["hb"]) for x in basliklar]]
    veri += [[Paragraph(_xml(str(x)), s["hb"] if i in vurgulu else s["h"]) for x in r]
             for i, r in enumerate(satirlar, 1)]
    tablo = Table(veri, colWidths=[w * cm for w in genislikler], repeatRows=1)
    stil = [("BACKGROUND", (0, 0), (-1, 0), renk.HexColor("#1F4E8C")),
            ("TEXTCOLOR", (0, 0), (-1, 0), renk.white),
            ("GRID", (0, 0), (-1, -1), 0.3, renk.HexColor("#CBD5E1")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [renk.white, renk.HexColor("#F4F7FB")])]
    stil += [("BACKGROUND", (0, i), (-1, i), renk.HexColor("#E3ECF8")) for i in vurgulu]
    tablo.setStyle(TableStyle(stil))
    doc = SimpleDocTemplate(str(hedef), pagesize=A4, leftMargin=1.4 * cm, rightMargin=1.4 * cm,
                            topMargin=1.4 * cm, bottomMargin=1.4 * cm, title=baslik)
    doc.build([Paragraph(_xml(baslik), s["b"]), Paragraph(aciklama, s["a"]), Spacer(1, 4), tablo])


def _xml(t: str) -> str:
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def hazirla(arsiv: KanitArsivi, soyad: str, basvuru: date | None, haric: tuple[str, ...],
            gecici: Path, belirsiz_kod: str | None = None) -> AtifBelgeleri:
    """Atıflar bölümünün dosyalarını hazırlar (üretilen PDF'ler `gecici` klasörüne yazılır)."""
    import aves_yardimci as ay
    gecici.mkdir(parents=True, exist_ok=True)
    sonuc = AtifBelgeleri()
    atiflar = ka_atif.sayilan(ka_atif.atiflari_topla(arsiv, soyad), belirsiz_kod, haric)
    yayina_gore = defaultdict(list)
    for a in atiflar:
        yayina_gore[a.atif_yapilan].append(a)
    kayitlar = {k.aves_kod: k for k in arsiv.kayitlar if k.aves_kod}
    kodlar = sorted({*yayina_gore, *(k for k, v in kayitlar.items() if wos_goruntuleri(v.klasor))},
                    key=lambda k: ({"UM": 0, "UL": 1, "KB": 2, "UB": 3, "NB": 4}.get(k[:2], 9), k))
    tarih_metni = f"{basvuru:%d.%m.%Y}" if basvuru else "girilmemiş"
    ozet_satir, goruntusuz = [], []
    for kod in kodlar:
        kay = kayitlar.get(kod)
        liste = sorted(yayina_gore.get(kod, []), key=lambda a: (a.tarih() or date.max))
        sayac = Counter(ka_atif.zaman(a, basvuru) for a in liste)
        sonuc.ozet[kod] = sayac
        goruntuler = wos_goruntuleri(kay.klasor) if kay else []
        if liste and not goruntuler:
            goruntusuz.append(kod)
        for i, p in enumerate(goruntuler, 1):
            sonuc.dosyalar.append((p, f"{kod}_wos_atif" + (f"_{i}" if len(goruntuler) > 1 else "")
                                   + ".pdf"))
        baslik = ay.baslik_cikar(kay.kunye) if kay and kay.kunye else kod
        if liste:
            satirlar = []
            for i, a in enumerate(liste, 1):
                b = ka_atif.bilgi(a, arsiv.kok / "_onbellek" / "crossref.json")
                satirlar.append([i, b["baslik"], b["dergi"], b["tarih"],
                                 ENDEKS_ADI.get(a.endeks or belirsiz_kod or "", a.endeks or "?"),
                                 ZAMAN_ADI[ka_atif.zaman(a, basvuru)]])
            yol = gecici / f"{kod}_atif_listesi.pdf"
            _tablo_pdf(yol, f"{kod} – {baslik}",
                       f"Bu yayına yapılan ve puanlamaya giren {len(liste)} atıf (öz atıflar hariç"
                       + (f"; {', '.join(ENDEKS_ADI.get(h, h) for h in haric)} hariç" if haric else "")
                       + f"). Doçentlik başvuru tarihi: <b>{tarih_metni}</b>. "
                       f"Başvuru sonrası: <b>{sayac['sonrası']}</b> · öncesi: {sayac['öncesi']}"
                       + (f" · tarihi bilinmeyen: {sayac['bilinmiyor']}" if sayac["bilinmiyor"] else "")
                       + ". Tarih, atıf yapan yayının yayım tarihidir (WoS kaydından ay, diğerlerinde "
                         "yıl); başvuru yılındaki yalnızca yılı bilinen atıflar temkinli olarak "
                         "'öncesi' sayılmıştır.",
                       ["#", "Atıf yapan yayın", "Dergi", "Tarih", "Endeks", "Doçentlik başvurusu"],
                       satirlar, [0.9, 7.4, 3.6, 1.8, 2.4, 2.1])
            sonuc.dosyalar.append((yol, yol.name))
        ozet_satir.append([kod, baslik, sayac["sonrası"], sayac["öncesi"],
                           sayac["bilinmiyor"] or "", sum(sayac.values()),
                           "var" if goruntuler else "YOK"])
    if ozet_satir:
        toplam = Counter()
        for c in sonuc.ozet.values():
            toplam.update(c)
        ozet_satir.append(["", "TOPLAM", toplam["sonrası"], toplam["öncesi"],
                           toplam["bilinmiyor"] or "", sum(toplam.values()), ""])
        yol = gecici / "00_Atif_Ozeti.pdf"
        _tablo_pdf(yol, "Atıflar – özet",
                   f"Yayınlarınıza yapılan ve puanlamaya giren atıflar (öz atıflar hariç"
                   + (f"; {', '.join(ENDEKS_ADI.get(h, h) for h in haric)} hariç" if haric else "")
                   + f"). Doçentlik başvuru tarihi: <b>{tarih_metni}</b>. Her yayın için WoS ekran "
                     "görüntüsü (KOD_wos_atif.pdf) ve atıfların tek tek tarih ve öncesi/sonrası "
                     "dökümü (KOD_atif_listesi.pdf) bu klasördedir. Atıf yapan yayınların kendileri "
                     "ilgili yayın klasörünün 'atiflar' alt klasöründedir.",
                   ["Kod", "Yayın", "Sonrası", "Öncesi", "Tarihsiz", "Toplam", "WoS görüntüsü"],
                   ozet_satir, [1.2, 8.9, 1.5, 1.4, 1.6, 1.5, 2.0], vurgulu={len(ozet_satir)})
        sonuc.dosyalar.insert(0, (yol, yol.name))
    if goruntusuz:
        sonuc.eksikler.append("WoS atıf ekran görüntüsü (wos_atif.pdf) olmayan yayınlar: "
                              + ", ".join(goruntusuz) + " – atıf listeleri yine eklendi")
    return sonuc
