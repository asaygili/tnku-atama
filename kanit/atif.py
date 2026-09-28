"""
Atıfların kanıt klasöründen sayılması (EK-2 5.x).

Her yayın klasörünün atiflar\\ alt klasöründe, atıf yapan her yayının PDF'i bir atıf
sayılır. Aynı atıf yapan yayın (aynı içerik ya da aynı DOI) iki kez sayılmaz.
Endeks, aynı atıf klasöründeki kanıt belgelerinden (Master Journal List, dizin
sayfası vb.) ve atıf yapan yayının ilk sayfasından okunur:
    SCI / SCI-E / SSCI / AHCI  → 5.1     ESCI / Scopus → 5.2     TR Dizin → 5.5
Belirlenemeyenler "belirsiz" olarak işaretlenir (kullanıcı karar verir).
Adayın kendisinin yazar olduğu yayın öz atıftır ve sayılmaz (EK-2 atıf tanımı).
WoS "Citations of …" ekran görüntüleri atıf listesidir; tek tek atıf sayılmaz.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from .kayit import KanitArsivi, KanitKaydi
from .ortak import doi_bul, md5, norm, pdf_metin

KANIT_BELGESI = ("master journal", "journal search", "dizin", "indeks", "index", "kanit",
                 "cilt", "ekran", "citations of", "secili", "ilgili sayfa", "ilgilisayfa", "son5",
                 "about", "editor", "aims and scope", "archives", "scope", "atif yapilan",
                 "atifyapilan", "retrieve", "out.pdf", "issn", "endeks")
ENDEKS_IFADELERI = [
    ("5.1", ("science citation index expanded", "science citation index", "sci expanded",
             "social sciences citation index", "arts humanities citation index", "sci e ")),
    ("5.2", ("emerging sources citation index", "esci", "scopus")),
    ("5.5", ("tr dizin", "trdizin", "ulakbim")),
    ("5.7", ("book citation index", "bkci")),
]


@dataclass
class Atif:
    atif_yapilan: str          # AVES kodu (UM22 …)
    yol: Path                  # atıf yapan yayının PDF'i
    endeks: str | None         # "5.1" / "5.2" / "5.5" / None (belirsiz)
    oz_atif: bool
    doi: str
    yil: int | None

    def tarih(self) -> date | None:
        return date(self.yil, 1, 1) if self.yil else None


def _kanit_belgesi_mi(p: Path) -> bool:
    n = norm(p.name)
    return any(norm(k) in n for k in KANIT_BELGESI)


# Bazı eski PDF'lerde "i" harfi bozuk karakterlerle kodlanmış ("Clarඈvate Analytඈcs")
BOZUK_I = str.maketrans({"ඈ": "i", "൴": "i"})
# Arşiv klasör adlarındaki endeks ipuçları: "Atıf 38 (SCI)", "Atıf 36 (Diğer)"
KLASOR_IPUCU = [("5.1", r"\((?:sci|sci-?e|ssci|ahci)\)|\bsci-?e\b|\bssci\b"),
                ("5.2", r"\((?:esci|scopus)\)|\besci\b|\bscopus\b"),
                ("5.5", r"tr ?dizin")]


def _klasor_endeksi(ad: str) -> str | None:
    n = ad.lower()
    for kod, desen in KLASOR_IPUCU:
        if re.search(desen, n):
            return kod
    return None


def _endeks(metin: str) -> str | None:
    m = " " + norm((metin or "").translate(BOZUK_I)) + " "
    for kod, ifadeler in ENDEKS_IFADELERI:
        if any(f" {norm(i)} " in m or norm(i) in m for i in ifadeler):
            return kod
    return None


def _yil(metin: str) -> int | None:
    for desen in (r"(?:published|yayın tarihi|accepted|received)[^0-9]{0,40}((?:19|20)\d{2})",
                  r"©\s*((?:19|20)\d{2})"):
        if m := re.search(desen, metin, re.I):
            return int(m.group(1))
    yillar = [int(y) for y in re.findall(r"\b((?:19|20)\d{2})\b", metin[:3000])]
    return max(yillar) if yillar else None


def _wos_atifi(k: KanitKaydi, alt: Path) -> Atif | None:
    """WoS dışa aktarımından açılmış atıf klasörü (kayit.json kaynak=wos)."""
    import json
    kj = alt / "kayit.json"
    if not kj.exists():
        return None
    try:
        v = json.loads(kj.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if v.get("kaynak") != "wos":
        return None
    pdfler = sorted(p for p in alt.glob("*.pdf") if p.name != "endeks_bilgisi.pdf")
    yol = pdfler[0] if pdfler else alt / "endeks_bilgisi.pdf"
    return Atif(k.aves_kod, yol, v.get("endeks_kodu"), False, (v.get("doi") or "").lower(),
                v.get("yil"))


def atiflari_topla(arsiv: KanitArsivi, soyad: str) -> list[Atif]:
    soyad_n = norm(soyad)
    sonuc: list[Atif] = []
    for k in arsiv.kayitlar:
        if not k.aves_kod:
            continue
        gorulen_hash, gorulen_doi, gorulen_metin = set(), set(), set()
        for alt in k.atif_klasorleri():
            if (w := _wos_atifi(k, alt)) is not None:
                # WoS dışa aktarımından açılan klasör: endeks ve yıl WoS kaydından;
                # tam metin henüz konmamış olsa da atıf WoS kaydıyla belgelidir
                if w.doi and w.doi in gorulen_doi:
                    continue
                if w.doi:
                    gorulen_doi.add(w.doi)
                if w.yol != alt / "endeks_bilgisi.pdf":
                    gorulen_hash.add(md5(w.yol))
                sonuc.append(w)
                continue
            dosyalar = [p for p in alt.iterdir() if p.is_file()]
            kanitlar = [p for p in dosyalar if _kanit_belgesi_mi(p)]
            yayinlar = [p for p in dosyalar if p.suffix.lower() == ".pdf" and p not in kanitlar]
            klasor_endeksi = _klasor_endeksi(alt.name)
            for p in kanitlar:
                if e := _endeks(p.name + " " + pdf_metin(p, 1)[:4000]):
                    if klasor_endeksi is None or e < klasor_endeksi:     # 5.1 < 5.2 < 5.5
                        klasor_endeksi = e
            for p in yayinlar:
                import fitz
                try:
                    if fitz.open(p).page_count < 3:
                        continue
                except Exception:
                    continue
                h = md5(p)
                ilk = pdf_metin(p, 1)
                doi = doi_bul(ilk[:5000])
                # Aynı yayının ayrı indirilmiş kopyaları: aynı içerik / DOI / ilk sayfa metni
                metin_izi = norm(ilk[:1500])
                if h in gorulen_hash or (doi and doi in gorulen_doi) or                         (len(metin_izi) > 20 and metin_izi in gorulen_metin):
                    continue
                gorulen_hash.add(h)
                gorulen_metin.add(metin_izi)
                if doi:
                    gorulen_doi.add(doi)
                endeks = klasor_endeksi if len(yayinlar) == 1 or klasor_endeksi else None
                endeks = endeks or _endeks(ilk[:3000])
                oz = bool(soyad_n) and soyad_n in norm(ilk[:1500])
                sonuc.append(Atif(k.aves_kod, p, endeks, oz, doi, _yil(ilk)))
    return sonuc


def ozet(atiflar: list[Atif], basvuru_tarihi: date | None = None) -> Counter:
    """(endeks, 'sonrası'/'öncesi'/'bilinmiyor') → adet; öz atıflar hariç."""
    c = Counter()
    for a in atiflar:
        if a.oz_atif:
            continue
        if basvuru_tarihi and a.yil:
            zaman = "sonrası" if a.yil > basvuru_tarihi.year else "öncesi"
        else:
            zaman = "bilinmiyor"
        c[(a.endeks or "belirsiz", zaman)] += 1
    return c


def faaliyetler(atiflar: list[Atif], basvuru_tarihi: date | None, belirsiz_kod: str | None,
                faaliyet_sinifi) -> list:
    """Atıfları EK-2 5.x faaliyetlerine dönüştürür (kimlik 'atif:<kod>:<zaman>').

    Doçentlik başvurusu yılı ile aynı yıldaki atıflar temkinli olarak 'öncesi' sayılır.
    belirsiz_kod: endeksi belirlenemeyenlerin kodu (None → eklenmez)."""
    toplam = Counter()
    for (endeks, zaman), adet in ozet(atiflar, basvuru_tarihi).items():
        kod = endeks if endeks != "belirsiz" else belirsiz_kod
        if kod:
            toplam[(kod, zaman)] += adet
    return [faaliyet_sinifi(kod, adet=adet, docent_sonrasi=(zaman == "sonrası"),
                            kimlik=f"atif:{kod}:{zaman}")
            for (kod, zaman), adet in sorted(toplam.items())]
