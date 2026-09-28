"""
AVES aktarımı için saf (Streamlit'ten bağımsız) yardımcılar.

- AVES kodu: faaliyetin AVES'teki bölümü ve sırası (UM01, UB03 …); kanıt
  klasörleri de aynı kodlarla adlandırılır.
- Kitap / kitap bölümü ayrımı: AVES'in "Uluslararası Kitaplar veya Kitap
  Bölümleri" başlığı her ikisini içerir; künyede "Bölüm:" geçen kayıt bölümdür.
- Tekrar ayıklama: AVES'te aynı eser iki kez kayıtlı olabilir (örn. ortak
  yazarın soyadı değişince). Aynı başlık + yıl + sayfa → tek faaliyet.
"""

from __future__ import annotations

import re
import unicodedata

# AVES bölüm anahtarı → kod öneki
AVES_ONEK = {
    "ulusl_makale": "UM",     # Uluslararası hakemli dergi makalesi
    "ulusal_makale": "UL",    # Ulusal hakemli dergi makalesi
    "kitap_ulusl": "KB",      # Uluslararası kitap / kitap bölümü
    "kitap_ulusal": "KB",
    "kitap_bolum": "KB",
    "ulusl_bildiri": "UB",    # Uluslararası bildiri
    "ulusal_bildiri": "NB",   # Ulusal (national) bildiri
}


def aves_kodu(kat_key: str, sira: int) -> str:
    """AVES bölümü ve bölüm içindeki sırası (1'den başlar) → 'UM01'."""
    onek = AVES_ONEK.get(kat_key)
    return f"{onek}{sira:02d}" if onek else ""


def kitap_ek2_kodu(kat_key: str, metin: str, tip: str = "") -> str:
    """Kitap kaydının EK-2 kodu (AVES türü "tip" varsa ona göre).

    Bölüm: uluslararası → 2.5, ulusal → 2.6 (BKCI kapsamındaysa kullanıcı 2.4'e
    çevirebilir). Kitap: uluslararası → 2.2, ulusal → 2.3.
    Kitap Tercümesi → 2.9–2.12, Ansiklopedi Maddesi → 3.9/3.10,
    Ders Kitabı → 2.7 (yabancı üniversite) / 2.8 (ulusal üniversite).
    """
    bolum = "bolum" in kat_key or bool(re.search(r"Bölüm\s*:", metin))
    uluslararasi = "ulusl" in kat_key
    t = _norm(tip)
    if "tercume" in t or "ceviri" in t:
        if bolum:
            return "2.10" if uluslararasi else "2.12"
        return "2.9" if uluslararasi else "2.11"
    if "ansiklopedi" in t:
        return "3.9" if uluslararasi else "3.10"
    if "ders kitabi" in t and not bolum:
        return "2.7" if uluslararasi else "2.8"
    if bolum:
        return "2.5" if uluslararasi else "2.6"
    return "2.2" if uluslararasi else "2.3"


# EK-2 1.2 / 1.9 / 1.11 kapsamındaki (araştırma makalesi olmayan) türler.
# Dergi adlarındaki "Review" (örn. Physical Review) yanlış eşleşmesin diye yalın "review" aranmaz.
DERLEME_IPUCU = ("derleme", "review article", "(review)", "[review]")
NOT_IPUCU = ("teknik not", "technical note", "editöre mektup", "editore mektup", "letter to the editor",
             "vaka takdimi", "olgu sunumu", "case report", "kitap eleştirisi", "book review",
             "araştırma notu", "research note", "çeviri makale")


# AVES makale türleri (label-warning): araştırma makalesi olanlar ve derleme
AVES_ARASTIRMA = ("ozgun makale", "kisa makale")
AVES_DERLEME = ("derleme",)


def makale_ek2_kodu(endeksler: list, metin: str = "", ulusal: bool = False,
                    tip: str = "") -> str:
    """AVES makale kaydının EK-2 kodu (1.1–1.11): endekse ve makale türüne göre.

    tip: AVES türü (Özgün Makale, Derleme Makale, Vaka Takdimi, Editöre Mektup, Teknik Not,
    Kitap Kritiği, Araştırma Notu, Özet …). Yoksa künye metnindeki ipuçlarına bakılır.
    AVES endeks etiketleri: SCI / SCI-Expanded / SSCI / AHCI → 1.1–1.3;
    ESCI, Scopus, "Alan Endeksleri" (ÜAK tanımlı) → 1.4; TR DİZİN → 1.6;
    diğer endeksler → 1.5; "Endekste Taranmıyor" → 1.7 (ulusal dergide: 1.8).
    """
    etiketler = [e.upper() for e in (endeksler or [])]
    eks = " ".join(etiketler)
    t = _norm(tip)
    if t:
        derleme = any(k in t for k in AVES_DERLEME)
        not_ = not derleme and not any(k in t for k in AVES_ARASTIRMA)
    else:
        m = (metin or "").lower()
        derleme = any(k in m for k in DERLEME_IPUCU)
        not_ = any(k in m for k in NOT_IPUCU)
    diger = derleme or not_                     # araştırma makalesi değil
    trdizin = "TRDIZIN" in eks or "TR DİZİN" in eks or "TR DIZIN" in eks
    if re.search(r"(?<![A-Z])(SCI|SCI-EXPANDED|SCI-E|SSCI|AHCI|A&HCI)(?![A-Z])", eks):
        return "1.3" if derleme else "1.2" if not_ else "1.1"
    if "ESCI" in eks or "SCOPUS" in eks or "ALAN ENDEKS" in eks:
        return "1.9" if diger else "1.4"
    if trdizin:
        return "1.9" if diger else "1.6"
    if ulusal:
        return "1.11" if diger else "1.8"
    if any(e and "TARANMIYOR" not in e for e in etiketler):
        return "1.9" if diger else "1.5"          # diğer uluslararası endeksli
    return "1.11" if diger else "1.7"


def bildiri_ek2_kodu(tip: str, metin: str, uluslararasi: bool) -> str:
    """AVES bildiri kaydının EK-2 kodu (AVES türü: Tam metin bildiri, Özet bildiri, Poster,
    Sözlü Bildiri, Davetli konuşmacı). Tam metni belirtilmeyen sözlü bildiri temkinli olarak
    özet sayılır; uluslararası davetli konuşma 3.1'de CPCI şartı aradığı için 3.2'ye gider."""
    t = _norm(tip) or _norm(metin)
    if "poster" in t:
        return "3.4" if uluslararasi else "3.8"
    if "davetli" in t:
        return "3.2" if uluslararasi else "3.5"
    if "tam metin" in t:
        return "3.2" if uluslararasi else "3.6"
    if "ozet" in t or "abstract" in t or "sozlu" in t:
        return "3.3" if uluslararasi else "3.7"
    return "3.2" if uluslararasi else "3.6"



def _norm(t: str) -> str:
    t = t.replace("ı", "i").replace("İ", "i").lower()
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    return " ".join(re.sub(r"[^a-z0-9]+", " ", t).split())


def _yazar_mi(parca: str) -> bool:
    kel = parca.split()
    return 0 < len(kel) <= 4 and all(k[0].isupper() for k in kel) and \
        not any(c.isdigit() or c in ":-" for c in parca)


def baslik_cikar(metin: str) -> str:
    """AVES künyesinden eser başlığı (yazar listesinden sonraki ilk bölüm)."""
    if m := re.search(r"Bölüm\s*:\s*(.+?)(?:\.\s*Sayfa|$)", metin):
        return m.group(1).strip()
    parca = [p.strip() for p in re.split(r",\s*", metin)]
    for i, p in enumerate(parca):
        if not _yazar_mi(p):
            return p
    return metin


def tekrar_anahtari(metin: str) -> str:
    """Aynı eseri tanımlayan anahtar: başlık + yıl + sayfa aralığı."""
    yillar = re.findall(r"\b((?:19|20)\d{2})\b", metin)
    yil = yillar[-1] if yillar else ""
    sayfa = re.search(r"pp\.\s*(\d+\s*-\s*\d+)", metin)
    return f"{_norm(baslik_cikar(metin))}|{yil}|{sayfa.group(1).replace(' ', '') if sayfa else ''}"


def _gecerli_baglanti(oge: dict) -> bool:
    link = (oge.get("link") or "").strip()
    return link.startswith("http") and "/cv/yayinlar/" not in link


def tekrarlari_ayikla(ogeler: list[dict]) -> tuple[list[tuple[int, dict]], list[tuple[int, dict, int]]]:
    """Aynı eserin tekrar kayıtlarını ayıklar.

    Döndürür: (kalanlar, atılanlar)
      kalanlar  → [(AVES sırası, öğe), ...]  (sıra korunur)
      atılanlar → [(AVES sırası, öğe, tuttuğu kaydın sırası), ...]
    Tekrarlardan geçerli erişim bağlantısı (DOI vb.) olan tutulur; hepsinde ya da
    hiçbirinde yoksa ilk kayıt tutulur.
    """
    gruplar: dict[str, list[int]] = {}
    for i, oge in enumerate(ogeler, 1):
        gruplar.setdefault(tekrar_anahtari(oge.get("metin", "")), []).append(i)
    tutulan: dict[int, int] = {}
    for sira_listesi in gruplar.values():
        bagli = [s for s in sira_listesi if _gecerli_baglanti(ogeler[s - 1])]
        tut = bagli[0] if bagli else sira_listesi[0]
        for s in sira_listesi:
            tutulan[s] = tut
    kalan = [(i, o) for i, o in enumerate(ogeler, 1) if tutulan[i] == i]
    atilan = [(i, o, tutulan[i]) for i, o in enumerate(ogeler, 1) if tutulan[i] != i]
    return kalan, atilan
