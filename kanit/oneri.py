"""
Yayın dışı klasörlerden faaliyet önerileri.

Ders: DERS_* klasörlerindeki dosya adlarından ve PDF metinlerinden dönemler
("2021-2022_GUZ.pdf", "2021-2022 Bahar Dönemi") çıkarılır:
  • EK-2 17.4 → son üç yılda verilen dönem sayısı (değerlendirme tarihine göre)
  • Md. 11(7) → doçentlik unvanından sonra verilen farklı yarıyıl sayısı
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from .kayit import KanitArsivi
from .ortak import norm, pdf_metin

DONEM_RE = re.compile(r"((?:19|20)\d{2})\s*[-–/_ ]\s*((?:19|20)\d{2})\s*[-–/_ ]*\s*"
                      r"(guz|güz|bahar|yaz)", re.I)
# Öneki → önerilecek EK-2 kodları (arayüzde seçim listesi)
KLASOR_KODLARI = {
    "DERS": ["17.4", "17.1", "17.2", "17.3"],
    "HAKEM": ["6.3", "6.4", "6.5", "6.6", "6.8", "6.9", "6.1", "6.2", "6.7", "6.10", "6.11", "6.12"],
    "PROJE": ["12.5", "12.6", "12.11", "12.12", "12.3", "12.4", "12.13", "12.14", "12.1", "12.2"],
    "IDARI": ["18.3", "18.4", "18.5", "18.10", "18.9", "18.2", "18.1", "18.6", "18.7", "18.8"],
    "TEZ": ["5.1", "5.2", "5.5"],
}


@dataclass(frozen=True, order=True)
class Donem:
    baslangic_yili: int
    tur: str            # "Güz" / "Bahar" / "Yaz"

    @property
    def ad(self) -> str:
        return f"{self.baslangic_yili}-{self.baslangic_yili + 1} {self.tur}"

    @property
    def baslangic(self) -> date:
        return {"Güz": date(self.baslangic_yili, 9, 1),
                "Bahar": date(self.baslangic_yili + 1, 2, 1),
                "Yaz": date(self.baslangic_yili + 1, 7, 1)}[self.tur]

    @property
    def bitis(self) -> date:
        return {"Güz": date(self.baslangic_yili + 1, 1, 31),
                "Bahar": date(self.baslangic_yili + 1, 6, 30),
                "Yaz": date(self.baslangic_yili + 1, 8, 31)}[self.tur]


def _donemler(metin: str) -> set[Donem]:
    sonuc = set()
    for y1, y2, tur in DONEM_RE.findall(metin or ""):
        if int(y2) == int(y1) + 1:
            t = norm(tur)
            sonuc.add(Donem(int(y1), "Güz" if t == "guz" else ("Bahar" if t == "bahar" else "Yaz")))
    return sonuc


def ders_donemleri(arsiv: KanitArsivi) -> dict[Donem, list[Path]]:
    """Ders klasörlerinden bulunan dönemler → kanıt dosyaları."""
    sonuc: dict[Donem, list[Path]] = {}
    for d in arsiv.diger_klasorler:
        if not d.name.upper().startswith("DERS"):
            continue
        for p in d.rglob("*"):
            if not p.is_file():
                continue
            bulunan = _donemler(p.stem.replace("_", " "))
            if not bulunan and p.suffix.lower() == ".pdf":
                bulunan = _donemler(pdf_metin(p, 1)[:3000])
            for dn in bulunan:
                sonuc.setdefault(dn, []).append(p)
    return dict(sorted(sonuc.items()))


@dataclass
class DersOnerisi:
    donemler: list[Donem]
    son_uc_yil: list[Donem]          # EK-2 17.4
    unvan_sonrasi: list[Donem]       # Md. 11(7)


def ders_onerisi(arsiv: KanitArsivi, degerlendirme: date | None = None,
                 unvan_tarihi: date | None = None) -> DersOnerisi:
    degerlendirme = degerlendirme or date.today()
    uc_yil_once = date(degerlendirme.year - 3, degerlendirme.month, min(degerlendirme.day, 28))
    donemler = [d for d in ders_donemleri(arsiv) if d.tur != "Yaz"]
    return DersOnerisi(
        donemler,
        [d for d in donemler if d.bitis >= uc_yil_once and d.baslangic <= degerlendirme],
        [d for d in donemler if unvan_tarihi and d.baslangic >= unvan_tarihi],
    )
