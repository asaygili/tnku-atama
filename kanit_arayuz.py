"""
Streamlit arayüzünün kanıt arşivi bölümleri (yalnızca yerelde çalışır).

Kanıt klasörü bulunamazsa (örn. Streamlit Cloud) bu bölümler kendiliğinden gizlenir;
program kanıt klasörü olmadan eskisi gibi çalışır.
"""

from __future__ import annotations

import os
import sys
from datetime import date
from pathlib import Path

import streamlit as st

import tnku_atama as t
from kanit import KanitArsivi, aday_dosyasi, ayar
from kanit import klasor as kk
from kanit.kontrol import durum as kanit_durumu

ALAN_SECENEK = {"ALAN-1": "ALAN-1  –  Fen / Sağlık / Müh. / Matematik vb.",
                "ALAN-2": "ALAN-2  –  Sosyal / İdari / Eğitim / Güzel Sanatlar vb."}

# Oturum anahtarı ↔ AdayBilgi alanı
OTURUM_ALANLARI = {
    "v_ad": "ad_soyad", "v_guzel": "guzel_sanat", "v_kadro": "kadro_turu",
    "v_sure": "yeniden_sure", "v_doktora": "doktora_var", "v_ydpuan": "yabanci_dil_puani",
    "v_ydpuan2": "ikinci_yabanci_dil_puani", "v_ydbol": "calisma_alani_yabanci_dil_bolumu",
    "v_ornek": "ornek_ders_basarili", "v_uak": "uak_docent", "v_sifahi": "sifahi_sinav_basarili",
    "v_ders": "doktora_sonrasi_ders_yari_yil", "v_docsure": "docent_sonrasi_sure_yil",
    "v_docent_basvuru": "docent_basvuru_tarihi", "v_docent_unvan": "docent_unvan_tarihi",
    "v_uak_set": "uak_kriter_seti", "v_uak_docent_kriteri": "uak_kriterleri_yeniden_saglandi",
}


# ── Arşiv ──────────────────────────────────────────────────────────────────
def arsiv() -> KanitArsivi | None:
    kok = st.session_state.get("kanit_koku", "")
    return KanitArsivi(kok) if kok and Path(kok).is_dir() else None


def dosya_ac(yol: Path) -> None:
    """Dosyayı / klasörü işletim sisteminin varsayılan uygulamasıyla açar (yerel)."""
    try:
        if sys.platform == "win32":
            os.startfile(str(yol))  # noqa: S606
        elif sys.platform == "darwin":
            os.system(f'open "{yol}"')  # noqa: S605
        else:
            os.system(f'xdg-open "{yol}"')  # noqa: S605
    except OSError as e:
        st.error(f"Açılamadı: {e}")


# ── Aday dosyası ───────────────────────────────────────────────────────────
def _oturuma_yukle(aday: t.AdayBilgi, ek: dict) -> None:
    for anahtar, alan in OTURUM_ALANLARI.items():
        st.session_state[anahtar] = getattr(aday, alan)
    st.session_state["v_alan"] = ALAN_SECENEK.get(aday.alan, ALAN_SECENEK["ALAN-1"])
    if ek.get("aves_url"):
        st.session_state["v_aves_url"] = ek["aves_url"]
    st.session_state.faaliyetler = list(aday.faaliyetler)
    st.session_state.sonuc = None
    st.session_state.son_aday = None


def _yukle_cb():
    kok = Path(st.session_state["kanit_koku"])
    try:
        aday, ek = aday_dosyasi.yukle(kok)
        _oturuma_yukle(aday, ek)
        st.session_state["_kanit_mesaj"] = ("ok", f"{len(aday.faaliyetler)} faaliyet yüklendi "
                                                  f"({kok / aday_dosyasi.ADAY_DOSYASI}).")
    except (OSError, ValueError) as e:
        st.session_state["_kanit_mesaj"] = ("hata", f"Yüklenemedi: {e}")


def _kaydet_cb(aday_olustur):
    kok = Path(st.session_state["kanit_koku"])
    yol = aday_dosyasi.kaydet(kok, aday_olustur(),
                              {"aves_url": st.session_state.get("v_aves_url", "")})
    st.session_state["_kanit_mesaj"] = ("ok", f"Kaydedildi: {yol}")


def otomatik_yukle() -> None:
    """İlk açılışta, kanıt klasöründe aday.json varsa ve liste boşsa yükler."""
    if "kanit_koku" not in st.session_state:
        st.session_state["kanit_koku"] = ayar.kanit_koku()
    if st.session_state.get("_kanit_otomatik_denendi"):
        return
    st.session_state["_kanit_otomatik_denendi"] = True
    kok = st.session_state["kanit_koku"]
    if kok and (Path(kok) / aday_dosyasi.ADAY_DOSYASI).exists() and not st.session_state.faaliyetler:
        try:
            aday, ek = aday_dosyasi.yukle(Path(kok))
            _oturuma_yukle(aday, ek)
            st.session_state["_kanit_mesaj"] = ("ok", f"Kayıtlı aday dosyası yüklendi: "
                                                      f"{len(aday.faaliyetler)} faaliyet.")
        except (OSError, ValueError):
            pass


def kanit_bolumu(aday_olustur) -> None:
    """Aday Bilgileri sekmesinin başındaki 'Kanıt klasörü' kartı."""
    st.markdown('<div class="card-title">KANIT KLASÖRÜ (YEREL)</div>', unsafe_allow_html=True)
    k1, k2, k3 = st.columns([4, 1, 1], gap="small")
    with k1:
        yeni = st.text_input("Kanıt klasörü", value=st.session_state.get("kanit_koku", ""),
                             placeholder=r"E:\Kanit_Dosyalari",
                             help="Faaliyet kanıtlarının bulunduğu kök klasör. Yalnızca programı "
                                  "kendi bilgisayarınızda çalıştırdığınızda kullanılır.")
        if yeni != st.session_state.get("kanit_koku", ""):
            st.session_state["kanit_koku"] = yeni
            if yeni and Path(yeni).is_dir():
                ayar.kanit_koku_kaydet(yeni)
    a = arsiv()
    with k2:
        st.button("💾 Kaydet", use_container_width=True, disabled=a is None,
                  on_click=_kaydet_cb, args=(aday_olustur,),
                  help="Aday bilgilerini ve faaliyetleri kanıt klasörüne aday.json olarak kaydeder")
    with k3:
        var = a is not None and (a.kok / aday_dosyasi.ADAY_DOSYASI).exists()
        st.button("📂 Yükle", use_container_width=True, disabled=not var, on_click=_yukle_cb,
                  help="Kanıt klasöründeki aday.json'u yükler (mevcut liste değişir)")
    if msg := st.session_state.pop("_kanit_mesaj", None):
        (st.success if msg[0] == "ok" else st.error)(msg[1])
    if a is None:
        st.caption("Kanıt klasörü seçilmedi ya da bulunamadı. Program kanıt klasörü olmadan da "
                   "çalışır (Streamlit Cloud'da bu bölüm kullanılmaz).")
    else:
        tam = sum(1 for k in a.kayitlar if k.tam_metin)
        st.caption(f"📁 {len(a.kayitlar)} yayın klasörü (tam metni olan: {tam}) · "
                   f"{len(a.diger_klasorler)} diğer klasör")
    st.divider()


# ── Faaliyet tablosu ve kanıt paneli ───────────────────────────────────────
def tablo_sutunlari(f, a: KanitArsivi | None) -> dict:
    if a is None:
        return {}
    k = a.bul(f)
    if k is None:
        return {"Kanıt": "—", "Eksik": ""}
    if not k.aves_kod:                               # elle bağlanan yayın dışı klasör
        return {"Kanıt": f"📁 {len(k.dosyalar())} dosya", "Eksik": ""}
    d = kanit_durumu(k)
    return {"Kanıt": ("✓ tam metin" if k.tam_metin else "✗ tam metin yok")
                     + (f" · {len(k.atif_klasorleri())} atıf" if k.atif_klasorleri() else ""),
            "Eksik": str(len(d.eksik)) if d.eksik else "✓"}


def kanit_paneli(f, didx: int, a: KanitArsivi | None) -> str:
    """Düzenleme panelindeki kanıt bilgisi; seçilen kimliği döndürür."""
    kimlik = getattr(f, "kimlik", "")
    if a is None:
        return kimlik
    k = a.bul(f)
    st.markdown("**📁 Kanıt klasörü**")
    if k is not None:
        c1, c2, c3 = st.columns([3, 1, 1])
        with c1:
            st.caption(f"{k.klasor.relative_to(a.kok)}")
            if k.aves_kod:
                d = kanit_durumu(k)
                st.caption(("✓ Tam metin: " + k.tam_metin.name) if k.tam_metin else "✗ Tam metin yok")
                if d.eksik:
                    st.caption("Eksik: " + " · ".join(d.eksik_aciklamalari()))
                if k.atif_klasorleri():
                    st.caption(f"Atıf kanıtı: {len(k.atif_klasorleri())}")
        with c2:
            if st.button("Klasörü aç", key=f"kac_{didx}", use_container_width=True):
                dosya_ac(k.klasor)
        with c3:
            if k.tam_metin and st.button("Tam metni aç", key=f"tac_{didx}",
                                         use_container_width=True):
                dosya_ac(k.tam_metin)
    else:
        st.caption("Bu faaliyet bir kanıt klasörüne bağlı değil.")

    # Elle bağlama
    secenekler = {"": "— bağlı değil —"}
    for kay in a.kayitlar:
        secenekler[kay.kimlikler[0] if kay.kimlikler else ""] = kay.klasor.name
    for d in a.baglanabilir_klasorler():
        secenekler[a.klasor_kimligi(d)] = str(d.relative_to(a.kok))
    simdiki = kimlik if kimlik in secenekler else (
        (k.kimlikler[0] if k and k.kimlikler else "") if k else "")
    return st.selectbox("Kanıt klasörünü bağla", options=list(secenekler),
                        index=list(secenekler).index(simdiki) if simdiki in secenekler else 0,
                        format_func=secenekler.get, key=f"kbag_{didx}",
                        help="AVES dışı faaliyetleri (ders, proje, hakemlik…) ilgili klasöre "
                             "bağlayabilirsiniz; başvuru dosyasında bu klasörün belgeleri kullanılır.")


# ── AVES aktarımı sonrası klasör işlemleri ─────────────────────────────────
def aves_klasor_islemleri(a: KanitArsivi | None, faaliyetler) -> None:
    if a is None:
        return
    plan = kk.numara_plani(a, faaliyetler)
    if plan:
        st.warning("🔢 AVES'teki sıra değişmiş; şu kanıt klasörlerinin kodu güncellenmeli:\n\n"
                   + "\n".join(f"- `{p.kayit.klasor.name}` → `{p.yeni_ad}`" for p in plan))
        if st.button("Klasörleri yeniden adlandır", key="kanit_numara"):
            kk.numara_uygula(a, plan)
            st.success(f"{len(plan)} klasör yeniden adlandırıldı.")
            st.rerun()
    eksik = kk.eksik_klasorler(a, faaliyetler)
    if eksik:
        st.info(f"📁 AVES'teki {len(eksik)} faaliyetin kanıt klasörü yok: "
                + ", ".join(f.aves_kod for f in eksik[:20]) + ("…" if len(eksik) > 20 else ""))
        if st.button("Eksik klasörleri oluştur", key="kanit_olustur"):
            for f in eksik:
                kk.klasor_olustur(a, f)
            st.success(f"{len(eksik)} klasör oluşturuldu (künye ve kontrol listesiyle).")
            st.rerun()
