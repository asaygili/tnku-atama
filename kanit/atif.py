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
    ay: date | None = None        # yayım ayının ilk günü (WoS erken erişim / yayın tarihi)
    kitap_bolumu: bool = False    # atıf yapan yayın bir kitap bölümü (ÜAK 5b)

    def tarih(self) -> date | None:
        return self.ay or (date(self.yil, 1, 1) if self.yil else None)


def zaman(a: Atif, basvuru_tarihi: date | None) -> str:
    """'sonrası' / 'öncesi' / 'bilinmiyor' (EK-1 (g), Md. 11(2)).

    Ay biliniyorsa: ayın tamamı başvuru tarihinden sonraysa 'sonrası'.
    Yalnızca yıl biliniyorsa başvuru yılındaki atıflar temkinli olarak 'öncesi' sayılır."""
    if not basvuru_tarihi:
        return "bilinmiyor"
    if a.ay:
        return "sonrası" if a.ay > basvuru_tarihi else "öncesi"
    if a.yil:
        return "sonrası" if a.yil > basvuru_tarihi.year else "öncesi"
    return "bilinmiyor"


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
    # Etiketsiz yıllar ("Vision 2030" gibi) atıfı başvuru sonrasına kaydırmasın: en küçüğü
    yillar = [int(y) for y in re.findall(r"\b((?:19|20)\d{2})\b", metin[:3000])]
    return min(yillar) if yillar else None


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
    try:
        ay = date.fromisoformat(v["tarih"]) if v.get("tarih") else None
    except ValueError:
        ay = None
    return Atif(k.aves_kod, yol, v.get("endeks_kodu"), False, (v.get("doi") or "").lower(),
                v.get("yil"), ay, bool(v.get("kitap_bolumu")))


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
                # Md. 4(d): adayın yazar olduğu yayın öz atıftır (soyadı tam kelime olarak,
                # uzun yazar listeleri için ilk sayfanın başında)
                oz = bool(soyad_n) and re.search(rf"\b{re.escape(soyad_n)}\b",
                                                 norm(ilk[:4000])) is not None
                sonuc.append(Atif(k.aves_kod, p, endeks, oz, doi, _yil(ilk)))
    return sonuc


def ozet(atiflar: list[Atif], basvuru_tarihi: date | None = None) -> Counter:
    """(endeks, 'sonrası'/'öncesi'/'bilinmiyor') → adet; öz atıflar hariç."""
    c = Counter()
    for a in atiflar:
        if a.oz_atif:
            continue
        c[(a.endeks or "belirsiz", zaman(a, basvuru_tarihi))] += 1
    return c


KITAP_BOLUMU_UAK = "5b"   # ÜAK: kitaplarda bölüm olarak yayımlanan yayınlardaki atıf


def kimlik_coz(kimlik: str) -> tuple[str, str, bool]:
    """'atif:<kod>:<zaman>[:bolum]' → (kod, zaman, kitap_bolumu)."""
    p = kimlik.split(":")
    return p[1], p[2] if len(p) > 2 else "bilinmiyor", p[3:4] == ["bolum"]


def sayilan(atiflar: list[Atif], belirsiz_kod: str | None = None,
            haric: tuple[str, ...] = ()) -> list[Atif]:
    """Puana giren atıflar: öz atıflar, hariç tutulan endeksler (örn. ESCI) ve kodu
    verilmemiş belirsizler dışarıda."""
    return [a for a in atiflar if not a.oz_atif and (kod := a.endeks or belirsiz_kod)
            and kod not in haric]


def _pdf_basligi(yol: Path) -> str:
    """Makale PDF'inin başlığı: ilk sayfadaki en büyük yazı (yoksa PDF meta verisi)."""
    try:
        import fitz
        d = fitz.open(yol)
        satirlar = []
        for b in d[0].get_text("dict")["blocks"]:
            for ln in b.get("lines", []):
                metin = " ".join(sp["text"] for sp in ln["spans"]).strip()
                if len(metin) > 3 and ln["spans"]:
                    satirlar.append((round(max(sp["size"] for sp in ln["spans"]), 1), metin))
        if satirlar:
            buyuk = max(b for b, m in satirlar if len(m) > 12) if any(
                len(m) > 12 for _, m in satirlar) else max(b for b, _ in satirlar)
            baslik = " ".join(m for b, m in satirlar if b == buyuk)
            if 15 < len(baslik) < 300:
                return " ".join(baslik.split())
        meta = (d.metadata or {}).get("title", "")
        if 15 < len(meta) < 300 and not meta.lower().endswith((".pdf", ".doc", ".docx")):
            return meta
    except Exception:  # noqa: BLE001
        pass
    return ""


_CROSSREF: dict | None = None


def _temiz(t: str) -> str:
    """Crossref metni: HTML kaçışları ve yazı tipinde olmayan tire/boşluk karakterleri."""
    import html
    t = html.unescape(html.unescape(t or ""))
    t = re.sub(r"<[^>]+>", "", t)                      # <i>, <sub> gibi etiketler
    for a, b in (("‐", "-"), ("‑", "-"), ("‒", "-"), ("–", "–"),
                 (" ", " "), (" ", " "), (" ", " ")):
        t = t.replace(a, b)
    return " ".join(t.split())


def _crossref(doi: str, onbellek: Path | None) -> dict:
    """DOI → {baslik, dergi} (Crossref; sonuçlar önbellek dosyasında saklanır)."""
    global _CROSSREF
    import json
    if _CROSSREF is None:
        try:
            _CROSSREF = json.loads(onbellek.read_text(encoding="utf-8")) if onbellek else {}
        except (OSError, ValueError):
            _CROSSREF = {}
    if doi in _CROSSREF:
        return {k: _temiz(v) for k, v in _CROSSREF[doi].items()}
    sonuc = {}
    try:
        import requests
        r = requests.get(f"https://api.crossref.org/works/{doi}", timeout=15,
                         headers={"User-Agent": "tnku-atama (mailto:destek@example.org)"})
        if r.status_code == 200:
            m = r.json()["message"]
            sonuc = {"baslik": _temiz((m.get("title") or [""])[0]),
                     "dergi": _temiz((m.get("container-title") or [""])[0])}
    except Exception:  # noqa: BLE001 – internet yoksa boş
        return {}
    _CROSSREF[doi] = sonuc
    if onbellek:
        try:
            onbellek.parent.mkdir(parents=True, exist_ok=True)
            onbellek.write_text(json.dumps(_CROSSREF, ensure_ascii=False, indent=0), encoding="utf-8")
        except OSError:
            pass
    return sonuc


def bilgi(a: Atif, onbellek: Path | None = None, internet: bool = True) -> dict:
    """Atıf yapan yayının listede gösterilecek bilgileri: WoS kaydı varsa oradan; yoksa
    DOI ile Crossref'ten, o da yoksa PDF'in ilk sayfasındaki başlıktan."""
    import json
    v = {}
    kj = a.yol.parent / "kayit.json"
    if kj.exists():
        try:
            v = json.loads(kj.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            v = {}
    wos = v.get("kaynak") == "wos"
    baslik, dergi = (v.get("baslik", ""), v.get("dergi", "")) if wos else ("", "")
    doi = a.doi or v.get("doi", "")
    if not baslik and doi and internet:
        c = _crossref(doi, onbellek)
        baslik, dergi = c.get("baslik", ""), c.get("dergi", "")
    if not baslik and a.yol.exists():
        baslik = _pdf_basligi(a.yol)
    if not baslik:
        baslik = a.yol.parent.name if a.yol.parent.name.lower() != "atiflar" else a.yol.stem
        baslik = re.sub(r"^(Atama|Docentlik|Tesvik)\d{4}_", "", baslik).strip()
    aylar = "Ocak Şubat Mart Nisan Mayıs Haziran Temmuz Ağustos Eylül Ekim Kasım Aralık".split()
    tarih = (f"{aylar[a.ay.month - 1]} {a.ay.year}" if a.ay else str(a.yil) if a.yil else "?")
    return {"baslik": baslik, "dergi": dergi, "tarih": tarih, "doi": doi, "wos": wos}


def faaliyetler(atiflar: list[Atif], basvuru_tarihi: date | None, belirsiz_kod: str | None,
                faaliyet_sinifi, haric: tuple[str, ...] = ()) -> list:
    """Atıfları EK-2 5.x faaliyetlerine dönüştürür (kimlik 'atif:<kod>:<zaman>[:bolum]').

    Zaman ayrımı `zaman()` ile yapılır. Kitap bölümlerindeki atıflar (5.7) ayrı satır olur
    ve ÜAK'ta 5b kalemine eşlenir. belirsiz_kod: endeksi belirlenemeyenlerin kodu
    (None → eklenmez)."""
    toplam = Counter()
    for a in sayilan(atiflar, belirsiz_kod, haric):
        kod = a.endeks or belirsiz_kod
        toplam[(kod, zaman(a, basvuru_tarihi), a.kitap_bolumu and kod == "5.7")] += 1
    sonuc = []
    for (kod, z, bolum), adet in sorted(toplam.items()):
        f = faaliyet_sinifi(kod, adet=adet, docent_sonrasi=(z == "sonrası"),
                            kimlik=f"atif:{kod}:{z}" + (":bolum" if bolum else ""))
        if bolum and hasattr(f, "uak_kalem"):
            f.uak_kalem = KITAP_BOLUMU_UAK
        sonuc.append(f)
    return sonuc
