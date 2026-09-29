"""
Kanıt denetimi: puan alan her faaliyetin yönergenin istediği belgelerle desteklenip
desteklenmediği (EYS-YNG-129 Md. 7: "Tüm akademik/bilimsel etkinliklerin
belgelendirilmiş olması şarttır").
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import tnku_atama as t

from .kayit import KanitArsivi
from .kontrol import durum as kanit_durumu
from .ortak import norm

# Kanıt türü → ilgili yönerge maddesi
MADDE = {"tam_metin": "Md. 7(4)/(6)", "endeks": "Md. 7(3)", "q": "EK-2 1.1 (Q çarpanı)",
         "program": "Md. 7(5)", "katilim": "Md. 7(5)", "kapak": "Md. 7(5)", "isbn": "Md. 7(6)"}


# Md. 7(4): makale "cilt, sayı ve sayfa numarası alınmış" olmalı
CILT_SAYFA = re.compile(r"\bvol\.?\s*\d|\bcilt\b|\bpp\.?\s*\d|\bss\.?\s*\d|"
                        r"\bno\.?\s*\d|\bsayı\b|\bsayfa\b|\bart(icle)?\.?\s*(no\.?)?\s*\d",
                        re.I)


@dataclass
class Uyari:
    faaliyet: object
    sira: int
    aves_kod: str
    kod: str
    ad: str
    eksikler: list[str] = field(default_factory=list)   # açıklama (madde)
    etiket: str = ""                                     # faaliyetin adı (yayın / proje / dergi)


# Yayın dışı faaliyetlerde istenen kanıt
KANIT_ONERISI = {
    "6": "dergiden hakemlik teşekkür e-postası ya da Web of Science Reviewer Recognition kaydı",
    "12": "proje sözleşmesi / görevlendirme ve tamamlandığını gösteren sonuç raporu kabul yazısı",
    "18": "görevlendirme yazısı (başlangıç ve bitiş tarihli)",
    "17": "ders görevlendirme / tez atama yazısı",
}


def faaliyet_etiketi(f, arsiv: KanitArsivi | None = None, uzunluk: int = 70) -> str:
    """Faaliyetin okunur adı: yayın başlığı, proje / dergi / görev adı ya da EK-2 adı."""
    import aves_yardimci as ay
    kunye = getattr(f, "_kunye", "") or ""
    ad = ay.baslik_cikar(kunye) if kunye and getattr(f, "kod", "")[:2] in (
        "1.", "2.", "3.") else kunye.split(", Hakemlik")[0]
    if not ad and arsiv is not None and (k := arsiv.bul(f)) is not None:
        ad = (ay.baslik_cikar(k.kunye) if k.kunye else "") or k.klasor.name
    ad = " ".join((ad or t.EK2_PUANLAR.get(f.kod, {}).get("ad", "")).split())
    return ad[:uzunluk - 1] + "…" if len(ad) > uzunluk else ad


def tavan_disi(faaliyetler, arsiv: KanitArsivi | None) -> set[int]:
    """Grup üst sınırı (hakemlik 20, atıf 50…) dolduğu için hiç puan almayan faaliyetler
    (id kümesi). Kanıtı bulunanlar önce sayılır; böylece sınır belgeli olanlarla dolar."""
    liste = [f for f in faaliyetler if f.kod in t.EK2_PUANLAR]
    if arsiv is not None:
        liste.sort(key=lambda f: arsiv.bul(f) is None)
    p = t.puan_hesapla(t.AdayBilgi(faaliyetler=liste))
    return {id(f) for f, d in zip(liste, p["detaylar"]) if d["puan"] <= 0 < d["ham_puan"]}


def denetle(faaliyetler, arsiv: KanitArsivi | None) -> list[Uyari]:
    if arsiv is None:
        return []
    uyarilar = []
    disarida = tavan_disi(faaliyetler, arsiv)
    for i, f in enumerate(faaliyetler, 1):
        if f.kod not in t.EK2_PUANLAR or t.faaliyet_puan_hesapla(f)[0] <= 0 or id(f) in disarida:
            continue
        bilgi = t.EK2_PUANLAR[f.kod]
        eksik = []
        if f.kimlik.startswith("atif:"):
            continue                      # atıflar yayın klasörlerinin atiflar\ kanıtlarından sayıldı
        k = arsiv.bul(f)
        if k is None:
            oneri = KANIT_ONERISI.get(f.kod.split(".")[0])
            eksik.append("Kanıt klasörü bağlı değil (Md. 7(7))"
                         + (f" – gereken: {oneri}" if oneri else ""))
        elif k.aves_kod:
            onek = k.aves_kod[:2]
            d = kanit_durumu(k, onek)
            eksik += [f"{a} ({MADDE.get(e, 'Md. 7(7)')})"
                      for e, a in zip(d.eksik, d.eksik_aciklamalari())]
            if onek in ("UM", "UL") and not CILT_SAYFA.search(k.kunye or ""):
                eksik.append("Künyede cilt / sayı / sayfa numarası yok – öngörünümdeki makale "
                             "başvuru tarihine kadar yayımlanmış olmalıdır (Md. 7(4))")
        else:
            dosyalar = k.dosyalar()
            if not dosyalar:
                eksik.append("Bağlı klasörde belge yok (Md. 7(7))")
            if bilgi["grup"] == 12 and not any(
                    x in norm(p.name) for p in dosyalar for x in ("sonuc", "kabul", "rapor")):
                eksik.append("Projenin tamamlandığını gösteren sonuç raporu / kabul yazısı "
                             "(EK-2 12: tamamlanmış olmalıdır)")
        if f.baslica_eser and (k is None or not k.tam_metin):
            eksik.append("Başlıca Araştırma Eseri'nin tam metni (Md. 11(5))")
        if eksik:
            uyarilar.append(Uyari(f, i, getattr(f, "aves_kod", ""), f.kod, bilgi["ad"], eksik,
                                  faaliyet_etiketi(f, arsiv)))
    return uyarilar
