# -*- coding: utf-8 -*-
"""
TNKÜ Öğretim Üyeliği Kadrosuna Başvuru Puanlama Programı – Web Arayüzü
Tekirdağ Namık Kemal Üniversitesi | EYS-YNG-129 (28.03.2025)

Çalıştırmak için:
    pip install streamlit pandas reportlab
    streamlit run tnku_streamlit.py
"""

from __future__ import annotations
import io
import os
import datetime
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import tnku_atama as t

# ── AVES Otomatik Yükleme ────────────────────────────────────────────────────
try:
    import sys as _sys, os as _os, json as _json, hashlib as _hashlib, re as _re_aves

    def _aves_data_dir():
        """cv_scraper'ın veri dizinini bul."""
        script_dir = _os.path.dirname(_os.path.abspath(__file__))
        for candidate in [
            _os.path.join(script_dir, "cv_data"),
            _os.path.join(script_dir, "..", "cv_data"),
            r"C:\Users\asayg\OneDrive\Desktop\files2\cv_data",
        ]:
            if _os.path.exists(candidate):
                return candidate
        return None

    def _aves_yukle_cv(cv_url: str) -> dict:
        """cv_url için yerel JSON'ı yükle."""
        data_dir = _aves_data_dir()
        if not data_dir or not cv_url:
            return {}
        key = _hashlib.md5(cv_url.encode()).hexdigest()[:12]
        path = _os.path.join(data_dir, f"{key}.json")
        if _os.path.exists(path):
            try:
                return _json.load(open(path, encoding="utf-8"))
            except Exception:
                return {}
        return {}

    def _aves_scholar_yukle(cv_url: str) -> dict:
        """Scholar verisini yükle."""
        script_dir = _os.path.dirname(_os.path.abspath(__file__))
        scholar_dir = None
        for candidate in [
            _os.path.join(script_dir, "scholar_data"),
            _os.path.join(script_dir, "..", "scholar_data"),
            r"C:\Users\asayg\OneDrive\Desktop\files2\scholar_data",
        ]:
            if _os.path.exists(candidate):
                scholar_dir = candidate
                break
        if not scholar_dir or not cv_url:
            return {}
        key = _hashlib.md5(cv_url.encode()).hexdigest()[:12]
        path = _os.path.join(scholar_dir, f"{key}.json")
        if _os.path.exists(path):
            try:
                return _json.load(open(path, encoding="utf-8"))
            except Exception:
                return {}
        return {}

    def _aves_q_bul(metin: str) -> str | None:
        """Dergi Q değerini metin içinden veya scimago/jcr cache'den tahmin et."""
        # Basit keyword tabanlı Q tahmini
        m_low = metin.lower()
        if "q1" in m_low: return "Q1"
        if "q2" in m_low: return "Q2"
        if "q3" in m_low: return "Q3"
        if "q4" in m_low: return "Q4"
        return None

    def _yazar_sirasi_bul(metin: str, isim: str):
        """Künye metninden yazar listesini ve aranan kişinin sırasını bul."""
        if not isim or not metin:
            return 1, 1, False

        BAG = {'a','an','the','in','of','and','or','for','with','by',
               've','ile','bir','bu','da','de','to','on','at','is','as',
               'using','based','via','from','through','detection','classification',
               'approach','method','analysis','deep','learning','neural','network'}

        def _normalize_if_needed(m):
            """Sadece hiç büyük harf yoksa title case'e çevir."""
            harfler = [c for c in m if c.isalpha()]
            if not harfler:
                return m
            if sum(1 for c in harfler if c.isupper()) == 0:
                parcalar = m.split(',')
                yeni = []
                for p in parcalar:
                    p = p.strip()
                    kelimeler = [k[0].upper() + k[1:] if k else k for k in p.split()]
                    yeni.append(' '.join(kelimeler))
                return ', '.join(yeni)
            return m

        def _yazar_mi(parca):
            p = parca.strip()
            if not p or len(p) < 2:
                return False
            if p[0].isdigit():
                return False
            if ':' in p:
                return False
            kelimeler = p.split()
            if len(kelimeler) > 4:
                return False
            if any(_re_aves.search(r'\d', k) for k in kelimeler):
                return False
            if any(k.lower() in BAG for k in kelimeler):
                return False
            if any(k[0].islower() for k in kelimeler if k):
                return False
            tam_buyuk = [k for k in kelimeler if k == k.upper() and len(k) > 1]
            title_case = all(k[0].isupper() for k in kelimeler if k)
            return len(tam_buyuk) >= 1 or title_case

        metin_n = _normalize_if_needed(metin)
        parcalar = [p.strip() for p in metin_n.split(',')]
        yazarlar = []
        for p in parcalar:
            if _yazar_mi(p):
                yazarlar.append(p)
            else:
                break

        if not yazarlar:
            return 1, 1, False

        def _norm(s):
            return _re_aves.sub(r'\s+', ' ', s.upper().strip())

        isim_norm  = _norm(isim)
        isim_parts = [p for p in isim_norm.split() if len(p) > 2]

        for si, yazar in enumerate(yazarlar, 1):
            yazar_norm = _norm(yazar)
            if isim_norm == yazar_norm:
                return si, len(yazarlar), False
            if sum(1 for p in isim_parts if p in yazar_norm) >= min(2, len(isim_parts)):
                return si, len(yazarlar), False
            if len(isim_parts) == 1 and isim_parts[0] in yazar_norm:
                return si, len(yazarlar), False

        return 1, len(yazarlar), False

    def _makale_kod(endeksler: list, metin: str = "") -> str:
        eks = " ".join(endeksler).upper()
        m = metin.lower()
        if any(x in eks for x in ("SCI-EXPANDED","SCI-E","SSCI","AHCI")):
            if "derleme" in m or "review" in m: return "1.3"
            if "teknik not" in m or "editöre" in m: return "1.2"
            return "1.1"
        if "ESCI" in eks or "SCOPUS" in eks: return "1.4"
        if "TRDIZIN" in eks or "TR DİZİN" in eks:
            return "1.6" if "ulusal" in m else "1.6"
        if any(x in eks for x in ("EBSCO","DOAJ","DRJI")): return "1.5"
        return "1.7"


    _aves_son_hata = [""]  # Hata mesajını dışarı taşımak için


    # ── Dergi Q Değeri Lookup ────────────────────────────────────────────────
    _DERGI_Q = {
        # Q1 - SCI/SCI-E
        "nature": "Q1", "science": "Q1", "cell": "Q1",
        "ieee transactions on pattern analysis and machine intelligence": "Q1",
        "medical image analysis": "Q1", "pattern recognition": "Q1",
        "neural networks": "Q1", "information fusion": "Q1",
        "expert systems with applications": "Q1",
        "knowledge-based systems": "Q1",
        "computers in biology and medicine": "Q1",
        "biomedical signal processing and control": "Q1",
        "artificial intelligence in medicine": "Q1",
        "journal of biomedical informatics": "Q1",
        "applied soft computing": "Q1", "neurocomputing": "Q1",
        "ieee transactions on neural networks and learning systems": "Q1",
        "ieee transactions on image processing": "Q1",
        "ieee transactions on medical imaging": "Q1",
        "ieee journal of biomedical and health informatics": "Q1",
        "computers in human behavior": "Q1",
        "information sciences": "Q1", "future generation computer systems": "Q1",
        "pattern recognition letters": "Q1",
        "computer methods and programs in biomedicine": "Q1",
        "international journal of neural systems": "Q1",
        "ieee transactions on cybernetics": "Q1",
        "ieee transactions on systems man and cybernetics": "Q1",
        "journal of king saud university - computer and information sciences": "Q1",
        # Q2 - SCI
        "ieee access": "Q2",
        "peerj computer science": "Q2",
        "diagnostics": "Q2", "sensors": "Q2", "electronics": "Q2",
        "symmetry": "Q2", "mathematics": "Q2", "applied sciences": "Q2",
        "healthcare": "Q2", "bioengineering": "Q2",
        "signal image and video processing": "Q2",
        "international journal of imaging systems and technology": "Q2",
        "computational and mathematical methods in medicine": "Q2",
        "mathematical biosciences and engineering": "Q2",
        "journal of healthcare engineering": "Q2",
        "multimedia tools and applications": "Q2",
        "signal processing: image communication": "Q2",
        "applied intelligence": "Q2",
        "neural computing and applications": "Q2",
        "soft computing": "Q2",
        "international journal of machine learning and cybernetics": "Q2",
        "journal of ambient intelligence and humanized computing": "Q2",
        "turkish journal of electrical engineering and computer sciences": "Q2",
        # Q3 - ESCI/Scopus
        "journal of imaging": "Q3",
        "traitement du signal": "Q3",
        "international journal of advanced computer science and applications": "Q3",
        "journal of experimental and theoretical analyses": "Q3",
        "concurrency and computation practice and experience": "Q3",
        "automatika": "Q3",
    }

    def _dergi_q_bul(dergi_adi):
        """Dergi adından Q değeri bul (lookup + kısmi eşleşme)."""
        if not dergi_adi:
            return None
        d = dergi_adi.lower().strip()
        # Tam eşleşme
        if d in _DERGI_Q:
            return _DERGI_Q[d]
        # Kısmi eşleşme
        for bilinen, q in _DERGI_Q.items():
            if bilinen in d or d in bilinen:
                return q
        return None

    def _kunye_dergi_cikart(kunye):
        """Künye metninden dergi adını çıkar."""
        if not kunye:
            return None
        parcalar = [p.strip() for p in kunye.split(',')]
        bitis_idx = len(parcalar)
        for i, p in enumerate(parcalar):
            p_low = p.lower().strip()
            if _re_aves.match(
                r'^(vol|volume|cilt|sayı|no|pp|pages?|\d{4}$'
                r'|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec'
                r'|oca|şub|nis|haz|tem|ağu|eyl|eki|kas|ara)', p_low):
                bitis_idx = i
                break
        BAG = {'a','an','the','in','of','and','or','for','with','by','ve','ile'}
        def _yazar_mi2(p):
            kel = p.split()
            if len(kel) > 4: return False
            if any(k.lower() in BAG for k in kel): return False
            if ':' in p: return False
            if any(_re_aves.search(r'[0-9]', k) for k in kel): return False
            return all(k[0].isupper() for k in kel if k)
        yb = 0
        for i, p in enumerate(parcalar[:bitis_idx]):
            if _yazar_mi2(p): yb = i + 1
            else: break
        aralik = parcalar[yb:bitis_idx]
        if not aralik:
            return None
        dergi = aralik[-1].strip()
        if len(dergi) < 5 and len(aralik) >= 2:
            dergi = f"{aralik[-2]}, {aralik[-1]}"
        return dergi if len(dergi) >= 3 else None

    def _kunye_q_bul(kunye):
        """Künyeden dergi adını çıkar ve Q değerini bul."""
        dergi = _kunye_dergi_cikart(kunye)
        if dergi:
            return _dergi_q_bul(dergi)
        return None

    def _aves_canli_cek(cv_url: str) -> dict:
        """AVES CV sayfasından canlı veri çek. Session cookie zorunlu."""
        _aves_son_hata[0] = ""
        try:
            import requests as _req
            from bs4 import BeautifulSoup as _BS
            import copy as _copy
        except ImportError as _ie:
            _aves_son_hata[0] = f"Paket eksik: {_ie}"
            return {}

        HDR = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,*/*;q=0.9",
            "Accept-Language": "tr-TR,tr;q=0.9",
        }

        base = cv_url.rstrip("/").rstrip("\\")
        if base.startswith("//"):
            base = "http:" + base
        if not base.startswith("http"):
            # "asaygili.cv.nku.edu.tr" formatı
            base = "http://" + base

        # Session oluştur - önce ana sayfayı ziyaret et (cookie al)
        sess = _req.Session()
        sess.headers.update(HDR)
        try:
            r0 = sess.get(base + "/", timeout=12)
            if r0.status_code not in (200, 301, 302):
                _aves_son_hata[0] = f"Ana sayfa {r0.status_code}: {base}/"
                return {}
        except Exception as _e0:
            _aves_son_hata[0] = f"Bağlantı hatası: {_e0}"
            return {}

        # Kategori başlık → anahtar eşleşmesi
        KAT_MAP = [
            ("Uluslararası Hakemli Dergi",   "ulusl_makale"),
            ("Ulusal Hakemli Dergi",          "ulusal_makale"),
            ("Uluslararası Kitap",            "kitap_ulusl"),
            ("Ulusal Kitap",                  "kitap_ulusal"),
            ("Kitap Bölümü",                  "kitap_bolum"),
            ("Uluslararası Bilimsel Toplantı","ulusl_bildiri"),
            ("Ulusal Bilimsel Toplantı",      "ulusal_bildiri"),
        ]
        def _kategori_key(baslik):
            for anahtar, key in KAT_MAP:
                if anahtar.lower() in baslik.lower():
                    return key
            return baslik.lower().replace(" ","_")[:20]

        def _parse_yayinlar_html(html):
            soup = _BS(html, "html.parser")
            sonuc = {}
            for panel in soup.find_all("div", class_="panel"):
                heading = panel.find("div", class_="panel-heading")
                if not heading:
                    continue
                baslik = heading.get_text(strip=True)
                key    = _kategori_key(baslik)
                ogeler = []
                for tr in panel.find_all("tr"):
                    tds = tr.find_all("td")
                    if len(tds) < 2:
                        continue
                    td = tds[1]
                    endeks = [s.get_text(strip=True)
                              for s in td.find_all("span", class_="label-info")]
                    tip    = next((s.get_text(strip=True)
                                   for s in td.find_all("span", class_="label-warning")), "")
                    td_c   = _copy.copy(td)
                    for tag in td_c.find_all(["span","a"]):
                        tag.extract()
                    metin  = td_c.get_text(separator=" ", strip=True)
                    if metin and len(metin) > 5:
                        ogeler.append({"metin": metin, "endeks": endeks, "tip": tip})
                if ogeler:
                    sonuc[key] = {"baslik": baslik, "sayi": len(ogeler), "ogeler": ogeler}
            return sonuc

        def _parse_genel_html(html):
            soup = _BS(html, "html.parser")
            ogeler = []
            for tr in soup.find_all("tr"):
                tds = tr.find_all("td")
                if len(tds) >= 2:
                    metin = tds[1].get_text(separator=" ", strip=True)
                    if metin and len(metin) > 5:
                        ogeler.append({"metin": metin[:400]})
            return {"sayi": len(ogeler), "ogeler": ogeler}

        def _parse_patent_odul_html(html):
            soup = _BS(html, "html.parser")
            ogeler = []
            mevcut_tip = "patent"
            ODUL_KW = {"ödül","award","prize","madalya","plaket","teşvik","birincilik"}
            PATENT_KW = {"patent","faydalı model","ep ","us ","wo ","pct","wipo"}
            # Bölüm başlıklarını bul
            for el in soup.find_all(True):
                if el.name in ("h2","h3","h4") or (
                        el.get("class") and "panel-heading" in " ".join(el.get("class",""))):
                    txt = el.get_text(strip=True).lower()
                    if "ödül" in txt: mevcut_tip = "odul"
                    elif "patent" in txt: mevcut_tip = "patent"
                elif el.name == "tr":
                    tds = el.find_all("td")
                    if len(tds) >= 2:
                        metin = tds[1].get_text(separator=" ", strip=True)
                        if not metin or len(metin) < 5: continue
                        m_low = metin.lower()
                        if any(k in m_low for k in ODUL_KW): tip = "odul"
                        elif any(k in m_low for k in PATENT_KW): tip = "patent"
                        else: tip = mevcut_tip
                        ogeler.append({"metin": metin[:400], "tip": tip})
            return {"sayi": len(ogeler), "ogeler": ogeler}

        veri = {}
        referer = base + "/"

        # Yayınlar (tüm kategoriler tek sayfada)
        try:
            r = sess.get(base + "/cv/yayinlar/", timeout=12,
                         headers={"Referer": referer})
            if r.status_code == 200:
                parsed = _parse_yayinlar_html(r.text)
                veri.update(parsed)
        except Exception:
            pass

        # Projeler
        try:
            r = sess.get(base + "/cv/projeler/", timeout=10,
                         headers={"Referer": referer})
            if r.status_code == 200:
                p = _parse_genel_html(r.text)
                if p["sayi"] > 0:
                    veri["proje"] = p
        except Exception:
            pass

        # Patent & Ödüller
        try:
            r = sess.get(base + "/cv/patentleroduller/", timeout=10,
                         headers={"Referer": referer})
            if r.status_code == 200:
                p = _parse_patent_odul_html(r.text)
                if p["sayi"] > 0:
                    veri["patent"] = p
        except Exception:
            pass

        return veri

    def _yayin_yili_bul(metin: str) -> int:
        """Künye metninden yayın yılını bul (4 haneli sayı)."""
        import re as _re_yil
        # Son 4 haneli yıl sayısını al (2000-2030 arası)
        yillar = _re_yil.findall(r'\b(20\d{2}|19\d{2})\b', metin)
        if yillar:
            return int(yillar[-1])  # Son yılı al
        return 0

    def aves_faaliyete_donustur(cv_url: str, isim: str) -> list[t.Faaliyet]:
        """AVES verisini t.Faaliyet listesine dönüştür.
        Önce yerel cache'e bakar, yoksa AVES'ten canlı çeker."""
        import streamlit as _st2
        # Profesör başvurusuysa doçentlik yılını al
        kadro_v    = _st2.session_state.get("v_kadro", "")
        docent_yil = int(_st2.session_state.get("v_docent_yil", 0) or 0)
        # Sadece profesör başvurusunda docent_sonrasi hesapla
        def _docent_sonrasi_mi(metin_):
            if kadro_v != "profesor" or docent_yil == 0:
                return False
            yayin_yil = _yayin_yili_bul(metin_)
            return yayin_yil > docent_yil if yayin_yil > 0 else False

        veri = _aves_yukle_cv(cv_url)
        sch  = _aves_scholar_yukle(cv_url)
        if not veri:
            veri = _aves_canli_cek(cv_url)

        faaliyetler = []
        ekle = faaliyetler.append

        # 1. Makaleler
        for kat_key in ("ulusl_makale", "ulusal_makale"):
            blok = veri.get(kat_key)
            if not blok: continue
            for o in blok.get("ogeler", []):
                metin  = o.get("metin", "")
                endeks = o.get("endeks", []) or []
                si, toplam, sorumlu = _yazar_sirasi_bul(metin, isim)
                # Önce kodu belirle
                if kat_key == "ulusal_makale":
                    eks_str = " ".join(endeks).upper()
                    kod = "1.6" if "TRDIZIN" in eks_str or "TR DİZİN" in eks_str else "1.8"
                else:
                    kod = _makale_kod(endeks, metin)
                # Q değeri sadece 1.1, 1.3, 4.1 için geçerli
                if kod in ("1.1", "1.3", "4.1"):
                    q = o.get("q") or _kunye_q_bul(metin) or _aves_q_bul(metin)
                else:
                    q = None
                f_obj = t.Faaliyet(
                    kod=kod, adet=1,
                    toplam_yazar=toplam, yazar_sirasi=si,
                    sorumlu_veya_senyör=sorumlu, q_degeri=q,
                    docent_sonrasi=_docent_sonrasi_mi(metin),
                )
                f_obj._kunye = metin[:300]
                ekle(f_obj)

        # 2. Kitap / Bölüm
        for kat_key in ("kitap_ulusl","kitap_ulusal","kitap_bolum"):
            blok = veri.get(kat_key)
            if not blok: continue
            for o in blok.get("ogeler", []):
                metin = o.get("metin","")
                if "ulusl" in kat_key:
                    kod = "2.4" if "bölüm" in kat_key else "2.2"
                else:
                    kod = "2.6" if "bölüm" in kat_key else "2.3"
                si, toplam, sorumlu = _yazar_sirasi_bul(metin, isim)
                f_obj2 = t.Faaliyet(kod=kod, adet=1,
                                toplam_yazar=toplam, yazar_sirasi=si,
                                sorumlu_veya_senyör=sorumlu,
                                docent_sonrasi=_docent_sonrasi_mi(metin))
                f_obj2._kunye = metin[:300]
                ekle(f_obj2)

        # 3. Bildiriler
        for kat_key, ulusl in [("ulusl_bildiri",True),("ulusal_bildiri",False)]:
            blok = veri.get(kat_key)
            if not blok: continue
            for o in blok.get("ogeler", []):
                metin = o.get("metin","").lower()
                if ulusl:
                    kod = "3.3" if "özet" in metin or "abstract" in metin else                           "3.4" if "poster" in metin else "3.2"
                else:
                    kod = "3.7" if "özet" in metin else                           "3.8" if "poster" in metin else "3.6"
                si, toplam, sorumlu = _yazar_sirasi_bul(metin, isim)
                f_obj3 = t.Faaliyet(kod=kod, adet=1,
                                toplam_yazar=toplam, yazar_sirasi=si,
                                docent_sonrasi=_docent_sonrasi_mi(metin))
                f_obj3._kunye = metin[:300]
                ekle(f_obj3)

        # 5. Atıf (Scholar)
        atif   = int(sch.get("atif",0)    or 0)
        hindex = int(sch.get("h_index",0) or 0)
        if atif > 0:
            ekle(t.Faaliyet(kod="5.1", adet=atif))
        if hindex > 0:
            ekle(t.Faaliyet(kod="5.9", adet=hindex))

        # 11. Patent
        PATENT_KW = {"patent","faydalı model","ep ","us ","wo ","pct","wipo"}
        blok = veri.get("patent")
        if blok:
            for o in blok.get("ogeler", []):
                metin = o.get("metin","")
                m_low = metin.lower()
                tip   = o.get("tip","")
                if tip == "odul": continue
                if tip == "patent" or any(k in m_low for k in PATENT_KW):
                    if any(x in m_low for x in ("us ","ep ","wo ","pct","wipo")):
                        kod, pd = "11.1", "tescilli"
                    else:
                        kod, pd = "11.2", "tescilli"
                    if "başvuru" in m_low: pd = "basvuru"
                    elif "araştırma" in m_low: pd = "arastirma_raporu"
                    f_obj4 = t.Faaliyet(kod=kod, adet=1, patent_durum=pd,
                                        docent_sonrasi=_docent_sonrasi_mi(metin))
                    f_obj4._kunye = metin[:300]
                    ekle(f_obj4)

        # 12. Proje
        blok = veri.get("proje")
        if blok:
            for o in blok.get("ogeler", []):
                m = o.get("metin","").lower()
                yurt = any(x in m for x in ("yürütücü","koordinatör","pi "))
                if "tubitak" in m or "tübitak" in m:
                    kod = "12.5" if yurt else "12.6"
                elif any(x in m for x in ("ab ","h2020","horizon","fp7","erasmus")):
                    kod = "12.1" if yurt else "12.2"
                elif "bap" in m:
                    kod = "12.11" if yurt else "12.12"
                else:
                    kod = "12.13" if yurt else "12.14"
                f_obj5 = t.Faaliyet(kod=kod, adet=1,
                                    docent_sonrasi=_docent_sonrasi_mi(m))
                f_obj5._kunye = m[:300]
                ekle(f_obj5)

        # 17. Tez danışmanlığı
        for gorev in (veri.get("_akademik_gorev") or []):
            rol = gorev.get("unvan","").lower()
            if "tez" in rol or "danışman" in rol:
                kod = "17.1" if "doktora" in rol else "17.2"
                f_obj5 = t.Faaliyet(kod=kod, adet=1,
                                    docent_sonrasi=_docent_sonrasi_mi(m))
                f_obj5._kunye = m[:300]
                ekle(f_obj5)

        return faaliyetler

    AVES_OK = True

except Exception as _aves_ex:
    AVES_OK = False
    def aves_faaliyete_donustur(cv_url, isim):
        return []


# ── PDF kütüphanesi ──────────────────────────────────────────────────────────
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable,
    )
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    PDF_OK = True
except ImportError:
    PDF_OK = False

# ─────────────────────────────────────────────────────────────────────────────
# Sayfa Yapılandırması
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="TNKÜ Atama Puanlama",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed",
)

components.html("""
<script>
(function() {
  var GA_ID = 'G-QJFQV27KN5';
  var win = window;
  try { if (window.top && window.top.document) win = window.top; } catch(e) {}

  win.dataLayer = win.dataLayer || [];
  function gtag(){ win.dataLayer.push(arguments); }
  gtag('js', new Date());
  gtag('config', GA_ID, {
    'page_location': 'https://tnku-atama.streamlit.app',
    'page_title': 'TNKU Atama Puanlama'
  });

  var s = document.createElement('script');
  s.async = true;
  s.src = 'https://www.googletagmanager.com/gtag/js?id=' + GA_ID;
  s.onload = function() {
    if (win !== window) {
      win.dataLayer = win.dataLayer || [];
      function gtagTop(){ win.dataLayer.push(arguments); }
      gtagTop('js', new Date());
      gtagTop('config', GA_ID, {
        'page_location': 'https://tnku-atama.streamlit.app'
      });
    }
  };
  document.head.appendChild(s);
})();
</script>
""", height=1)

# ─────────────────────────────────────────────────────────────────────────────
# CSS  (Google Fonts → Türkçe karakter desteği + responsive tasarım)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">

<style>
/* ── Temel font — ikon fontlarını (Material Icons) bozmamak için
       span ve div dahil edilmedi ── */
html, body { font-family: 'Inter', 'Segoe UI', system-ui, sans-serif !important; }

.stMarkdown, .stMarkdown p, .stMarkdown li,
.stTextInput input, .stTextInput label,
.stSelectbox label, .stSelectbox div[data-baseweb],
.stRadio label, .stCheckbox label,
.stNumberInput input, .stNumberInput label,
.stButton button, .stDownloadButton button,
.stDataFrame, .stMetric label, .stMetric div,
.stAlert, .stInfo, .stSuccess, .stError, .stWarning,
.stTabs [data-baseweb="tab"],
h1, h2, h3, h4, p, label {
    font-family: 'Inter', 'Segoe UI', system-ui, sans-serif !important;
}

/* ── Streamlit üst çubuk: mobilde daha yüksek olduğu için padding ── */
.block-container {
    padding-top: 4.5rem !important;
    padding-bottom: 0 !important;
}
.stMainBlockContainer { max-width: 1100px; }

/* Masaüstünde padding'i azalt */
@media (min-width: 769px) {
    .block-container { padding-top: 2rem !important; }
}

/* ── Başlık bandı ── */
.header-bar {
    background: linear-gradient(135deg, #1A2B4A 0%, #2E4A7A 100%);
    padding: 18px 24px;
    border-radius: 12px;
    margin-bottom: 20px;
    box-shadow: 0 4px 16px rgba(26,43,74,0.18);
}
.header-bar h2 {
    color: #fff;
    margin: 0 0 4px 0;
    font-size: clamp(1em, 2.5vw, 1.3em);
    font-weight: 700;
    letter-spacing: -0.02em;
}
.header-bar small { color: #A8C8F0; font-size: 0.8em; font-weight: 400; }

/* ── Kart ── */
.card {
    background: #fff;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 16px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.card-title {
    font-size: 0.75em;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #2E5DA3;
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 2px solid #E8F0FB;
}

/* ── Sonuç bandı ── */
.sonuc-ok {
    background: linear-gradient(135deg, #1A7A3A, #27AE60);
    color: #fff;
    padding: 18px 24px;
    border-radius: 12px;
    text-align: center;
    font-size: clamp(0.95em, 2vw, 1.1em);
    font-weight: 700;
    letter-spacing: 0.01em;
    margin: 12px 0;
    box-shadow: 0 4px 16px rgba(26,122,58,0.25);
}
.sonuc-fail {
    background: linear-gradient(135deg, #C0392B, #E74C3C);
    color: #fff;
    padding: 18px 24px;
    border-radius: 12px;
    text-align: center;
    font-size: clamp(0.95em, 2vw, 1.1em);
    font-weight: 700;
    letter-spacing: 0.01em;
    margin: 12px 0;
    box-shadow: 0 4px 16px rgba(192,57,43,0.25);
}

/* ── Kriter satırları ── */
.kriter-ok {
    background: #F0FBF4;
    border-left: 4px solid #27AE60;
    padding: 9px 14px;
    margin: 3px 0;
    border-radius: 0 8px 8px 0;
    font-size: 0.88em;
    line-height: 1.5;
}
.kriter-fail {
    background: #FEF2F2;
    border-left: 4px solid #E74C3C;
    padding: 9px 14px;
    margin: 3px 0;
    border-radius: 0 8px 8px 0;
    font-size: 0.88em;
    line-height: 1.5;
}
.kriter-info {
    background: #FFFBEB;
    border-left: 4px solid #F59E0B;
    padding: 9px 14px;
    margin: 3px 0;
    border-radius: 0 8px 8px 0;
    font-size: 0.88em;
    line-height: 1.5;
    color: #78350F;
}

/* ── Puan kutuları ── */
.puan-kutu {
    background: #F8FAFF;
    border: 1px solid #DBEAFE;
    border-radius: 10px;
    padding: 14px 18px;
    text-align: center;
}
.puan-kutu .label { font-size: 0.75em; color: #64748B; font-weight: 600;
                    text-transform: uppercase; letter-spacing: 0.06em; }
.puan-kutu .value { font-size: 1.8em; font-weight: 700; color: #1E3A5F;
                    line-height: 1.2; margin-top: 4px; }
.puan-kutu.toplam { background: linear-gradient(135deg, #1A2B4A, #2E5DA3);
                     border: none; }
.puan-kutu.toplam .label { color: #A8C8F0; }
.puan-kutu.toplam .value { color: #fff; }

/* ── Hesapla çubuğu ── */
.hesapla-bar {
    background: #F8FAFF;
    border: 1px solid #DBEAFE;
    border-radius: 12px;
    padding: 14px 20px;
    margin: 8px 0 16px 0;
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
}
.hesapla-bar .faaliyet-sayisi {
    flex: 1;
    color: #475569;
    font-size: 0.88em;
    min-width: 180px;
}
.faaliyet-badge {
    display: inline-block;
    background: #2E5DA3;
    color: white;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.82em;
    font-weight: 600;
    margin-right: 4px;
}

/* ── Sekme başlıkları ── */
[data-baseweb="tab"] { font-weight: 600 !important; }

/* ── Kategori listesi ── */
.stRadio [role="radiogroup"] { gap: 2px !important; }
.stRadio label { font-size: 0.85em !important; padding: 4px 8px !important;
                 border-radius: 6px !important; }
.stRadio label:hover { background: #EFF6FF !important; }

/* ── Mobil uyum ── */
@media (max-width: 768px) {
    .block-container {
        padding-top: 4.5rem !important;
        padding-left: 0.75rem !important;
        padding-right: 0.75rem !important;
    }
    .header-bar { padding: 12px 14px; border-radius: 8px; }
    .header-bar h2 { font-size: 0.95em !important; line-height: 1.4; }
    .card { padding: 14px; }
    .puan-kutu .value { font-size: 1.4em; }
}

/* ── Buton iyileştirme ── */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #1A7A3A, #27AE60) !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    padding: 0.5rem 1.2rem !important;
    box-shadow: 0 2px 8px rgba(26,122,58,0.3) !important;
    transition: transform 0.1s, box-shadow 0.1s !important;
}
.stButton > button[kind="primary"]:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(26,122,58,0.4) !important;
}
.stButton > button[kind="secondary"] {
    border-radius: 8px !important;
    font-weight: 500 !important;
}

/* ── Download butonu ── */
.stDownloadButton > button {
    background: linear-gradient(135deg, #1A2B4A, #2E5DA3) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    box-shadow: 0 2px 8px rgba(26,43,74,0.25) !important;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Session State
# ─────────────────────────────────────────────────────────────────────────────
if "faaliyetler" not in st.session_state:
    st.session_state.faaliyetler: list[t.Faaliyet] = []
if "sonuc" not in st.session_state:
    st.session_state.sonuc = None
if "son_aday" not in st.session_state:
    st.session_state.son_aday = None

# ─────────────────────────────────────────────────────────────────────────────
# Sabitler
# ─────────────────────────────────────────────────────────────────────────────
GRUPLAR: dict[int, str] = {
    1: "Makale",
    2: "Kitap / Kitap Bölümü",
    3: "Bildiri / Ansiklopedi",
    4: "Editörlük (max 40p)",
    5: "Atıf (max 50p)",
    6: "Hakemlik (max 20p)",
    7: "Panelist / Jüri (max 20p)",
    8: "TV – Sinema – Tasarım",
    9: "Sanat ve Tasarım",
    10: "Sportif Etkinlikler",
    11: "Patentler ve Girişimler",
    12: "Projeler",
    13: "Çalıştay / Kongre (max 20p)",
    14: "Ödüller",
    15: "Kazı Çalışmaları",
    16: "Yurt Dışı Deneyimi",
    17: "Egitim – Öğretim",
    18: "İdari Görevler",
    19: "Diğer",
}

KADRO_ADI: dict[str, str] = {
    "dr_ilk":     "Dr. Öğretim Üyesi – İlk Atanma",
    "dr_yeniden": "Dr. Öğretim Üyesi – Yeniden Atanma",
    "docent":     "Doçent",
    "profesor":   "Profesör",
}

PATENT_MAP: dict[str, str] = {
    "Tescilli (tam puan)":           "tescilli",
    "Araştırma raporu almış (x0.5)": "arastirma_raporu",
    "Basvuru aşaması (x0.25)":       "basvuru",
}

# ─────────────────────────────────────────────────────────────────────────────
# Yardımcı Fonksiyonlar
# ─────────────────────────────────────────────────────────────────────────────

def _tur_renk(val: str) -> str:
    return ("background-color: #E8F5E9" if val == "PUAN-1"
            else "background-color: #EAF0FA")


def _aday_olustur() -> t.AdayBilgi:
    alan_raw = st.session_state.get("v_alan", "ALAN-1")
    alan     = "ALAN-1" if "ALAN-1" in alan_raw else "ALAN-2"
    kadro    = st.session_state.get("v_kadro", "dr_ilk")
    return t.AdayBilgi(
        ad_soyad=(st.session_state.get("v_ad", "").strip() or "Bilinmiyor"),
        alan=alan,
        guzel_sanat=bool(st.session_state.get("v_guzel", False)),
        kadro_turu=kadro,
        yeniden_sure=int(st.session_state.get("v_sure", 3)) if kadro == "dr_yeniden" else 3,
        faaliyetler=list(st.session_state.faaliyetler),
        doktora_var=bool(st.session_state.get("v_doktora", False)),
        yabanci_dil_puani=float(st.session_state.get("v_ydpuan", 0.0)),
        calisma_alani_yabanci_dil_bolumu=bool(st.session_state.get("v_ydbol", False)),
        ornek_ders_basarili=bool(st.session_state.get("v_ornek", False)),
        uak_docent=bool(st.session_state.get("v_uak", False)),
        sifahi_sinav_basarili=bool(st.session_state.get("v_sifahi", False)),
        doktora_sonrasi_ders_yari_yil=int(st.session_state.get("v_ders", 0)),
        docent_sonrasi_sure_yil=float(st.session_state.get("v_docsure", 0.0)),
        baslica_arastirma_eseri_var=bool(st.session_state.get("v_baslica", False)),
    )


def _faaliyet_satirlari(kadro_su: str) -> list[dict]:
    rows = []
    for i, f in enumerate(st.session_state.faaliyetler):
        bilgi_f = t.EK2_PUANLAR.get(f.kod, {})
        p_f, _  = t.faaliyet_puan_hesapla(f)
        p1_f    = t.is_puan1(f.kod, kadro_su)
        grup    = bilgi_f.get("grup", 0)
        ek      = f.q_degeri or {
            "tescilli": "Tescil",
            "arastirma_raporu": "ArRapor",
            "basvuru": "Bas.",
        }.get(f.patent_durum or "", "")
        # Künye: Faaliyet nesnesine metin ekliyoruz (AVES'ten gelen)
        kunye = getattr(f, "_kunye", "") or ""
        rows.append({
            "#":        i + 1,
            "Kod":      f.kod,
            "Faaliyet": bilgi_f.get("ad", "")[:55],
            "Künye":    kunye[:120] if kunye else "—",
            "Adet":     f.adet,
            "Top.Yz.":  f.toplam_yazar if grup in {1, 2, 3} else "-",
            "Sira":     ("Sor/Sny" if f.sorumlu_veya_senyör else str(f.yazar_sirasi))
                        if grup in {1, 2, 3} else "-",
            "Q/Pat.":   ek,
            "Puan":     round(p_f, 2),
            "Tur":      "PUAN-1" if p1_f else "PUAN-2",
            "Doc.Sn.":  "✓" if f.docent_sonrasi else "",
        })
    return rows


def _bul_font(dosya: str) -> str | None:
    klasorler = [
        # Windows
        r"C:\Windows\Fonts",