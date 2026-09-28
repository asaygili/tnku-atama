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


def kitap_ek2_kodu(kat_key: str, metin: str) -> str:
    """Kitap kaydının EK-2 kodu.

    Bölüm: uluslararası → 2.5, ulusal → 2.6 (BKCI kapsamındaysa kullanıcı 2.4'e
    çevirebilir). Kitap: uluslararası → 2.2, ulusal → 2.3.
    """
    bolum = "bolum" in kat_key or bool(re.search(r"Bölüm\s*:", metin))
    uluslararasi = "ulusl" in kat_key
    if bolum:
        return "2.5" if uluslararasi else "2.6"
    return "2.2" if uluslararasi else "2.3"


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
