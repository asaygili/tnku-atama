"""
Faaliyetler için kanıt klasörü açma ve AVES numaraları kayınca yeniden adlandırma.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from pathlib import Path

import aves_yardimci as ay

from .kayit import KAYIT_DOSYASI, KUNYE_DOSYASI, KanitArsivi, KanitKaydi, kayit_yaz
from .ortak import slug, yil_bul

GRUP_AD = {"UM": "Uluslararası hakemli dergi makalesi", "UL": "Ulusal hakemli dergi makalesi",
           "KB": "Kitap / kitap bölümü", "UB": "Uluslararası bildiri", "NB": "Ulusal bildiri"}


def klasor_adi(aves_kod: str, kunye: str) -> str:
    return f"{aves_kod}_{yil_bul(kunye) or '0000'}_{slug(ay.baslik_cikar(kunye))}"


def kanit_listesi(aves_kod: str) -> list[str]:
    onek = aves_kod[:2]
    if onek in ("UM", "UL"):
        return ["Yayın tarihindeki endeks kanıtı (WoS Master Journal List / TR Dizin ekran görüntüsü)",
                "Yayın yılındaki JCR kuartil (Q) kanıtı"]
    if onek in ("UB", "NB"):
        return ["Kongre programı (sunumun yapıldığını gösterir)",
                "Katılım belgesi (en az bir yazarın katıldığını gösterir)",
                "Bildiri kitabı kapak/künye sayfası"]
    return ["Kitabın ISBN'li künye sayfası", "Yayınevi bilgisi (Md. 4 yayınevi tanımı)"]


def kunye_yaz(klasor: Path, aves_kod: str, kunye: str, doi: str = "", tur: str = "") -> None:
    """Yeni klasör için kunye.txt (kanıt kontrol listesiyle)."""
    metin = (f"Faaliyet     : {aves_kod} – {GRUP_AD.get(aves_kod[:2], '')}\n"
             f"Künye (AVES) : {kunye}\n"
             f"Tür / Endeks : {tur or '-'} (AVES kaydı)\n"
             f"DOI          : {doi or '-'}\n"
             f"Erişim       : {'https://doi.org/' + doi if doi else '-'}\n"
             f"Tam metin    : YOK – klasör {time.strftime('%d.%m.%Y')} tarihinde programdan açıldı\n\n"
             "Başvuru dosyası için ayrıca gerekli kanıtlar:\n"
             + "".join(f"  [ ] {x}\n" for x in kanit_listesi(aves_kod)))
    (klasor / KUNYE_DOSYASI).write_text(metin, encoding="utf-8")


def eksik_klasorler(arsiv: KanitArsivi, faaliyetler) -> list:
    """AVES'ten gelen ama kanıt klasörü olmayan faaliyetler."""
    return [f for f in faaliyetler
            if getattr(f, "aves_kod", "") and getattr(f, "kimlik", "")
            and arsiv.kimlik_ile(f.kimlik, f.aves_kod) is None]


def klasor_olustur(arsiv: KanitArsivi, faaliyet) -> KanitKaydi:
    kunye = getattr(faaliyet, "_kunye", "") or ""
    doi = faaliyet.kimlik[4:] if faaliyet.kimlik.startswith("doi:") else ""
    d = arsiv.kok / klasor_adi(faaliyet.aves_kod, kunye)
    d.mkdir(parents=True, exist_ok=True)
    kunye_yaz(d, faaliyet.aves_kod, kunye, doi)
    if doi:
        (d / "Kaynak.url").write_text(f"[InternetShortcut]\nURL=https://doi.org/{doi}\n",
                                      encoding="utf-8")
    k = kayit_yaz(d, faaliyet.aves_kod, kunye, doi, ek_kimlikler=[faaliyet.kimlik])
    arsiv.kayitlar.append(k)
    return k


@dataclass
class YenidenAdlandirma:
    kayit: KanitKaydi
    yeni_kod: str
    yeni_ad: str


def numara_plani(arsiv: KanitArsivi, faaliyetler) -> list[YenidenAdlandirma]:
    """Kimliği eşleşen ama AVES kodu değişmiş klasörler (AVES'e yeni yayın eklenince)."""
    plan = []
    for f in faaliyetler:
        kod = getattr(f, "aves_kod", "")
        k = arsiv.kimlik_ile(getattr(f, "kimlik", ""), kod)
        if kod and k and k.aves_kod and k.aves_kod != kod:
            yeni_ad = re.sub(r"^[A-Z]{2}\d{2}", kod, k.klasor.name)
            plan.append(YenidenAdlandirma(k, kod, yeni_ad))
    return plan


def numara_uygula(arsiv: KanitArsivi, plan: list[YenidenAdlandirma]) -> None:
    """İki aşamalı yeniden adlandırma (UM01↔UM02 gibi yer değişimlerinde çakışma olmaz)."""
    gecici = []
    for i, p in enumerate(plan):
        tmp = p.kayit.klasor.with_name(f"__yeniden_{i}_{p.kayit.klasor.name}")
        p.kayit.klasor.rename(tmp)
        gecici.append((tmp, p))
    for tmp, p in gecici:
        hedef = arsiv.kok / p.yeni_ad
        tmp.rename(hedef)
        # kayit.json ve kunye.txt'deki kodu güncelle
        kj = hedef / KAYIT_DOSYASI
        if kj.exists():
            v = json.loads(kj.read_text(encoding="utf-8"))
            v["aves_kod"] = p.yeni_kod
            kj.write_text(json.dumps(v, ensure_ascii=False, indent=1), encoding="utf-8")
        ku = hedef / KUNYE_DOSYASI
        if ku.exists():
            ku.write_text(re.sub(r"^(Faaliyet\s*: )[A-Z]{2}\d{2}", rf"\g<1>{p.yeni_kod}",
                                 ku.read_text(encoding="utf-8"), count=1, flags=re.M),
                          encoding="utf-8")
        p.kayit.klasor, p.kayit.aves_kod = hedef, p.yeni_kod


def kimlikleri_yaz(arsiv: KanitArsivi) -> int:
    """kayit.json'u olmayan (eski) yayın klasörlerine kayit.json yazar."""
    n = 0
    for k in arsiv.kayitlar:
        if not (k.klasor / KAYIT_DOSYASI).exists():
            kayit_yaz(k.klasor, k.aves_kod, k.kunye, k.doi, k.tur)
            n += 1
    return n
