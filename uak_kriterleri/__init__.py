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
    # Dergi kuartiline göre puan, örn. (("Q1", 30), ("Q2", 20), …); Q girilmemişse en düşük
    q_puanlari: tuple[tuple[str, float], ...] = ()
    # Eşik kalemi: faaliyet adedi bu eşiğe ulaşırsa bir kez `puan` (örn. h-indeks ≥ 5)
    esik_adet: int = 0
    # Yalnızca bu patent durumları ("tescilli", "arastirma_raporu", "basvuru")
    patent_durumlari: tuple[str, ...] = ()
    # Yalnızca başarıyla tamamlanmış projeler (Faaliyet.devam_ediyor değilse)
    tamamlanmis: bool = False


@dataclass(frozen=True)
class AltKosul:
    """Bölüm içindeki belirli kalemler için asgari puan şartı."""
    aciklama: str
    kalemler: tuple[str, ...]
    min_puan: float
    baslica_yazar_gerekli: bool = False  # en az bir eserde başlıca yazar
    baslica_q: tuple[str, ...] = ()      # başlıca yazarlık bu kuartillerde aranır (örn. Q1–Q3)
    doktora_sonrasi: bool = False        # yalnızca doktora sonrası çalışmalardan


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
    # Bölümdeki belirli kalemlerin toplam üst sınırı: ((("4c", "4d"), 5), …)
    alt_sinirlar: tuple[tuple[tuple[str, ...], float], ...] = ()
    # min_yayin yalnızca bu kalemlerden sayılır (boşsa tüm kalemler)
    min_yayin_kalemleri: tuple[str, ...] = ()
    # Eğitim puanı ders sayısından: dönemlik ≥4 farklı yarıyıl → 2, yıllık ≥2 yıl → 2
    egitim_sayimi: bool = False


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
    # Başlıca yazar tanımı makalenin ilk yazarını da kapsar (2018 öncesi dönemler)
    ilk_yazar_baslica: bool = False
    # "Doktora sonrası ≥ X puan" hesabına girmeyen bölümler (örn. tezden üretilmiş yayınlar)
    doktora_sonrasi_haric: tuple[int, ...] = ()
    # Puan yerine koşul aranan eski dönemler: toplam_min yayın adedidir
    kosul_sistemi: bool = False

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


def _baslica_mi(f, kset: Optional["KriterSeti"] = None) -> Optional[bool]:
    if f.toplam_yazar <= 1:
        return True
    if kset is not None and kset.ilk_yazar_baslica and getattr(f, "yazar_sirasi", 0) == 1:
        return True
    return getattr(f, "uak_baslica_yazar", None)


def kalem_bul(kset: KriterSeti, f) -> Optional[tuple[Bolum, Kalem]]:
    """Faaliyetin eşlendiği (bölüm, kalem) çiftini döndürür; yoksa None."""
    tezden = bool(getattr(f, "tezden_uretilmis", False))
    zorunlu = getattr(f, "uak_kalem", "")
    for b in kset.bolumler:
        for k in b.kalemler:
            if zorunlu:
                if k.kod == zorunlu:
                    return b, k
                continue
            if f.kod not in k.ek2_kodlari:
                continue
            if k.tez is not None and k.tez != tezden:
                continue
            if k.patent_raporlu and f.patent_durum not in (None, "tescilli",
                                                          "arastirma_raporu"):
                continue
            if k.patent_durumlari and (f.patent_durum or "tescilli") not in k.patent_durumlari:
                continue
            if k.tamamlanmis and getattr(f, "devam_ediyor", False):
                continue
            return b, k
    return None


def _pay(k: Kalem, f, kset: Optional["KriterSeti"] = None) -> float:
    if k.yazar_dagilimi == "makale":
        return makale_yazar_payi(f.toplam_yazar, _baslica_mi(f, kset))
    if k.yazar_dagilimi == "esit":
        return 1.0 / max(1, f.toplam_yazar)
    return 1.0


def _kalem_puani(k: Kalem, f) -> float:
    """Kalemin bir faaliyet için birim puanı (Q'ya göre ya da sabit)."""
    if k.q_puanlari:
        tablo = dict(k.q_puanlari)
        return tablo.get(getattr(f, "q_degeri", None) or "", min(tablo.values()))
    return k.puan


def _doktora_sonrasi_mi(f, doktora_tarihi) -> bool:
    """Doktora tarihi bilinmiyorsa ya da faaliyet tarihsizse (örn. atıf satırları) sayılır."""
    t = getattr(f, "yayin_tarihi", None)
    return doktora_tarihi is None or t is None or t > doktora_tarihi


def degerlendir(kset: KriterSeti, faaliyetler: list, *,
                egitim_yari_yil: int = 0, egitim_yil: int = 0,
                profesorluk: bool = True, doktora_tarihi=None) -> dict:
    """
    Faaliyetleri kriter setine göre puanlar ve koşulları denetler.

    faaliyetler      Değerlendirmeye girecek faaliyetler (profesörlükte:
                     doçentlik başvurusu sonrası olanlar).
    egitim_yari_yil  Farklı yarıyıl ders sayısı (≥4 → "2 yıl eğitim" kuralı).
    egitim_yil       Yıllık programlarda ders verilen farklı yıl sayısı.
    profesorluk      True → Md. 11(2) istisnası uygulanır ve tüm faaliyetler
                     doçentlik başvurusu sonrası (dolayısıyla doktora sonrası)
                     kabul edilir. False → doçentliğe başvuru ön kontrolü:
                     doktora sonrası şartları `doktora_tarihi`ne göre denetlenir.
    """
    satirlar, eslesmeyen = [], []
    for f in faaliyetler:
        bk = kalem_bul(kset, f)
        if bk is None:
            eslesmeyen.append(f)
            continue
        b, k = bk
        pay = _pay(k, f, kset)
        danisman = 0.5 if (k.ikinci_danisman_yarim
                           and getattr(f, "ikinci_danisман", False)) else 1.0
        birim = _kalem_puani(k, f)
        if k.esik_adet:
            puan = birim if f.adet >= k.esik_adet else 0.0
        else:
            puan = birim * pay * danisman * f.adet
        satirlar.append({
            "faaliyet": f, "bolum": b.no, "kalem": k.kod, "kalem_ad": k.ad,
            "kalem_puan": birim, "adet": f.adet, "pay": pay,
            "danisman_carpani": danisman, "puan": round(puan, 2),
            "doktora_sonrasi": profesorluk or _doktora_sonrasi_mi(f, doktora_tarihi),
        })

    bolum_sonuclari, kontroller = [], []

    def kontrol(kriter: str, saglandi: bool, notlar: str = ""):
        kontroller.append({"kriter": kriter, "saglandi": saglandi,
                           "notlar": notlar})

    def bolum_puani(b: Bolum, bs: list) -> tuple[float, float]:
        ham = sum(s["puan"] for s in bs)
        puan = ham
        for kalemler, ust in b.alt_sinirlar:
            alt = sum(s["puan"] for s in bs if s["kalem"] in kalemler)
            puan -= max(0.0, alt - ust)
        if b.egitim_sayimi:
            puan += (2 if egitim_yari_yil >= 4 else 0) + (2 if egitim_yil >= 2 else 0)
        if b.iki_yil_egitim_puani and (egitim_yari_yil >= 4 or egitim_yil >= 2):
            puan = max(puan, b.iki_yil_egitim_puani)
        if b.max_puan is not None:
            puan = min(puan, b.max_puan)
        return round(ham, 2), round(puan, 2)

    toplam = 0.0
    doktora_sonrasi_toplam = 0.0
    for b in kset.bolumler:
        bs = [s for s in satirlar if s["bolum"] == b.no]
        ham, puan = bolum_puani(b, bs)
        toplam += puan
        if b.no not in kset.doktora_sonrasi_haric:
            doktora_sonrasi_toplam += bolum_puani(b, [s for s in bs if s["doktora_sonrasi"]])[1]
        bolum_sonuclari.append({
            "no": b.no, "ad": b.ad, "ham": ham, "puan": puan,
            "min": b.min_puan, "max": b.max_puan, "adet": len(bs),
            "elle_kontrol": b.elle_kontrol,
        })

        if b.min_puan:
            kontrol(f"{b.no}. {b.ad} ≥{b.min_puan:g} puan",
                    puan >= b.min_puan, f"Puan: {puan:g}")
        if b.min_yayin:
            yayin = sum(s["adet"] for s in bs
                        if not b.min_yayin_kalemleri or s["kalem"] in b.min_yayin_kalemleri)
            if profesorluk and b.profesorlukte_aranmaz:
                kontrol(f"{b.no}. {b.ad} en az {b.min_yayin} yayın", True,
                        "Md. 11(2) gereği profesörlükte aranmaz")
            else:
                kontrol(f"{b.no}. {b.ad} en az {b.min_yayin} yayın",
                        yayin >= b.min_yayin, f"Yayın: {yayin}")
        for ak in b.alt_kosullar:
            aks = [s for s in bs if s["kalem"] in ak.kalemler
                   and (not ak.doktora_sonrasi or s["doktora_sonrasi"])]
            ak_puan = round(sum(s["puan"] for s in aks), 2)
            notlar = f"Puan: {ak_puan:g}"
            ok = ak_puan >= ak.min_puan
            if ak.baslica_yazar_gerekli:
                baslica = any(_baslica_mi(s["faaliyet"], kset) and (
                    not ak.baslica_q or getattr(s["faaliyet"], "q_degeri", None) in ak.baslica_q)
                    for s in aks)
                ok = ok and baslica
                notlar += ("; başlıca yazar olunan makale var" if baslica
                           else "; başlıca yazar olunan makale yok"
                           + (f" ({'/'.join(ak.baslica_q)})" if ak.baslica_q else ""))
            kontrol(ak.aciklama, ok, notlar)

    toplam = round(toplam, 2)
    if kset.kosul_sistemi:
        kontrol(f"En az {kset.toplam_min:g} makale", toplam >= kset.toplam_min,
                f"Makale: {toplam:g}")
    else:
        kontrol(f"Toplam ≥{kset.toplam_min:g} puan", toplam >= kset.toplam_min,
                f"Toplam: {toplam:g}")
    if kset.doktora_sonrasi_min and not kset.kosul_sistemi:
        if profesorluk:
            kontrol(f"Doktora sonrası çalışmalardan ≥{kset.doktora_sonrasi_min:g} puan",
                    doktora_sonrasi_toplam >= kset.doktora_sonrasi_min,
                    "Doçentlik başvurusu sonrası çalışmaların tamamı doktora sonrasıdır")
        else:
            kontrol(f"Doktora sonrası çalışmalardan ≥{kset.doktora_sonrasi_min:g} puan",
                    doktora_sonrasi_toplam >= kset.doktora_sonrasi_min,
                    f"Doktora sonrası: {round(doktora_sonrasi_toplam, 2):g}"
                    + ("" if doktora_tarihi else " (doktora tarihi girilmedi: tümü sayıldı)"))

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
from . import mart_2022, muhendislik_donemleri  # noqa: E402,F401
