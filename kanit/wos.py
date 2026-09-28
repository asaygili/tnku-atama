"""
Web of Science "atıf yapan yayınlar" dışa aktarımından atıf klasörleri oluşturma.

WoS'ta (Citation Report → Citing articles → isteğe bağlı "Web of Science Index"
süzgeci → Export → "Tab delimited file", içerik "Full Record and Cited References")
alınan dosya okunur. Her atıf yapan yayın için:
  • kaynakçasındaki (CR) DOI'lerden – yoksa yazar/yıl/cilt/sayfadan – hangi
    yayınımıza atıf yaptığı bulunur (birden çok yayınımıza atıf → her birine),
  • WoS indeksi (WE alanı) → EK-2 kodu (SCI-E / SSCI / AHCI → 5.1, ESCI → 5.2),
  • öz atıflar (yazarlar arasında aday) ve arşivde zaten bulunan atıflar atlanır,
  • yayının atiflar\\ klasöründe ayrı bir alt klasör açılır:
        WoS_<yıl>_<ilk yazar>_<başlık> (SCI-E)\\
            kayit.json          WoS kaydı (makine için)
            endeks_bilgisi.pdf  WoS kaydından üretilen endeks bilgisi sayfası
            atif_yapan.pdf      açık erişimli tam metin (varsa)
            INDIRILECEK.txt     ücretli yayınlar için DOI bağlantısı
"""

from __future__ import annotations

import csv
import json
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from .kayit import KanitArsivi, KanitKaydi
from .ortak import doi_bul, norm, pdf_metin, slug

KAYNAK = "wos"
INDIRILECEK_LISTESI = "_indirilecek_atiflar.xlsx"

# WoS tab-delimited alan etiketleri ↔ Excel sütun adları
ALANLAR = {
    "UT": ("UT", "UT (Unique WOS ID)"), "TI": ("TI", "Article Title"),
    "AU": ("AU", "Authors"), "AF": ("AF", "Author Full Names"), "SO": ("SO", "Source Title"),
    "SN": ("SN", "ISSN"), "EI": ("EI", "eISSN"), "PY": ("PY", "Publication Year"),
    "PD": ("PD", "Publication Date"), "EA": ("EA", "Early Access Date"), "DI": ("DI", "DOI"),
    "WE": ("WE", "Web of Science Index"), "CR": ("CR", "Cited References"),
    "DT": ("DT", "Document Type"), "VL": ("VL", "Volume"), "BP": ("BP", "Start Page"),
    "AR": ("AR", "Article Number"),
}
ENDEKS_KODU = [("5.1", ("science citation index expanded", "sci expanded", "science citation index",
                        "social sciences citation index", "ssci", "arts humanities citation index",
                        "a hci", "ahci")),
               ("5.2", ("emerging sources citation index", "esci"))]
ENDEKS_KISA = {"science citation index expanded": "SCI-E", "social sciences citation index": "SSCI",
               "arts humanities citation index": "AHCI", "emerging sources citation index": "ESCI"}


@dataclass
class WosKaydi:
    ut: str
    baslik: str
    yazarlar: list[str]
    dergi: str
    issn: str
    eissn: str
    yil: int | None
    doi: str
    endeks: str                       # WE alanı (ham)
    kaynakca: list[str] = field(default_factory=list)
    tur: str = ""

    @property
    def endeks_kodu(self) -> str | None:
        m = norm(self.endeks)
        for kod, ifadeler in ENDEKS_KODU:
            if any(norm(i) in m for i in ifadeler):
                return kod
        return None

    @property
    def endeks_kisa(self) -> str:
        m = norm(self.endeks)
        kisa = [v for k, v in ENDEKS_KISA.items() if k in m]
        return "/".join(kisa) or (self.endeks[:20] or "?")


# ── Okuma ──────────────────────────────────────────────────────────────────
def _satirlar(yol: Path) -> list[dict]:
    yol = Path(yol)
    if yol.suffix.lower() == ".xlsx":
        from openpyxl import load_workbook
        ws = load_workbook(yol, read_only=True).active
        rows = list(ws.iter_rows(values_only=True))
        basliklar = [str(h or "").strip() for h in rows[0]]
        return [{b: ("" if v is None else str(v)) for b, v in zip(basliklar, r)} for r in rows[1:]]
    if yol.suffix.lower() == ".xls":
        raise ValueError("Eski Excel (.xls) biçimi desteklenmiyor: WoS'tan 'Tab delimited file' "
                         "ya da .xlsx olarak dışa aktarın.")
    ham = yol.read_bytes()
    for kodlama in ("utf-8-sig", "utf-16", "cp1254"):
        try:
            metin = ham.decode(kodlama)
            if "\t" in metin.split("\n", 1)[0]:
                break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError("Dosya okunamadı (WoS 'Tab delimited file' bekleniyor)")
    okuyucu = csv.DictReader(metin.splitlines(), delimiter="\t", quoting=csv.QUOTE_NONE)
    return [{k.strip(): (v or "") for k, v in r.items() if k} for r in okuyucu]


def oku(yol: Path) -> list[WosKaydi]:
    sonuc = []
    for r in _satirlar(yol):
        def al(etiket):
            return next((r[a].strip() for a in ALANLAR[etiket] if r.get(a)), "")
        if not (al("TI") or al("UT")):
            continue
        yil = re.search(r"(19|20)\d{2}", al("PY") or al("EA"))
        sonuc.append(WosKaydi(
            ut=al("UT"), baslik=re.sub(r"\s+", " ", al("TI")),
            yazarlar=[a.strip() for a in (al("AU") or al("AF")).split(";") if a.strip()],
            dergi=al("SO"), issn=al("SN"), eissn=al("EI"),
            yil=int(yil.group(0)) if yil else None, doi=al("DI").lower(),
            endeks=al("WE"), kaynakca=[c.strip() for c in al("CR").split(";") if c.strip()],
            tur=al("DT")))
    return sonuc


# ── Eşleştirme ─────────────────────────────────────────────────────────────
def _ref_ipuclari(kunye: str) -> tuple[str, str, str]:
    """Künyeden (yıl, cilt, ilk sayfa)."""
    yil = (re.findall(r"\b((?:19|20)\d{2})\b", kunye) or [""])[-1]
    cilt = (re.search(r"vol\.\s*(\d+)", kunye) or [None, ""])[1]
    sayfa = (re.search(r"pp\.\s*(\d+)", kunye) or [None, ""])[1]
    return yil, cilt, sayfa


def atif_yapilan_yayinlar(k: WosKaydi, arsiv: KanitArsivi) -> list[KanitKaydi]:
    """Kaynakçasında geçen yayınlarımız (önce DOI; yoksa yıl + cilt + sayfa + soyad)."""
    bulunan = []
    for kay in arsiv.kayitlar:
        if not kay.aves_kod:
            continue
        doiler = {i[4:] for i in kay.kimlikler if i.startswith("doi:")}
        yil, cilt, sayfa = _ref_ipuclari(kay.kunye)
        for ref in k.kaynakca:
            ref_doi = doi_bul(ref)
            if ref_doi and ref_doi in doiler:
                bulunan.append(kay)
                break
            if not ref_doi and yil and cilt and sayfa:
                r = norm(ref)
                if f" {yil} " in f" {r} " and f"v{cilt} " in f"{r} " and f"p{sayfa}" in r.replace(" ", ""):
                    bulunan.append(kay)
                    break
    return bulunan


def oz_atif_mi(k: WosKaydi, soyad: str) -> bool:
    s = norm(soyad)
    return bool(s) and any(norm(a).split()[:1] == [s] for a in k.yazarlar)


def _mevcut_atiflar(kay: KanitKaydi) -> tuple[set[str], list[str]]:
    """Yayının atiflar\\ klasöründeki mevcut atıfların DOI'leri ve ilk sayfa metinleri."""
    doiler, metinler = set(), []
    for alt in kay.atif_klasorleri():
        kj = alt / "kayit.json"
        if kj.exists():
            try:
                if d := json.loads(kj.read_text(encoding="utf-8")).get("doi"):
                    doiler.add(d.lower())
            except (OSError, json.JSONDecodeError):
                pass
        for p in alt.glob("*.pdf"):
            ilk = pdf_metin(p, 1)[:5000]
            if d := doi_bul(ilk):
                doiler.add(d)
            metinler.append(norm(ilk))
    return doiler, metinler


@dataclass
class PlanSatiri:
    wos: WosKaydi
    hedef: KanitKaydi | None
    durum: str               # yeni / zaten var / öz atıf / kapsam dışı / eşleşmedi
    klasor: Path | None = None


def plan_olustur(arsiv: KanitArsivi, kayitlar: list[WosKaydi], soyad: str,
                 kodlar: tuple[str, ...] = ("5.1",)) -> list[PlanSatiri]:
    plan, mevcut = [], {}
    gorulen = set()                                # aynı dışa aktarımda iki kez gelen kayıt
    for w in kayitlar:
        anahtar = w.doi or w.ut or norm(w.baslik)
        if anahtar in gorulen:
            continue
        gorulen.add(anahtar)
        hedefler = atif_yapilan_yayinlar(w, arsiv)
        if not hedefler:
            plan.append(PlanSatiri(w, None, "eşleşmedi"))
            continue
        for h in hedefler:
            if oz_atif_mi(w, soyad):
                durum = "öz atıf"
            elif w.endeks_kodu not in kodlar:
                durum = "kapsam dışı"
            else:
                if h.aves_kod not in mevcut:
                    mevcut[h.aves_kod] = _mevcut_atiflar(h)
                doiler, metinler = mevcut[h.aves_kod]
                bn = norm(w.baslik)[:80]
                var = (w.doi and w.doi in doiler) or (len(bn) > 30 and any(bn in m for m in metinler))
                durum = "zaten var" if var else "yeni"
            yazar = (w.yazarlar[0].split(",")[0] if w.yazarlar else "Anonim")
            klasor = h.klasor / "atiflar" / (f"WoS_{w.yil or 0}_{slug(yazar, 20)}_"
                                             f"{slug(w.baslik, 45)} ({w.endeks_kisa})")
            plan.append(PlanSatiri(w, h, durum, klasor))
    return plan


# ── Uygulama ───────────────────────────────────────────────────────────────
def _endeks_sayfasi(w: WosKaydi, hedef: KanitKaydi, yol: Path) -> None:
    import fitz
    from .paket import _Yazici
    doc = fitz.open()
    _Yazici(doc).sayfa([
        ("ATIF KANITI – WEB OF SCIENCE KAYDI", 14, True),
        (f"Atıf yapan yayın:\n{w.baslik}", 11, True),
        (f"Yazarlar: {'; '.join(w.yazarlar[:12])}{' …' if len(w.yazarlar) > 12 else ''}", 10, False),
        (f"Dergi: {w.dergi}\nISSN: {w.issn or '-'}   eISSN: {w.eissn or '-'}\n"
         f"Yayın yılı: {w.yil or '-'}   Belge türü: {w.tur or '-'}\n"
         f"DOI: {w.doi or '-'}\nWoS kayıt no (UT): {w.ut or '-'}", 10, False),
        (f"Web of Science Index: {w.endeks or '-'}", 11, True),
        (f"Atıf yapılan eser ({hedef.aves_kod}):\n{hedef.kunye}", 10, False),
        ("Bu sayfa, Web of Science Core Collection 'atıf yapan yayınlar' dışa aktarımından "
         "(Full Record and Cited References) otomatik üretilmiştir. Komisyon ayrıca Master "
         "Journal List ekran görüntüsü isterse aynı klasöre eklenebilir.", 8, False),
    ])
    doc.save(yol)


def uygula(plan: list[PlanSatiri], arsiv: KanitArsivi, indir: bool = True,
           ilerleme=None) -> Counter:
    """'yeni' satırlar için klasör açar; açık erişimli tam metni indirmeyi dener."""
    from .indir import acik_erisim, oturum, pdf_indir
    s = oturum() if indir else None
    sayac = Counter()
    yeniler = [p for p in plan if p.durum == "yeni"]
    for i, p in enumerate(yeniler, 1):
        if ilerleme:
            ilerleme(i, len(yeniler), p)
        w = p.wos
        p.klasor.mkdir(parents=True, exist_ok=True)
        (p.klasor / "kayit.json").write_text(json.dumps({
            "kaynak": KAYNAK, "ut": w.ut, "doi": w.doi, "baslik": w.baslik, "yazarlar": w.yazarlar,
            "dergi": w.dergi, "issn": w.issn, "eissn": w.eissn, "yil": w.yil,
            "endeks": w.endeks, "endeks_kodu": w.endeks_kodu,
            "atif_yapilan": p.hedef.aves_kod}, ensure_ascii=False, indent=1), encoding="utf-8")
        _endeks_sayfasi(w, p.hedef, p.klasor / "endeks_bilgisi.pdf")
        indi = False
        if indir and w.doi:
            try:
                for url in acik_erisim(w.doi, s)["pdf"]:
                    ok, _ = pdf_indir(url, p.klasor / "atif_yapan.pdf", s, deneme=2)
                    if ok:
                        indi = True
                        break
            except Exception:  # noqa: BLE001 – ağ hatası klasör oluşturmayı engellemesin
                pass
        if not indi:
            (p.klasor / "INDIRILECEK.txt").write_text(
                "Bu atıf yapan yayının tam metni açık erişimli değil (ya da indirilemedi).\n"
                "Üniversite hesabınızla indirip bu klasöre koyun (dosya adı önemli değil):\n"
                + (f"https://doi.org/{w.doi}\n" if w.doi else f"WoS: {w.ut}\n"), encoding="utf-8")
        sayac["tam metin indirildi" if indi else "tam metin indirilecek"] += 1
    sayac.update(p.durum for p in plan)
    indirilecek_listesi(arsiv)
    return sayac


def indirilecek_listesi(arsiv: KanitArsivi) -> Path | None:
    """Tam metni henüz konmamış WoS atıflarının listesi (kanıt kökünde Excel)."""
    satirlar = []
    for kay in arsiv.kayitlar:
        for alt in kay.atif_klasorleri():
            if (alt / "INDIRILECEK.txt").exists():
                pdfler = [p for p in alt.glob("*.pdf") if p.name != "endeks_bilgisi.pdf"]
                if pdfler:                         # kullanıcı tam metni koymuş
                    (alt / "INDIRILECEK.txt").unlink()
                    continue
                try:
                    v = json.loads((alt / "kayit.json").read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    v = {}
                satirlar.append([kay.aves_kod, v.get("baslik", alt.name), v.get("dergi", ""),
                                 v.get("yil", ""), f"https://doi.org/{v['doi']}" if v.get("doi") else "",
                                 str(alt)])
    yol = arsiv.kok / INDIRILECEK_LISTESI
    if not satirlar:
        if yol.exists():
            yol.unlink()
        return None
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "İndirilecek atıflar"
    ws.append(["Atıf yapılan", "Atıf yapan yayın", "Dergi", "Yıl", "DOI bağlantısı", "Klasör"])
    for r in satirlar:
        ws.append(r)
    for col, w in zip("ABCDEF", (10, 70, 35, 6, 40, 80)):
        ws.column_dimensions[col].width = w
    wb.save(yol)
    return yol
