"""
Açık erişimli tam metinlerin bulunup indirilmesi.

Yalnızca yasal açık erişim kaynakları (OpenAlex'in bildirdiği PDF konumları ve
kullanıcının kendi Google Drive bağlantıları) kullanılır. Bot koruması olan ya da
giriş isteyen sitelerde indirme denenmez; kullanıcıya bağlantı bırakılır.
"""

from __future__ import annotations

import re
import time
from pathlib import Path

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "Chrome/128 Safari/537.36"}


def oturum():
    import requests
    s = requests.Session()
    s.headers.update(UA)
    return s


def acik_erisim(doi: str, s=None) -> dict:
    """OpenAlex'ten açık erişim durumu, PDF adresleri ve atıf sayısı."""
    s = s or oturum()
    r = s.get(f"https://api.openalex.org/works/doi:{doi}", timeout=30)
    if r.status_code != 200:
        return {"durum": None, "pdf": [], "atif": None}
    w = r.json()
    return {"durum": (w.get("open_access") or {}).get("oa_status"),
            "pdf": [l["pdf_url"] for l in w.get("locations", []) if l.get("pdf_url")],
            "atif": w.get("cited_by_count")}


def yayinci_pdf_deseni(doi: str, sayfa: str) -> list[str]:
    """Yayıncının bilinen PDF adresi desenleri (sayfa: DOI'nin yönlendiği makale sayfası)."""
    sayfa = (sayfa or "").split("?")[0].split("#")[0].rstrip("/")
    d = (doi or "").lower()
    adres = []
    if "mdpi.com/" in sayfa:
        adres.append(sayfa + "/pdf")
    if "peerj.com/articles/" in sayfa:
        adres.append(sayfa + ".pdf")
    if "frontiersin.org/" in sayfa and not sayfa.endswith("/pdf"):
        adres.append(sayfa.replace("/full", "") + "/pdf")
    if d.startswith(("10.1007/", "10.1186/")):
        adres.append(f"https://link.springer.com/content/pdf/{doi}.pdf")
    if d.startswith(("10.1002/", "10.1111/")):
        adres.append(f"https://onlinelibrary.wiley.com/doi/pdfdirect/{doi}")
    if d.startswith("10.1080/"):
        adres.append(f"https://www.tandfonline.com/doi/pdf/{doi}")
    if d.startswith("10.1155/"):
        adres.append(f"https://downloads.hindawi.com/journals/{doi}.pdf")
    return adres


def pdf_adaylari(doi: str, s=None) -> dict:
    """Tam metin adayları: OpenAlex PDF konumları + yayıncı sayfasındaki citation_pdf_url
    etiketi + yayıncıya özgü desenler. Bot korumalı sitelerde (403 / "Just a moment")
    indirme denenmez; bulunan adres yine de kullanıcının tarayıcıdan indirmesi için döner."""
    from bs4 import BeautifulSoup
    s = s or oturum()
    oa = acik_erisim(doi, s)
    adres, sayfa, korumali = list(oa["pdf"]), "", False
    try:
        r = s.get(f"https://doi.org/{doi}", timeout=30)
        sayfa = r.url
        korumali = r.status_code in (401, 403, 429) or "Just a moment" in r.text[:3000]
        if r.status_code == 200 and not korumali:
            m = BeautifulSoup(r.text, "html.parser").find("meta", attrs={"name": "citation_pdf_url"})
            if m and m.get("content"):
                adres.append(m["content"])
    except Exception:  # noqa: BLE001
        pass
    adres += yayinci_pdf_deseni(doi, sayfa)
    return {"durum": oa["durum"], "pdf": list(dict.fromkeys(adres)), "sayfa": sayfa,
            "korumali": korumali}


def drive_adresi(url: str) -> str:
    m = re.search(r"/d/([^/]+)", url) or re.search(r"id=([^&]+)", url)
    return f"https://drive.google.com/uc?export=download&id={m.group(1)}" if m else url


def pdf_indir(url: str, hedef: Path, s=None, deneme: int = 6) -> tuple[bool, str]:
    """PDF'i indirir; gelen içeriğin gerçekten PDF olduğunu doğrular.
    Google Drive'ın büyük dosya onay sayfasını ve 429 (istek sınırı) yanıtlarını işler."""
    from bs4 import BeautifulSoup
    import requests

    s = s or oturum()
    if hedef.exists() and hedef.stat().st_size > 1000:
        return True, "zaten var"
    for i in range(deneme):
        try:
            r = s.get(url, stream=True, timeout=120)
            if "google.com" in r.url and "text/html" in r.headers.get("Content-Type", ""):
                form = BeautifulSoup(r.text, "html.parser").find("form")
                if not form:
                    return False, "Drive onay formu bulunamadı"
                q = {x["name"]: x.get("value", "") for x in form.find_all("input") if x.get("name")}
                r = s.get(form["action"], params=q, stream=True, timeout=300)
            if r.status_code == 429:
                time.sleep(20 * (i + 1))
                continue
            if r.status_code != 200:
                return False, f"HTTP {r.status_code}"
            gecici = hedef.with_suffix(".part")
            with open(gecici, "wb") as fp:
                for parca in r.iter_content(1 << 16):
                    fp.write(parca)
            with open(gecici, "rb") as fp:
                pdf_mi = fp.read(5) == b"%PDF-"
            if not pdf_mi:
                gecici.unlink()
                return False, "gelen dosya PDF değil"
            gecici.replace(hedef)
            return True, f"{hedef.stat().st_size / 1e6:.2f} MB"
        except requests.RequestException as e:
            time.sleep(10)
            son_hata = type(e).__name__
    return False, locals().get("son_hata", "tekrar denemeler başarısız")
