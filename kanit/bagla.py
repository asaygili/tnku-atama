"""
Yayın dışı faaliyetlerin (proje, hakemlik, idari görev) kanıt klasörlerine otomatik bağlanması.

AVES'ten gelen bu faaliyetlerin DOI'si ya da yayın klasörü yoktur; kanıtları PROJE_*,
HAKEM_*, IDARI_* gibi klasörlerin alt klasörlerindedir. Eşleştirme içerikle yapılır:
  - Proje (EK-2 12): proje adının anlamlı kelimeleri klasördeki belgelerde geçiyor mu
  - Hakemlik (EK-2 6): dergi adı klasördeki dosya adlarında / belgelerde geçiyor mu
  - İdari görev (EK-2 18): görev adı (Dekan Yardımcısı, Komisyon…) klasör adında geçiyor mu
Yalnızca kanıt klasörü bağlı olmayan faaliyetler bağlanır; mevcut bağlantılar değişmez.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .kayit import KanitArsivi
from .ortak import norm, pdf_metin

ONEKLER = {"12": ("PROJE",), "6": ("HAKEM",), "18": ("IDARI", "IDARİ")}
BOS = {"ve", "ile", "icin", "the", "and", "for", "of", "in", "from", "using", "bir", "olarak",
       "projesi", "proje", "bilimsel", "arastirma", "yuksekogretim", "kurumlari", "tarafindan",
       "destekli", "yurutucu", "arastirmaci", "tubitak", "uyeligi", "uyesi"}


# Proje türü → klasör türü (BAP projesi TÜBİTAK klasörüne bağlanmasın)
PROJE_TURU = {"12.3": "TUBITAK", "12.4": "TUBITAK", "12.5": "TUBITAK", "12.6": "TUBITAK",
              "12.11": "BAP", "12.12": "BAP"}


def _klasor_yili(d: Path) -> int | None:
    """'Atama2019_…', 'Docentlik2023_…' gibi klasörlerin hazırlandığı yıl: bu klasör o yıldan
    sonraki bir faaliyeti belgeleyemez."""
    m = re.search(r"(?:19|20)\d{2}", d.name)
    return int(m.group(0)) if m else None


def _faaliyet_yili(f) -> int | None:
    if getattr(f, "yayin_tarihi", None):
        return f.yayin_tarihi.year
    yillar = re.findall(r"\b((?:19|20)\d{2})\b", getattr(f, "_kunye", "") or "")
    return int(yillar[-1]) if yillar else None


@dataclass
class BaglantiOnerisi:
    faaliyet: object
    klasor: Path
    neden: str
    skor: float


def _klasor_metni(klasor: Path) -> str:
    parcalar = [klasor.name] + [p.name for p in klasor.rglob("*") if p.is_file()]
    parcalar += [pdf_metin(p, 2)[:6000] for p in sorted(klasor.rglob("*.pdf"))[:12]]
    return " " + norm(" ".join(parcalar)) + " "


def _kelimeler(metin: str) -> list[str]:
    return [w for w in norm(metin).split() if len(w) > 3 and w not in BOS and not w.isdigit()]


def _ad(f) -> str:
    """Faaliyetin adı: künyenin ilk virgülüne kadarki kısım (proje adı, dergi adı, görev)."""
    kunye = getattr(f, "_kunye", "") or ""
    return kunye.split("(")[0].split(",")[0].strip() if kunye else ""


def oneriler(arsiv: KanitArsivi, faaliyetler) -> list[BaglantiOnerisi]:
    klasorler = [d for d in arsiv.baglanabilir_klasorler() if d.parent != arsiv.kok]
    metinler: dict[Path, str] = {}

    def metin(d: Path) -> str:
        if d not in metinler:
            metinler[d] = _klasor_metni(d)
        return metinler[d]

    sonuc = []
    for f in faaliyetler:
        grup = f.kod.split(".")[0]
        if grup not in ONEKLER or arsiv.bul(f) is not None or not (ad := _ad(f)):
            continue
        yil = _faaliyet_yili(f)
        tur = PROJE_TURU.get(f.kod, "")
        adaylar = [d for d in klasorler
                   if (ust := d.relative_to(arsiv.kok).parts[0].upper()).startswith(ONEKLER[grup])
                   and (not tur or tur in ust.replace("İ", "I"))
                   and not (grup == "6" and yil and (ky := _klasor_yili(d)) and yil > ky)]
        en, en_skor, neden = None, 0.0, ""
        for d in adaylar:
            m = metin(d)
            if grup == "6":                      # dergi adı bütün olarak geçmeli
                if len(norm(ad)) < 12 and len(norm(ad).split()) < 2:
                    continue                     # "Electronics" gibi tek kelimelik genel adlar
                skor = 1.0 if f" {norm(ad)} " in m else 0.0
                n = f"dergi adı '{ad}' klasördeki belgelerde geçiyor"
            else:
                kel = _kelimeler(ad)
                if not kel:
                    continue
                if grup == "18":                 # görev adı klasör adında
                    ka = norm(d.name)
                    skor = sum(any(w[:6] in x for x in ka.split()) for w in kel) / len(kel)
                    n = f"görev '{ad}' klasör adıyla eşleşiyor"
                else:
                    skor = sum(f" {w} " in m for w in kel) / len(kel)
                    n = f"proje adının kelimelerinin %{skor * 100:.0f}'i klasördeki belgelerde geçiyor"
            if skor > en_skor:
                en, en_skor, neden = d, skor, n
        if en is not None and en_skor >= (0.6 if grup == "12" else 0.99):
            sonuc.append(BaglantiOnerisi(f, en, neden, en_skor))
    return sonuc


def uygula(arsiv: KanitArsivi, onerilerim: list[BaglantiOnerisi]) -> int:
    for o in onerilerim:
        o.faaliyet.kimlik = arsiv.klasor_kimligi(o.klasor)
    return len(onerilerim)
