"""
ÜAK doçentlik başvuru kriterleri – değerlendirme motoru ve kayıt defteri.

EYS-YNG-129 Md. 11(2): Profesörlük adayı, doçent unvanını almaya esas olan
doçentlik başvuru dönemindeki ÜAK kriterlerini (lisansüstü tezlerden üretilmiş
yayın yapma şartı hariç) doçentlik başvurusu sonrası çalışmalarıyla yeniden
sağlamış olmalıdır.

Her ÜAK dönemi / temel alan bir `KriterSeti` olarak tanımlanır. Setler bu
paketteki dönem dosyalarında (örn. `mart_2022.py`) yazılır ve `kaydet()` ile
kayıt defterine eklenir. Motor, adayın EK-2 faaliyetlerini her kalemin
`ek2_kodlari` listesine göre ÜAK kalemlerine eşler.

YENİ BİR KRİTER SETİ EKLEMEK
  1. Bu klasörde dönem dosyası oluşturun (örn. `ekim_2023.py`) ya da mevcut
     dönem dosyasına yeni temel alanı ekleyin (`mart_2022.py` örnek alınabilir).
  2. `KriterSeti(...)` tanımlayıp `kaydet(...)` çağırın.
  3. Yeni dosyaysa bu dosyanın en altındaki içe aktarma listesine ekleyin.
  4. `tests/test_uak_kriterleri.py` içine en az bir test yazın.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


# ─────────────────────────────────────────────────────────────────────────────
# Tanım yapıları
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Kalem:
    """ÜAK tablosundaki tek bir puanlı satır (örn. 1a)."""
    kod: str                      # "1a"
    ad: str
    puan: float
    ek2_kodlari: tuple[str, ...]  # bu kaleme eşlenen EK-2 faaliyet kodları
    # Lisansüstü tezden üretilmiş olma koşulu:
    #   True → yalnızca tezden üretilmiş, False → yalnızca üretilmemiş, None → fark etmez
    tez: Optional[bool] = False
    # Puanın yazarlar arasında paylaşımı:
    #   "makale" → ÜAK makale kuralı (başlıca yazar), "esit" → kişi sayısına eşit,
    #   "yok" → paylaştırılmaz
    yazar_dagilimi: str = "yok"
    # Yalnızca tescilli veya araştırma raporu almış patentler (ÜAK patent tanımı)
    patent_raporlu: bool = False
    # İkinci / eş danışman yarı puan alır
    ikinci_danisman_yarim: bool = False


@dataclass(frozen=True)
class AltKosul:
    """Bölüm içindeki belirli kalemler için asgari puan şartı."""
    aciklama: str
    kalemler: tuple[str, ...]
    min_puan: float
    baslica_yazar_gerekli: bool = False  # en az bir eserde başlıca yazar


@dataclass(frozen=True)
class Bolum:
    """ÜAK tablosundaki numaralı bölüm (örn. "1. Makaleler")."""
    no: int
    ad: str
    kalemler: tuple[Kalem, ...]
    min_puan: float = 0
    max_puan: Optional[float] = None
    min_yayin: int = 0                    # en az yayın adedi
    profesorlukte_aranmaz: bool = False   # min_yayin, Md. 11(2) istisnası
    alt_kosullar: tuple[AltKosul, ...] = ()
    # "En az 2 yıl eğitim-öğretim faaliyetinde bulunanlar X puan almış sayılır"
    iki_yil_egitim_puani: float = 0
    # Programın denetleyemediği, elle kontrol edilmesi gereken kurallar
    elle_kontrol: tuple[str, ...] = ()


@dataclass(frozen=True)
class KriterSeti:
    kimlik: str               # "2022-mart/muhendislik"
    donem: str                # "Mart 2022"
    temel_alan: str           # "Mühendislik"
    tablo: str                # "Tablo 9"
    kosul_no: str             # "91"
    toplam_min: float
    doktora_sonrasi_min: float
    bolumler: tuple[Bolum, ...]
    kaynak: str = ""

    @property
    def ad(self) -> str:
        return (f"ÜAK {self.donem} – {self.temel_alan} "
                f"({self.tablo}, koşul {self.kosul_no})")


# ─────────────────────────────────────────────────────────────────────────────
# Kayıt defteri
# ─────────────────────────────────────────────────────────────────────────────

_SETLER: dict[str, KriterSeti] = {}


def kaydet(kset: KriterSeti) -> KriterSeti:
    if kset.kimlik in _SETLER:
        raise ValueError(f"Kriter seti iki kez tanımlandı: {kset.kimlik}")
    kodlar = [k.kod for b in kset.bolumler for k in b.kalemler]
    if len(kodlar) != len(set(kodlar)):
        raise ValueError(f"{kset.kimlik}: kalem kodları tekrarlanıyor")
    _SETLER[kset.kimlik] = kset
    return kset


def getir(kimlik: str) -> KriterSeti:
    try:
        return _SETLER[kimlik]
    except KeyError:
        raise KeyError(f"Tanımlı olmayan ÜAK kriter seti: {kimlik!r}") from None


def setler() -> list[KriterSeti]:
    return list(_SETLER.values())


# ─────────────────────────────────────────────────────────────────────────────
# Değerlendirme
# ─────────────────────────────────────────────────────────────────────────────

def makale_yazar_payi(toplam_yazar: int, baslica: Optional[bool]) -> float:
    """ÜAK makale puan paylaşımı.

    Tek yazarlı: tam puan. İki yazarlı: başlıca 0.8, diğer 0.5.
    Üç ve daha fazla: başlıca 0.5, diğerleri kalan yarıyı eşit paylaşır.
    Başlıca yazar belirtilmemişse (baslica=None) puan eşit bölünür.
    """
    n = max(1, toplam_yazar)
    if n == 1:
        return 1.0
    if baslica is None:
        return 1.0 / n
    if n == 2:
        return 0.8 if baslica else 0.5
    return 0.5 if baslica else 0.5 / (n - 1)


def _baslica_mi(f) -> Optional[bool]:
    if f.toplam_yazar <= 1:
        return True
    return getattr(f, "uak_baslica_yazar", None)


def kalem_bul(kset: KriterSeti, f) -> Optional[tuple[Bolum, Kalem]]:
    """Faaliyetin eşlendiği (bölüm, kalem) çiftini döndürür; yoksa None."""
    tezden = bool(getattr(f, "tezden_uretilmis", False))
    for b in kset.bolumler:
        for k in b.kalemler:
            if f.kod not in k.ek2_kodlari:
                continue
            if k.tez is not None and k.tez != tezden:
                continue
            if k.patent_raporlu and f.patent_durum not in (None, "tescilli",
                                                          "arastirma_raporu"):
                continue
            return b, k
    return None


def _pay(k: Kalem, f) -> float:
    if k.yazar_dagilimi == "makale":
        return makale_yazar_payi(f.toplam_yazar, _baslica_mi(f))
    if k.yazar_dagilimi == "esit":
        return 1.0 / max(1, f.toplam_yazar)
    return 1.0


def degerlendir(kset: KriterSeti, faaliyetler: list, *,
                egitim_yari_yil: int = 0, profesorluk: bool = True) -> dict:
    """
    Faaliyetleri kriter setine göre puanlar ve koşulları denetler.

    faaliyetler      Değerlendirmeye girecek faaliyetler (profesörlükte:
                     doçentlik başvurusu sonrası olanlar).
    egitim_yari_yil  Farklı yarıyıl ders sayısı (≥4 → "2 yıl eğitim" kuralı).
    profesorluk      True → Md. 11(2) istisnası uygulanır ve tüm faaliyetler
                     doçentlik başvurusu sonrası (dolayısıyla doktora sonrası)
                     kabul edilir.
    """
    satirlar, eslesmeyen = [], []
    for f in faaliyetler:
        bk = kalem_bul(kset, f)
        if bk is None:
            eslesmeyen.append(f)
            continue
        b, k = bk
        pay = _pay(k, f)
        danisman = 0.5 if (k.ikinci_danisman_yarim
                           and getattr(f, "ikinci_danisман", False)) else 1.0
        satirlar.append({
            "faaliyet": f, "bolum": b.no, "kalem": k.kod, "kalem_ad": k.ad,
            "kalem_puan": k.puan, "adet": f.adet, "pay": pay,
            "danisman_carpani": danisman,
            "puan": round(k.puan * pay * danisman * f.adet, 2),
        })

    bolum_sonuclari, kontroller = [], []

    def kontrol(kriter: str, saglandi: bool, notlar: str = ""):
        kontroller.append({"kriter": kriter, "saglandi": saglandi,
                           "notlar": notlar})

    toplam = 0.0
    for b in kset.bolumler:
        bs = [s for s in satirlar if s["bolum"] == b.no]
        ham = sum(s["puan"] for s in bs)
        puan = ham
        if b.iki_yil_egitim_puani and egitim_yari_yil >= 4:
            puan = max(puan, b.iki_yil_egitim_puani)
        if b.max_puan is not None:
            puan = min(puan, b.max_puan)
        puan = round(puan, 2)
        toplam += puan
        bolum_sonuclari.append({
            "no": b.no, "ad": b.ad, "ham": round(ham, 2), "puan": puan,
            "min": b.min_puan, "max": b.max_puan, "adet": len(bs),
            "elle_kontrol": b.elle_kontrol,
        })

        if b.min_puan:
            kontrol(f"{b.no}. {b.ad} ≥{b.min_puan:g} puan",
                    puan >= b.min_puan, f"Puan: {puan:g}")
        if b.min_yayin:
            yayin = sum(s["adet"] for s in bs)
            if profesorluk and b.profesorlukte_aranmaz:
                kontrol(f"{b.no}. {b.ad} en az {b.min_yayin} yayın", True,
                        "Md. 11(2) gereği profesörlükte aranmaz")
            else:
                kontrol(f"{b.no}. {b.ad} en az {b.min_yayin} yayın",
                        yayin >= b.min_yayin, f"Yayın: {yayin}")
        for ak in b.alt_kosullar:
            aks = [s for s in bs if s["kalem"] in ak.kalemler]
            ak_puan = round(sum(s["puan"] for s in aks), 2)
            notlar = f"Puan: {ak_puan:g}"
            ok = ak_puan >= ak.min_puan
            if ak.baslica_yazar_gerekli:
                baslica = any(_baslica_mi(s["faaliyet"]) for s in aks)
                ok = ok and baslica
                notlar += ("; başlıca yazar olunan makale var" if baslica
                           else "; başlıca yazar olunan makale yok")
            kontrol(ak.aciklama, ok, notlar)

    toplam = round(toplam, 2)
    kontrol(f"Toplam ≥{kset.toplam_min:g} puan", toplam >= kset.toplam_min,
            f"Toplam: {toplam:g}")
    if profesorluk:
        kontrol(f"Doktora sonrası çalışmalardan ≥{kset.doktora_sonrasi_min:g} puan",
                toplam >= kset.doktora_sonrasi_min,
                "Doçentlik başvurusu sonrası çalışmaların tamamı doktora sonrasıdır")

    return {
        "set": kset,
        "satirlar": satirlar,
        "bolumler": bolum_sonuclari,
        "toplam": toplam,
        "kontroller": kontroller,
        "eslesmeyen": eslesmeyen,
        "saglandi": all(k["saglandi"] for k in kontroller),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Dönem tanımları (yeni dönem dosyalarını buraya ekleyin)
# ─────────────────────────────────────────────────────────────────────────────
from . import mart_2022  # noqa: E402,F401
