"""Bildiri kitabından bir bildirinin sayfalarını ve kapak/künye sayfalarını kesme."""

from __future__ import annotations

import re
from pathlib import Path

import fitz

from .ortak import norm


def bildiri_sayfalari(kitap: Path, baslik: str, klasor: Path, yazar: str,
                      ozet: bool = False) -> str:
    """Bildirinin sayfalarını klasor/bildiri_sayfalari.pdf, kitabın ilk 4 sayfasını
    klasor/bildiri_kitabi_kapak_kunye.pdf olarak kaydeder. Açıklama döndürür.

    Bildirinin ilk sayfası: başlığın ilk kelimeleri sayfanın başında geçer ve yazar
    adı bulunur (içindekiler sayfası elenir; aynı başlık birden çok sayfada geçerse
    sonuncusu gerçek bildiridir). Sonraki bildirinin ilk sayfası: özet + anahtar
    kelimeler içerir ve kongre başlığıyla (sayfa numarasıyla değil) başlar.
    """
    doc = fitz.open(kitap)
    kapak = fitz.open()
    kapak.insert_pdf(doc, from_page=0, to_page=min(3, doc.page_count - 1))
    kapak.save(klasor / "bildiri_kitabi_kapak_kunye.pdf")
    kapak.close()

    kelimeler = [w for w in norm(baslik).split() if len(w) > 3][:7]
    if not kelimeler:
        return "başlık kelimesi yok"
    ifade = " ".join(norm(baslik).split()[:4])
    yazar_n = norm(yazar)
    adaylar = []
    for i in range(doc.page_count):
        metin = norm(doc[i].get_text())
        if yazar_n and yazar_n not in metin:
            continue
        konum = metin.find(ifade)
        puan = sum(w in metin[:1500] for w in kelimeler)
        if konum != -1 and konum < 800 and puan >= max(3, len(kelimeler) * 0.6):
            adaylar.append(i)
    if not adaylar:
        return "bildiri sayfası kitapta otomatik bulunamadı"
    bas = son = adaylar[-1]
    if not ozet:
        ilk_ust = norm(doc[bas].get_text())[:40]
        for j in range(bas + 1, min(bas + 30, doc.page_count)):
            m = norm(doc[j].get_text())
            yeni = (("abstract" in m or "ozet" in m)
                    and ("keywords" in m or "key words" in m or "anahtar kelime" in m)
                    and (j > bas + 1 or m[:40] == ilk_ust or not m[:1].isdigit()))
            if yeni:
                break
            son = j
    out = fitz.open()
    out.insert_pdf(doc, from_page=bas, to_page=son)
    out.save(klasor / "bildiri_sayfalari.pdf")
    out.close()
    return f"kitabın {bas + 1}–{son + 1}. sayfaları kesildi (elle kontrol edin)"


def kongre_adi(kunye: str) -> str:
    """AVES bildiri künyesinde başlıktan sonraki bölüm = kongre adı."""
    parca = [p.strip() for p in re.split(r",\s*", kunye)]
    import aves_yardimci as ay
    baslik = ay.baslik_cikar(kunye)
    if baslik in parca and parca.index(baslik) + 1 < len(parca):
        return parca[parca.index(baslik) + 1]
    return kunye
