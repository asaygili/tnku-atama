"""
Kanıt kontrol listesi: bir faaliyet klasöründe yönergenin istediği belgelerin
bulunup bulunmadığı (dosya adlarından; ilgili PDF'lerin ilk sayfasından da bakılır).
"""

from __future__ import annotations

import re

from dataclasses import dataclass, field
from pathlib import Path

from .kayit import KanitKaydi
from .ortak import norm, pdf_metin

# Madde → (dosya adında aranan ifadeler, ilk sayfa metninde aranan ifadeler)
KANIT_TURLERI = {
    "tam_metin": ("Tam metin", (), ()),
    "endeks": ("Yayın tarihindeki endeks kanıtı (WoS Master Journal List / TR Dizin)",
               ("master journal", "journal search", "trdizin", "tr dizin", "dizinler", "indexing",
                "dizin", "indeks", "kanit1", "kanit2", "about", "issn", "tarandigi"),
               ("master journal list", "science citation index", "emerging sources",
                "tr dizin")),
    "q": ("Yayın yılındaki JCR kuartil (Q) kanıtı",
          ("jcr", "kanit3", "kanit4", "quartile", "ceyreklik", "cilt1"),
          ("journal citation reports", "jif quartile")),
    "program": ("Kongre programı (sunumun yapıldığını gösterir)",
                ("program", "oturum"), ("programme", "bilimsel program", "oturum")),
    "katilim": ("Katılım belgesi (en az bir yazarın katıldığını gösterir)",
                ("katilim", "certificate", "sertifika", "participation"),
                ("katilim belgesi", "certificate of participation")),
    "kapak": ("Bildiri kitabı kapak/künye sayfası",
              ("bildiri kitabi kapak", "ilksayfa", "ilk sayfa", "kapak", "ilk5sayfa"), ()),
    "isbn": ("Kitabın ISBN'li künye sayfası", ("isbn", "kunye sayfasi"), ("isbn",)),
}

# AVES öneki / EK-2 grubu → gerekli kanıtlar (Md. 7(3)-(7))
GEREKLI = {
    "UM": ["tam_metin", "endeks", "q"], "UL": ["tam_metin", "endeks"],
    "UB": ["tam_metin", "program", "katilim", "kapak"],
    "NB": ["tam_metin", "program", "katilim", "kapak"],
    "KB": ["tam_metin", "isbn"],
}


def _q_gerekli(tur: str) -> bool:
    return re.search(r"(?<![A-Z])(SCI|SSCI|AHCI)", (tur or "").upper()) is not None


@dataclass
class KanitDurumu:
    kayit: KanitKaydi
    bulunan: dict[str, list[str]] = field(default_factory=dict)   # tür → dosya adları
    eksik: list[str] = field(default_factory=list)                # tür anahtarları

    @property
    def tamam(self) -> bool:
        return not self.eksik

    def eksik_aciklamalari(self) -> list[str]:
        return [KANIT_TURLERI[e][0] for e in self.eksik]


def kanit_bul(tur: str, dosyalar: list[Path]) -> list[str]:
    _, ad_ifadeleri, metin_ifadeleri = KANIT_TURLERI[tur]
    bulunan = []
    for p in dosyalar:
        n = norm(p.name)
        if "citations of" in n:                 # WoS atıf ekranı endeks kanıtı değildir
            continue
        if any(norm(i) in n for i in ad_ifadeleri):
            bulunan.append(p.name)
        elif metin_ifadeleri and p.suffix.lower() == ".pdf" and p.stat().st_size < 5_000_000:
            m = norm(pdf_metin(p, 1)[:3000])
            if any(norm(i) in m for i in metin_ifadeleri):
                bulunan.append(p.name)
    return sorted(set(bulunan))


def durum(kayit: KanitKaydi, onek: str | None = None) -> KanitDurumu:
    """Klasördeki kanıtların, faaliyet türünün gerektirdikleriyle karşılaştırması.
    Atıf kanıtları (atiflar\\) bu listeye dahil değildir."""
    onek = onek or kayit.aves_kod[:2]
    gerekli = list(GEREKLI.get(onek, ["tam_metin"]))
    if onek == "UM" and not _q_gerekli(kayit.tur):
        gerekli.remove("q")
    dosyalar = [p for p in kayit.dosyalar() if "atiflar" not in p.relative_to(kayit.klasor).parts]
    d = KanitDurumu(kayit)
    for g in gerekli:
        if g == "tam_metin":
            bulunan = [kayit.tam_metin.name] if kayit.tam_metin else []
        else:
            bulunan = kanit_bul(g, dosyalar)
        if bulunan:
            d.bulunan[g] = bulunan
        else:
            d.eksik.append(g)
    return d
