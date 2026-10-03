"""
Giriş şifresi (Streamlit Cloud sürümü için).

Şifre kodda değil, Streamlit'in "Secrets" ayarında tutulur:
    giris_sifresi = "…"                      # düz şifre
ya da
    giris_sifresi_sha256 = "<sha256 özeti>"   # şifrenin SHA-256 özeti (daha güvenli)
İkisi de tanımlı değilse (ör. kendi bilgisayarınızda) şifre sorulmaz.
Yerel denemede TNKU_GIRIS_SIFRESI ortam değişkeni de kullanılabilir.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import time

import streamlit as st

DENEME_SINIRI = 5        # bu kadar hatalı denemeden sonra
BEKLEME_SN = 60          # bu kadar saniye beklenir


def _ayar(ad: str) -> str:
    try:
        return str(st.secrets.get(ad, "") or "")
    except Exception:  # noqa: BLE001 – secrets dosyası hiç yoksa
        return ""


def _beklenen() -> tuple[str, str]:
    """(tür, değer): ("sha256", özet) | ("duz", şifre) | ("", "")"""
    if ozet := _ayar("giris_sifresi_sha256").strip().lower():
        return "sha256", ozet
    if duz := (_ayar("giris_sifresi") or os.environ.get("TNKU_GIRIS_SIFRESI", "")):
        return "duz", duz
    return "", ""


def _dogru_mu(girilen: str, tur: str, deger: str) -> bool:
    if tur == "sha256":
        return hmac.compare_digest(hashlib.sha256(girilen.encode("utf-8")).hexdigest(), deger)
    return hmac.compare_digest(girilen.encode("utf-8"), deger.encode("utf-8"))


def sifre_kontrol() -> None:
    """Şifre tanımlıysa ve oturum açılmamışsa giriş ekranını gösterip sayfayı durdurur."""
    tur, deger = _beklenen()
    ss = st.session_state
    if not tur or ss.get("_giris_ok"):
        return

    import arayuz_tema as ui
    ui.stil_uygula()
    _, orta, _ = st.columns([1, 1.4, 1])
    with orta:
        st.markdown(
            '<div class="hero" style="text-align:center;margin-top:8vh">'
            '<div class="hero-logo" style="display:inline-block">🎓</div>'
            "<h1 style='margin-top:10px !important'>Öğretim Üyeliği Atama Puanlama Sistemi</h1>"
            "<p>Tekirdağ Namık Kemal Üniversitesi · EYS-YNG-129</p></div>",
            unsafe_allow_html=True)
        kilit = ss.get("_giris_kilit", 0.0) - time.time()
        if kilit > 0:
            st.error(f"Çok sayıda hatalı deneme. {int(kilit) + 1} saniye sonra yeniden deneyin.")
            st.stop()
        with st.form("giris_formu"):
            sifre = st.text_input("Giriş şifresi", type="password",
                                  help="Programı kullanmak için yöneticiden aldığınız şifre.")
            gonder = st.form_submit_button("Giriş", type="primary", use_container_width=True)
        if gonder:
            if _dogru_mu(sifre, tur, deger):
                ss["_giris_ok"] = True
                ss.pop("_giris_hata", None)
                st.rerun()
            time.sleep(1)                         # tahmin denemelerini yavaşlat
            ss["_giris_hata"] = ss.get("_giris_hata", 0) + 1
            if ss["_giris_hata"] >= DENEME_SINIRI:
                ss["_giris_kilit"] = time.time() + BEKLEME_SN
                ss["_giris_hata"] = 0
            st.error("Şifre hatalı.")
    st.stop()
