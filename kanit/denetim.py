"""
Kanıt denetimi: puan alan her faaliyetin yönergenin istediği belgelerle desteklenip
desteklenmediği (EYS-YNG-129 Md. 7: "Tüm akademik/bilimsel etkinliklerin
belgelendirilmiş olması şarttır").
"""

from __future__ import annotations

from dataclasses import dataclass, field

import tnku_atama as t

from .kayit import KanitArsivi
from .kontrol import durum as kanit_durumu
from .ortak import norm

# Kanıt türü → ilgili yönerge maddesi
MADDE = {"tam_metin": "Md. 7(4)/(6)", "endeks": "Md. 7(3)", "q": "EK-2 1.1 (Q çarpanı)",
         "program": "Md. 7(5)", "katilim": "Md. 7(5)", "kapak": "Md. 7(5)", "isbn": "Md. 7(6)"}


@dataclass
class Uyari:
    faaliyet: object
    sira: int
    aves_kod: str
    kod: str
    ad: str
    eksikler: list[str] = field(default_factory=list)   # açıklama (madde)


def denetle(faaliyetler, arsiv: KanitArsivi | None) -> list[Uyari]:
    if arsiv is None:
        return []
    uyarilar = []
    for i, f in enumerate(faaliyetler, 1):
        if f.kod not in t.EK2_PUANLAR or t.faaliyet_puan_hesapla(f)[0] <= 0:
            continue
        bilgi = t.EK2_PUANLAR[f.kod]
        eksik = []
        if f.kimlik.startswith("atif:"):
            continue                      # atıflar yayın klasörlerinin atiflar\ kanıtlarından sayıldı
        k = arsiv.bul(f)
        if k is None:
            eksik.append("Kanıt klasörü bağlı değil (Md. 7(7))")
        elif k.aves_kod:
            onek = k.aves_kod[:2]
            d = kanit_durumu(k, onek)
            eksik += [f"{a} ({MADDE.get(e, 'Md. 7(7)')})"
                      for e, a in zip(d.eksik, d.eksik_aciklamalari())]
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
            uyarilar.append(Uyari(f, i, getattr(f, "aves_kod", ""), f.kod, bilgi["ad"], eksik))
    return uyarilar
