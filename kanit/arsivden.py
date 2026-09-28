"""
Eski arşiv klasörlerindeki (teşvik, doçentlik, atama dosyaları) belgeleri kanıt
arşivindeki faaliyet klasörlerine eşleyip KOPYALAR. Kaynak klasörler yalnızca okunur.

Eşleştirme:
  • Yayın: başlığın ardışık kelime grupları PDF'in ilk sayfalarında geçmeli
    (ya da dosya/klasör adı başlığın tamamını / başlangıcını içermeli).
  • Atıf klasörü: atıf yapılan eser ilk sayfadan, üst klasör adından ya da atıf
    yapan yayının kaynakçasından bulunur (birden çok yayınımıza atıf → her birine).
  • Ders / hakemlik / proje / idari görev: klasör ve dosya adı kuralları.
  • Tekrar: hedefte ya da daha önce işlenmiş kaynaklarda aynı içerik (MD5) varsa
    eklenmez; farklı yayınlara atıf yapan makale her yayın için ayrı kalemdir.

Kişiye özgü kurallar kanıt kökündeki `_eslestirme_kurallari.json` dosyasındadır:
  {"diger_basliklar": {"NB02": ["İngilizce başlık"]},
   "elle_klasor": {"Yayın No 9 (Bildiri)": "UB11"},
   "elle_yer": {"dosya.pdf": ["UM27", "HAKEM_Hakemlikler"]},
   "atla": ["CD.rar"]}
"""

from __future__ import annotations

import csv
import json
import re
import shutil
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

import aves_yardimci as ay

from .kayit import KanitArsivi
from .ortak import md5, norm, pdf_metin

KURAL_DOSYASI = "_eslestirme_kurallari.json"

# Genel (kişiye özgü olmayan) klasör adı kuralları: normalize ad sonu → hedef klasör
OZEL_KLASOR = {
    "verilen dersler": "DERS_Verilen_Dersler",
    "hakemlikler": "HAKEM_Hakemlikler",
    "dekan yardimciligi gorevi": "IDARI_Gorevler",
    "komisyon gorevleri": "IDARI_Gorevler",
    "idari gorevler": "IDARI_Gorevler",
    "tubitak proje": "PROJE_TUBITAK",
    "bap proje": "PROJE_BAP",
    "proje": "PROJE_TUBITAK",
    "beyan formu": "_Genel_Belgeler",
    "yoksis basvuru formu": "_Genel_Belgeler",
    "diploma": "_Kisisel_Belgeler",
}
DOSYA_KURALLARI = [
    (["review of manuscript", "thank you for submitting your review", "thank you for the review",
      "thanks for undertaking the review", "hakemlik", "scholarone"], "HAKEM_Hakemlikler"),
    (["ders tanim", "verilendersler", "verilen dersler"], "DERS_Verilen_Dersler"),
    (["bap gorevlendirme"], "PROJE_BAP"),
    (["komisyon", "oturumbaskanligi", "oturum baskanligi", "duzenlemekurulu", "duzenleme kurulu"],
     "IDARI_Gorevler"),
    (["diploma"], "_Kisisel_Belgeler"),
]
BAGLAC = set("with from using based that this into their approach method methods novel new "
             "analysis images image ile icin olarak yontemi yontemleri kullanarak".split())
TAM_METIN_DISI = ("katilim", "certificate", "sertifika", "belgesi", "master journal",
                  "journal search", "citations of", "dizin", "indeks", "program")


@dataclass
class PlanSatiri:
    kaynak: Path
    hedef: Path
    ad: str
    gerekce: str
    durum: str = "plan"


def kurallari_oku(kok: Path) -> dict:
    yol = Path(kok) / KURAL_DOSYASI
    return json.loads(yol.read_text(encoding="utf-8")) if yol.exists() else {}


def _anahtar(baslik):
    return [w for w in dict.fromkeys(norm(baslik).split()) if len(w) > 3 and w not in BAGLAC]


class Eslestirici:
    def __init__(self, arsiv: KanitArsivi, kurallar: dict | None = None):
        self.arsiv = arsiv
        self.kurallar = kurallar or {}
        self.faal = {}
        for k in arsiv.kayitlar:
            if not k.aves_kod:
                continue
            basliklar = [ay.baslik_cikar(k.kunye)] + \
                self.kurallar.get("diger_basliklar", {}).get(k.aves_kod, [])
            gramlar = []
            for b in basliklar:
                w = norm(b).split()
                n = 3 if len(w) >= 5 else 2
                gramlar.append([" ".join(w[i:i + n]) for i in range(len(w) - n + 1)] or [" ".join(w)])
            self.faal[k.aves_kod] = {"kayit": k, "basliklar": basliklar,
                                     "anahtarlar": [_anahtar(b) for b in basliklar],
                                     "gramlar": gramlar}

    # ── puanlama ────────────────────────────────────────────────────────────
    def puanla(self, metin, izinli=None):
        m = " " + norm(metin) + " "
        sonuc = sorted(((max(sum(f" {g} " in m for g in gr) / len(gr) for gr in f["gramlar"]), kod)
                        for kod, f in self.faal.items() if not izinli or kod[:2] in izinli),
                       reverse=True)
        if not sonuc:
            return None, 0, 0
        return sonuc[0][1], sonuc[0][0], sonuc[1][0] if len(sonuc) > 1 else 0

    def _ad_puanla(self, ad, izinli=None):
        kel = [w for w in _anahtar(ad) if not w.isdigit() and w not in
               ("makale", "trdizin", "indeks", "diger", "fireshot", "capture", "citations",
                "webofscience")]
        if len(kel) < 3:
            return None, 0, 0
        sonuc = []
        for kod, f in self.faal.items():
            if izinli and kod[:2] not in izinli:
                continue
            kume = {w for a in f["anahtarlar"] for w in a}
            say = sum(w in kume for w in kel[:-1]) + any(k.startswith(kel[-1]) for k in kume)
            sonuc.append((say / len(kel), kod))
        sonuc.sort(reverse=True)
        return sonuc[0][1], sonuc[0][0], sonuc[1][0] if len(sonuc) > 1 else 0

    def onek_eslesme(self, ad):
        """WoS 'Citations of <başlığın başı>_ - [..]' gibi kesilmiş başlıklar."""
        m = re.search(r"Citations of (.+?)_? - \[", ad)
        if not m or len(norm(m.group(1))) < 25:
            return None
        on = norm(m.group(1))
        kodlar = {k for k, f in self.faal.items() for b in f["basliklar"] if norm(b).startswith(on)}
        return kodlar.pop() if len(kodlar) == 1 else None

    def ad_eslesme(self, ad, izinli=None):
        if kod := self.onek_eslesme(ad):
            return kod
        kod, p, p2 = self._ad_puanla(ad, izinli)
        if kod and p >= 0.99 and p - p2 >= 0.15:
            return kod
        kod, p, p2 = self.puanla(ad, izinli)
        return kod if p >= 0.8 and p - p2 >= 0.25 else None

    def ilk_sayfa_eslesme(self, yol: Path, izinli=None):
        if yol.suffix.lower() != ".pdf":
            return None
        kod, p, p2 = self.puanla(pdf_metin(yol)[:6000], izinli)
        return kod if p >= 0.8 and p - p2 >= 0.25 else None

    def atif_yapilan_eserler(self, yol: Path):
        m = " " + norm(pdf_metin(yol, tumu=True)[-120000:]) + " "
        return [kod for kod, f in self.faal.items()
                if max(sum(f" {g} " in m for g in gr) / len(gr) for gr in f["gramlar"]) >= 0.8]


def _tur_ipucu(t):
    t = norm(t)
    return {"UB", "NB"} if "bildiri" in t else ({"UM", "UL"} if "makale" in t else None)


def _ozel_hedef(ad):
    n = norm(ad)
    for anahtar, hedef in OZEL_KLASOR.items():
        if n.endswith(anahtar) or anahtar in n.split("yayin no")[-1]:
            return hedef
    return None


def _dosya_kurali(ad):
    n = norm(ad)
    return next((h for ifadeler, h in DOSYA_KURALLARI if any(norm(i) in n for i in ifadeler)), None)


def _etiket(kaynak, klasor):
    return f"{kaynak}_{re.sub(r'[^A-Za-z0-9ÇĞİÖŞÜçğıöşü() -]+', '', klasor.name)[:60].strip()}"


def plan_olustur(arsiv: KanitArsivi, kaynaklar: dict[str, Path],
                 kurallar: dict | None = None) -> list[PlanSatiri]:
    """Kaynak klasörlerdeki dosyaların nereye kopyalanacağını planlar (kopyalamaz)."""
    kurallar = kurallar if kurallar is not None else kurallari_oku(arsiv.kok)
    e = Eslestirici(arsiv, kurallar)
    elle_klasor = kurallar.get("elle_klasor", {})
    elle_yer = kurallar.get("elle_yer", {})
    atla = set(kurallar.get("atla", []))
    hedef_kok = arsiv.kok
    plan: list[PlanSatiri] = []

    def faal_klasor(kod):
        return e.faal[kod]["kayit"].klasor

    def ekle(src, hedef, gerekce, ad=None):
        plan.append(PlanSatiri(src, hedef, ad or src.name, gerekce))

    def elle(f, kaynak, klasor):
        for y in elle_yer[f.name]:
            h = (faal_klasor(y) / "arsiv") if y in e.faal else hedef_kok / y
            ekle(f, h / _etiket(kaynak, klasor), f"elle → {y}")

    for kaynak, kok in kaynaklar.items():
        kok = Path(kok)
        klasorler = defaultdict(list)
        for f in kok.rglob("*"):
            if f.is_file() and f.name not in atla:
                klasorler[f.parent].append(f)
        for klasor, dosyalar in sorted(klasorler.items()):
            rel = klasor.relative_to(kok)
            rel_n = norm(str(rel))
            if o := _ozel_hedef(klasor.name):
                for f in dosyalar:
                    ekle(f, hedef_kok / o / _etiket(kaynak, klasor), f"özel → {o}")
                continue
            if "atif" in rel_n or "citations" in rel_n or "web of science da olmayan" in rel_n:
                if norm(klasor.name) in ("atiflar", "sci web of science da olmayan"):
                    for f in dosyalar:
                        if f.name in elle_yer:
                            elle(f, kaynak, klasor); continue
                        kod = e.ad_eslesme(f.name) or e.ilk_sayfa_eslesme(f)
                        kodlar = [kod] if kod else (e.atif_yapilan_eserler(f)
                                                    if f.suffix.lower() == ".pdf" else [])
                        for k in kodlar:
                            ekle(f, faal_klasor(k) / "atiflar" / _etiket(kaynak, klasor),
                                 f"atıf dosyası → {k}")
                        if not kodlar:
                            ekle(f, hedef_kok / "_Eslesmeyen_Dosyalar" / kaynak / rel, "eşleşmedi")
                    continue
                if _atif_klasoru(e, plan, kaynak, klasor, dosyalar, hedef_kok):
                    continue
            if klasor != kok and _yayin_klasoru(e, plan, kaynak, klasor, dosyalar,
                                                 _tur_ipucu(str(rel)), elle_klasor):
                continue
            for f in dosyalar:
                if f.name in elle_yer:
                    elle(f, kaynak, klasor); continue
                kod = e.ilk_sayfa_eslesme(f) or e.ad_eslesme(f.stem)
                if not kod and (o := _dosya_kurali(f.name)):
                    ekle(f, hedef_kok / o / _etiket(kaynak, klasor), f"dosya adı → {o}")
                elif kod:
                    ekle(f, faal_klasor(kod) / "arsiv" / _etiket(kaynak, klasor), f"dosya → {kod}")
                elif klasor == kok:
                    ekle(f, hedef_kok / "_Genel_Belgeler" / kaynak, "genel belge")
                else:
                    ekle(f, hedef_kok / "_Eslesmeyen_Dosyalar" / kaynak / rel, "eşleşmedi")

    _tam_metin_plani(e, plan)
    return plan


def _atif_klasoru(e: Eslestirici, plan, kaynak, klasor, dosyalar, hedef_kok):
    pdfs = [f for f in dosyalar if f.suffix.lower() == ".pdf"]
    atif_yapilan = {f: e.ilk_sayfa_eslesme(f) for f in pdfs}
    kodlar = {k for k in atif_yapilan.values() if k}
    if not kodlar:
        for ust in (klasor, klasor.parent):
            if k := e.ad_eslesme(re.sub(r"^\d+\s*-\s*", "", ust.name)):
                kodlar = {k}
                break
    if not kodlar:
        for f in pdfs:
            if "master journal" not in f.name.lower():
                kodlar.update(e.atif_yapilan_eserler(f))
    if not kodlar:
        if any("tez" in norm(pdf_metin(f, 1)[:600]) for f in pdfs):
            for f in dosyalar:
                plan.append(PlanSatiri(f, hedef_kok / "TEZ_Lisansustu_Tez_Atiflari" /
                                       _etiket(kaynak, klasor), f.name, "atıf → lisansüstü tez"))
            return True
        return False
    for kod in sorted(kodlar):
        h = e.faal[kod]["kayit"].klasor / "atiflar" / _etiket(kaynak, klasor)
        for f in dosyalar:
            if atif_yapilan.get(f) != kod:     # atıf yapılan eserin kendisi eklenmez
                plan.append(PlanSatiri(f, h, f.name, f"atıf → {kod}"))
    return True


def _yayin_klasoru(e: Eslestirici, plan, kaynak, klasor, dosyalar, izinli, elle_klasor):
    kod = elle_klasor.get(klasor.name) or e.ad_eslesme(klasor.name, izinli)
    if not kod:
        oylar = Counter(k for f in dosyalar if (k := e.ilk_sayfa_eslesme(f, izinli)))
        kod = oylar.most_common(1)[0][0] if len(oylar) == 1 else None   # karışık klasör → tek tek
    if not kod or kod not in e.faal:
        return False
    h = e.faal[kod]["kayit"].klasor / "arsiv" / _etiket(kaynak, klasor)
    for f in dosyalar:
        plan.append(PlanSatiri(f, h, f.name, f"yayın klasörü → {kod}"))
    return True


def _tam_metin_mi(yol: Path) -> bool:
    if yol.suffix.lower() != ".pdf" or any(x in norm(yol.name) for x in TAM_METIN_DISI):
        return False
    import fitz
    try:
        return fitz.open(yol).page_count >= 4
    except Exception:
        return False


def _tam_metin_plani(e: Eslestirici, plan: list[PlanSatiri]):
    """Tam metni olmayan yayınlara, eşleşen en uzun PDF'i tam_metin.pdf olarak koyar;
    aynı dosyanın arsiv\\ kopyası plandan çıkarılır (iki kez eklenmez)."""
    adaylar = defaultdict(list)
    for s in plan:
        kod = s.gerekce.split("→ ")[-1]
        if s.gerekce.startswith(("atıf", "elle")) or kod not in e.faal:
            continue
        if _tam_metin_mi(s.kaynak) and e.ilk_sayfa_eslesme(s.kaynak) == kod:
            adaylar[kod].append(s)
    import fitz
    for kod, satirlar in adaylar.items():
        klasor = e.faal[kod]["kayit"].klasor
        if e.faal[kod]["kayit"].tam_metin:
            continue
        secilen = max(satirlar, key=lambda s: fitz.open(s.kaynak).page_count)
        secilen.hedef, secilen.ad, secilen.gerekce = klasor, "tam_metin.pdf", f"tam metin → {kod}"


def uygula(arsiv: KanitArsivi, plan: list[PlanSatiri], onceki: list[Path] = (),
           kopyala: bool = True, kayit_csv: Path | None = None) -> Counter:
    """Planı uygular. Hedefte ya da `onceki` kaynaklarda aynı içerik varsa eklenmez."""
    onceden = set()
    for kok in [arsiv.kok, *map(Path, onceki)]:
        onceden |= {md5(p) for p in kok.rglob("*") if p.is_file()}
    sayac = Counter()
    klasor_hash = defaultdict(set)
    bu_calisma = set()
    for s in plan:
        kok = s.hedef
        while kok.parent != arsiv.kok and kok != arsiv.kok:
            kok = kok.parent
        h = md5(s.kaynak)
        if s.ad == "tam_metin.pdf" and not (s.hedef / s.ad).exists():
            karar = "eklenir"
        elif h in onceden:
            karar = "aynısı zaten var"
        elif h in klasor_hash[kok]:
            karar = "aynısı bu klasöre eklendi"
        elif h in bu_calisma and not s.gerekce.startswith(("atıf", "elle")):
            karar = "aynısı başka klasöre eklendi"
        else:
            karar = "eklenir"
        sayac[karar] += 1
        s.durum = karar
        if karar == "eklenir":
            klasor_hash[kok].add(h)
            bu_calisma.add(h)
            if kopyala:
                s.hedef.mkdir(parents=True, exist_ok=True)
                hedef = s.hedef / s.ad
                i = 2
                while hedef.exists():
                    hedef = s.hedef / f"{Path(s.ad).stem}_{i}{Path(s.ad).suffix}"
                    i += 1
                shutil.copy2(s.kaynak, hedef)
                s.durum = "kopyalandı"
    if kayit_csv:
        with open(kayit_csv, "w", newline="", encoding="utf-8-sig") as fp:
            w = csv.writer(fp, delimiter=";")
            w.writerow(["Kaynak dosya", "Hedef klasör", "Hedef ad", "Gerekçe", "Durum"])
            for s in plan:
                w.writerow([s.kaynak, s.hedef, s.ad, s.gerekce, s.durum])
    return sayac
