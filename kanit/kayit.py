"""
Kanıt klasörlerinin okunması ve faaliyetlerle eşleştirilmesi.

Arşiv düzeni (kök klasör, örn. E:\\Kanit_Dosyalari):
    UM22_2021_<kısa başlık>\\       ← AVES'ten gelen bir yayın
        kayit.json                  ← makine için: kimlikler, AVES kodu, künye
        kunye.txt                   ← insan için özet ve kanıt kontrol listesi
        tam_metin.pdf / bildiri_sayfalari.pdf
        arsiv\\<kaynak>\\...          ← eski dosyalardan gelen kanıtlar
        atiflar\\<atıf>\\...          ← her alt klasör bir atıf
    DERS_Verilen_Dersler\\ ...        ← yayın dışı faaliyet kanıtları
    _Genel_Belgeler\\ ...             ← yardımcı klasörler ("_" ile başlar)

Eşleştirme sırası: kimlik (DOI / başlık izi / "klasor:<yol>") → AVES kodu.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from .ortak import doi_bul, kimlikler as kimlik_uret

KAYIT_DOSYASI = "kayit.json"
KUNYE_DOSYASI = "kunye.txt"
TAM_METIN_ADLARI = ("tam_metin.pdf", "bildiri_sayfalari.pdf")
YAYIN_KLASORU_RE = re.compile(r"^(UM|UL|KB|UB|NB)\d{2}_")


@dataclass
class KanitKaydi:
    """Bir faaliyetin kanıt klasörü."""
    klasor: Path
    aves_kod: str = ""
    kimlikler: list[str] = field(default_factory=list)
    kunye: str = ""
    doi: str = ""
    tur: str = ""

    @property
    def ad(self) -> str:
        return self.klasor.name

    @property
    def tam_metin(self) -> Path | None:
        for ad in TAM_METIN_ADLARI:
            if (self.klasor / ad).exists():
                return self.klasor / ad
        return None

    def dosyalar(self) -> list[Path]:
        return sorted(p for p in self.klasor.rglob("*") if p.is_file())

    def arsiv_dosyalari(self) -> list[Path]:
        a = self.klasor / "arsiv"
        return sorted(p for p in a.rglob("*") if p.is_file()) if a.exists() else []

    def atif_klasorleri(self) -> list[Path]:
        a = self.klasor / "atiflar"
        return sorted({p.parent for p in a.rglob("*") if p.is_file()}) if a.exists() else []


def kunye_oku(klasor: Path) -> dict[str, str]:
    """kunye.txt'nin ilk bölümündeki 'Anahtar : değer' satırları."""
    yol = klasor / KUNYE_DOSYASI
    if not yol.exists():
        return {}
    ilk_blok = yol.read_text(encoding="utf-8").split("\n\n")[0]
    return {k.strip(): v.strip() for k, v in re.findall(r"^([^:\n]+?)\s*: (.*)$", ilk_blok, re.M)}


def kayit_yaz(klasor: Path, aves_kod: str, kunye: str, doi: str = "", tur: str = "",
              ek_kimlikler: list[str] | None = None) -> KanitKaydi:
    kimlikler = kimlik_uret(doi, kunye, aves_kod)
    for k in ek_kimlikler or []:
        if k not in kimlikler:
            kimlikler.append(k)
    veri = {"surum": 1, "aves_kod": aves_kod, "kimlikler": kimlikler,
            "kunye": kunye, "doi": doi, "tur": tur}
    (klasor / KAYIT_DOSYASI).write_text(json.dumps(veri, ensure_ascii=False, indent=1),
                                        encoding="utf-8")
    return KanitKaydi(klasor, aves_kod, kimlikler, kunye, doi, tur)


def kayit_oku(klasor: Path) -> KanitKaydi | None:
    """kayit.json'dan; yoksa (eski klasörler) kunye.txt'den türetir."""
    yol = klasor / KAYIT_DOSYASI
    if yol.exists():
        try:
            v = json.loads(yol.read_text(encoding="utf-8"))
            return KanitKaydi(klasor, v.get("aves_kod", ""), list(v.get("kimlikler", [])),
                              v.get("kunye", ""), v.get("doi", ""), v.get("tur", ""))
        except (json.JSONDecodeError, OSError):
            pass
    alan = kunye_oku(klasor)
    if not alan:
        return None
    kunye = alan.get("Künye (AVES)", "")
    doi = alan.get("DOI", "")
    doi = doi_bul(doi) if doi not in ("", "-") else ""
    kod = alan.get("Faaliyet", "").split(" ")[0] or klasor.name[:4]
    return KanitKaydi(klasor, kod, kimlik_uret(doi, kunye, kod), kunye, doi,
                      alan.get("Tür / Endeks", "").split(" (")[0])


class KanitArsivi:
    """Kanıt kök klasörü."""

    def __init__(self, kok: Path | str):
        self.kok = Path(kok)
        self.kayitlar: list[KanitKaydi] = []
        self.diger_klasorler: list[Path] = []
        if not self.kok.is_dir():
            return
        for d in sorted(p for p in self.kok.iterdir() if p.is_dir()):
            if (k := kayit_oku(d)) is not None:
                self.kayitlar.append(k)
            else:
                self.diger_klasorler.append(d)

    @property
    def gecerli(self) -> bool:
        return self.kok.is_dir()

    def kimlik_ile(self, kimlik: str, aves_kod: str = "") -> KanitKaydi | None:
        """Kimliği taşıyan klasör; birden çoksa AVES kodu tutan tercih edilir."""
        if not kimlik:
            return None
        if kimlik.startswith("klasor:"):
            yol = self.kok / kimlik[len("klasor:"):]
            return KanitKaydi(yol, kimlikler=[kimlik]) if yol.is_dir() else None
        adaylar = [k for k in self.kayitlar if kimlik in k.kimlikler]
        return next((k for k in adaylar if k.aves_kod == aves_kod), adaylar[0] if adaylar else None)

    def bul(self, faaliyet) -> KanitKaydi | None:
        """Faaliyetin kanıt klasörü: önce kimlik, sonra AVES kodu."""
        kod = getattr(faaliyet, "aves_kod", "")
        if k := self.kimlik_ile(getattr(faaliyet, "kimlik", ""), kod):
            return k
        if kod:
            return next((k for k in self.kayitlar if k.aves_kod == kod), None)
        return None

    def klasor_kimligi(self, klasor: Path) -> str:
        """Yayın dışı bir klasörü faaliyete bağlamak için kimlik."""
        return "klasor:" + klasor.relative_to(self.kok).as_posix()

    def baglanabilir_klasorler(self) -> list[Path]:
        """Faaliyete elle bağlanabilecek klasörler (yayın dışı klasörlerin alt klasörleri dahil)."""
        sonuc = []
        for d in self.diger_klasorler:
            if d.name.startswith("_"):
                continue
            sonuc.append(d)
            sonuc.extend(sorted(p for p in d.iterdir() if p.is_dir()))
        return sonuc
