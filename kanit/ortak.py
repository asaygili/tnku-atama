"""Kanıt arşivi modüllerinin ortak yardımcıları."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

import aves_yardimci as ay

DOI_RE = re.compile(r"\b(10\.\d{4,9}/[^\s\"<>]+)", re.I)


def norm(t: str) -> str:
    """Küçük harf, Türkçe karakterler sadeleştirilmiş, yalnızca harf/rakam ve tek boşluk."""
    t = (t or "").replace("ı", "i").replace("İ", "i").lower()
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    return " ".join(re.sub(r"[^a-z0-9]+", " ", t).split())


def slug(t: str, n: int = 55) -> str:
    """Dosya/klasör adına uygun ASCII kısa ad."""
    t = unicodedata.normalize("NFKD", (t or "").replace("ı", "i").replace("İ", "I"))
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"[^A-Za-z0-9]+", "-", t).strip("-")[:n].rstrip("-")


def md5(yol: Path) -> str:
    h = hashlib.md5()
    with open(yol, "rb") as f:
        for parca in iter(lambda: f.read(1 << 20), b""):
            h.update(parca)
    return h.hexdigest()


def doi_bul(metin: str) -> str:
    m = DOI_RE.search(metin or "")
    return m.group(1).rstrip(".,;)").lower() if m else ""


def yil_bul(metin: str) -> str:
    yillar = re.findall(r"\b((?:19|20)\d{2})\b", metin or "")
    return yillar[-1] if yillar else ""


# AVES öneki → eser türü (aynı başlık ve yılla hem dergide hem kongrede yayımlanmış
# eserler farklı kimlik alsın; tür, AVES numaraları kaysa da değişmez)
ESER_TURU = {"UM": "makale", "UL": "makale", "KB": "kitap", "UB": "bildiri", "NB": "bildiri"}


def baslik_kimligi(kunye: str, aves_kod: str = "") -> str:
    """Tür + başlık + yıl izinden kimlik (DOI yoksa; yazar adı değişse de aynı kalır)."""
    iz = f"{ESER_TURU.get(aves_kod[:2], '')}|{norm(ay.baslik_cikar(kunye))}|{yil_bul(kunye)}"
    return "baslik:" + hashlib.sha1(iz.encode()).hexdigest()[:12]


def kimlikler(doi: str = "", kunye: str = "", aves_kod: str = "") -> list[str]:
    """Bir eserin tüm kimlikleri: DOI (varsa) ve başlık izi."""
    sonuc = []
    if doi := (doi or "").strip().lower().rstrip("."):
        if doi not in ("-", ""):
            sonuc.append("doi:" + doi)
    if kunye:
        sonuc.append(baslik_kimligi(kunye, aves_kod))
    return sonuc


def birincil_kimlik(doi: str = "", kunye: str = "", aves_kod: str = "") -> str:
    k = kimlikler(doi, kunye, aves_kod)
    return k[0] if k else ""


@lru_cache(maxsize=4096)
def _pdf_metin(yol: str, mtime: float, bastan: int, tumu: bool) -> str:
    import fitz
    try:
        doc = fitz.open(yol)
        sayfalar = range(doc.page_count) if tumu else range(min(bastan, doc.page_count))
        return " ".join(doc[i].get_text() for i in sayfalar)
    except Exception:
        return ""


def pdf_metin(yol: Path, bastan: int = 2, tumu: bool = False) -> str:
    """PDF'in ilk sayfalarının (ya da tamamının) metni; önbellekli."""
    if Path(yol).suffix.lower() != ".pdf":
        return ""
    try:
        mtime = Path(yol).stat().st_mtime
    except OSError:
        return ""
    return _pdf_metin(str(yol), mtime, bastan, tumu)
