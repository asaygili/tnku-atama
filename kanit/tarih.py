"""
Yayın tarihlerinin doldurulması.

Öncelik: DOI → Crossref'in 'published' tarihi (ilk yayımlanma; çevrim içi ya da basılı
hangisi önceyse). DOI yoksa AVES künyesindeki "Mart, 2021" ya da bildiri tarihi
"06.07.2026 - 07.07.2026". Yalnızca ay/yıl biliniyorsa ayın/yılın ilk günü alınır:
doçentlik başvurusuyla aynı aydaki eser temkinli olarak "başvuru öncesi" sayılır.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

AYLAR = {"ocak": 1, "şubat": 2, "subat": 2, "mart": 3, "nisan": 4, "mayıs": 5, "mayis": 5,
         "haziran": 6, "temmuz": 7, "ağustos": 8, "agustos": 8, "eylül": 9, "eylul": 9,
         "ekim": 10, "kasım": 11, "kasim": 11, "aralık": 12, "aralik": 12}


@dataclass
class TarihOnerisi:
    tarih: date
    kaynak: str        # "Crossref", "AVES (gün)", "AVES (ay)", "AVES (yıl)"


def aves_tarihi(kunye: str) -> TarihOnerisi | None:
    if m := re.search(r"\b(\d{2})\.(\d{2})\.((?:19|20)\d{2})\b", kunye or ""):
        try:
            return TarihOnerisi(date(int(m.group(3)), int(m.group(2)), int(m.group(1))), "AVES (gün)")
        except ValueError:
            pass
    if m := re.search(r"\b([A-Za-zÇĞİÖŞÜçğıöşü]+),\s*((?:19|20)\d{2})\b", kunye or ""):
        ay = AYLAR.get(m.group(1).lower().replace("İ", "i"))
        if ay:
            return TarihOnerisi(date(int(m.group(2)), ay, 1), "AVES (ay)")
    yillar = re.findall(r"\b((?:19|20)\d{2})\b", kunye or "")
    return TarihOnerisi(date(int(yillar[-1]), 1, 1), "AVES (yıl)") if yillar else None


def crossref_tarihi(doi: str, oturum=None) -> TarihOnerisi | None:
    from .indir import oturum as yeni_oturum
    s = oturum or yeni_oturum()
    try:
        r = s.get(f"https://api.crossref.org/works/{doi}", timeout=20)
        if r.status_code != 200:
            return None
        mesaj = r.json()["message"]
    except Exception:
        return None
    # Çevrim içi, basılı ve genel yayın tarihlerinin en erkeni (temkinli: erken yayımlanan
    # eser doçentlik başvurusu "sonrası" sayılmaz). Bazı yayınevleri çevrim içi tarihi
    # bildirmez; DOI'nin oluşturulma tarihi ('created') çevrim içi yayına denk gelir.
    tarihler = []
    for alan in ("published-online", "published-print", "published", "issued", "created"):
        parca = ((mesaj.get(alan) or {}).get("date-parts") or [[]])[0]
        if parca and parca[0]:
            y, a, g = (list(parca) + [1, 1])[:3]
            try:
                tarihler.append(date(int(y), int(a or 1), int(g or 1)))
            except ValueError:
                pass
    return TarihOnerisi(min(tarihler), "Crossref") if tarihler else None


def oneriler(faaliyetler, internet: bool = True) -> list[tuple[object, TarihOnerisi]]:
    """Yayın tarihi boş olan AVES faaliyetleri için tarih önerileri."""
    s = None
    sonuc = []
    for f in faaliyetler:
        if f.yayin_tarihi or not getattr(f, "aves_kod", ""):
            continue
        o = None
        if internet and f.kimlik.startswith("doi:"):
            if s is None:
                from .indir import oturum
                s = oturum()
            o = crossref_tarihi(f.kimlik[4:], s)
        o = o or aves_tarihi(getattr(f, "_kunye", ""))
        if o:
            sonuc.append((f, o))
    return sonuc
