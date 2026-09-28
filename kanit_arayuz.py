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
    if f.kimlik.startswith("atif:"):
        return {"Kanıt": "atiflar\\ (kanıtlı sayım)", "Eksik": ""}
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


# ── Aşama 2: kanıt klasöründen doldurma ────────────────────────────────────
def _faaliyet_ekle_ya_da_guncelle(yeni, esle) -> None:
    liste = st.session_state.faaliyetler
    for i, f in enumerate(liste):
        if esle(f):
            liste[i] = yeni
            return
    liste.append(yeni)


def _ders_sayisi_cb(n):
    st.session_state["v_ders"] = n


ENDEKS_ADI = {"5.1": "5.1 SCI/SSCI/AHCI", "5.2": "5.2 ESCI/Scopus", "5.5": "5.5 TR Dizin"}
BELIRSIZ_SECENEK = {"": "Sayılmasın", "5.4": "5.4 Diğer uluslararası hakemli (1 p)",
                    "5.3": "5.3 Diğer uluslararası endeksli (2 p)",
                    "5.6": "5.6 Diğer ulusal hakemli (1 p)"}


def _tarih_bolumu():
    from collections import Counter
    from kanit import tarih
    st.markdown("**1. Yayın tarihleri**")
    bos = [f for f in st.session_state.faaliyetler
           if getattr(f, "aves_kod", "") and not f.yayin_tarihi]
    c1, c2 = st.columns([3, 1])
    with c1:
        st.caption(f"Yayın tarihi boş olan AVES faaliyeti: {len(bos)}. DOI'si olanlar Crossref'ten, "
                   "diğerleri AVES künyesindeki ay/yıldan doldurulur (yalnızca ay biliniyorsa "
                   "ayın 1'i – başvuruyla aynı aydaki eser temkinli olarak 'öncesi' sayılır).")
        internet = st.checkbox("Crossref'i kullan (internet)", value=True, key="kt_crossref")
    with c2:
        if st.button("Tarihleri doldur", disabled=not bos, key="kt_tarih",
                     use_container_width=True):
            with st.spinner("Tarihler bulunuyor…"):
                oneriler = tarih.oneriler(bos, internet=internet)
            for f, o in oneriler:
                f.yayin_tarihi = o.tarih
            c = Counter(o.kaynak for _, o in oneriler)
            st.success(f"{len(oneriler)} tarih dolduruldu: "
                       + ", ".join(f"{k}: {n}" for k, n in c.items()))


def _atif_bolumu(a: KanitArsivi):
    import pandas as pd
    from kanit import atif as ka_atif
    st.markdown("**2. Atıflar (EK-2 5.x)**")
    soyad = ((st.session_state.get("v_ad", "") or "").split() or [""])[-1]
    if st.button("Atıfları kanıt klasöründen say", key="kt_atif_say"):
        with st.spinner("Atıf klasörleri taranıyor…"):
            st.session_state["_kt_atiflar"] = ka_atif.atiflari_topla(a, soyad)
    atiflar = st.session_state.get("_kt_atiflar")
    if atiflar is None:
        st.caption("Her yayın klasörünün atiflar\\ alt klasöründeki atıf yapan yayınlar sayılır; "
                   "endeks yanındaki kanıt belgelerinden okunur, öz atıflar ayıklanır.")
        return
    basvuru = st.session_state.get("v_docent_basvuru")
    tablo = {}
    for (endeks, zaman), n in ka_atif.ozet(atiflar, basvuru).items():
        tablo.setdefault(endeks, {})[zaman] = n
    st.dataframe(pd.DataFrame([
        {"Endeks": ENDEKS_ADI.get(e, "Belirsiz"), "Başvuru sonrası": z.get("sonrası", 0),
         "Başvuru öncesi": z.get("öncesi", 0), "Tarihi bilinmiyor": z.get("bilinmiyor", 0)}
        for e, z in sorted(tablo.items())]), hide_index=True, use_container_width=True)
    belirsiz = [x for x in atiflar if not x.endeks and not x.oz_atif]
    st.caption(f"Toplam {len(atiflar)} atıf yapan yayın · öz atıf (sayılmaz): "
               f"{sum(x.oz_atif for x in atiflar)}"
               + ("" if basvuru else " · doçentlik başvuru tarihi girilmediği için zaman "
                                     "ayrımı yapılamadı"))
    if belirsiz:
        with st.expander(f"Endeksi belirlenemeyen {len(belirsiz)} atıf"):
            st.caption("Klasöre endeks kanıtı (Master Journal List, dizin sayfası) ekleyip ya da "
                       "klasör adına '(SCI)', '(ESCI)', '(TR Dizin)' yazıp yeniden sayabilirsiniz.")
            for x in belirsiz[:100]:
                st.caption(f"{x.atif_yapilan} · {x.yol.relative_to(a.kok)}")
    b1, b2 = st.columns(2)
    with b1:
        belirsiz_kod = st.selectbox("Endeksi belirlenemeyenler", key="kt_belirsiz",
                                    options=list(BELIRSIZ_SECENEK),
                                    format_func=BELIRSIZ_SECENEK.get)
    with b2:
        scholar_kaldir = st.checkbox(
            "Google Scholar'dan gelen atıf (5.1) ve h-endeks (5.9) satırlarını kaldır",
            value=True, key="kt_scholar",
            help="AVES aktarımı Scholar atıf sayısını tek bir 5.1 satırı olarak ekler; "
                 "kanıtlı sayım onun yerine geçer.")
    if st.button("Faaliyet listesine uygula", key="kt_atif_uygula", type="primary"):
        yeni = ka_atif.faaliyetler(atiflar, basvuru, belirsiz_kod or None, t.Faaliyet)
        kalan = [f for f in st.session_state.faaliyetler
                 if not f.kimlik.startswith("atif:")
                 and not (scholar_kaldir and f.kod in ("5.1", "5.9")
                          and not f.kimlik and not f.aves_kod)]
        st.session_state.faaliyetler = kalan + yeni
        st.session_state["_kanit_mesaj2"] = (f"{len(yeni)} atıf satırı eklendi "
                                             f"({sum(f.adet for f in yeni)} atıf).")
        st.rerun()
    if m := st.session_state.pop("_kanit_mesaj2", None):
        st.success(m)


def _ders_bolumu(a: KanitArsivi):
    from kanit import oneri
    st.markdown("**3. Verilen dersler**")
    o = oneri.ders_onerisi(a, None, st.session_state.get("v_docent_unvan"))
    if not o.donemler:
        st.caption("DERS_* klasörlerinde dönem bilgisi bulunamadı.")
        return
    st.caption("Bulunan dönemler: " + ", ".join(d.ad for d in o.donemler))
    d1, d2 = st.columns(2)
    with d1:
        st.caption(f"EK-2 17.4 (son üç yıl): **{len(o.son_uc_yil)} dönem**")
        if st.button("17.4 satırını ekle / güncelle", key="kt_ders174", disabled=not o.son_uc_yil):
            ders = next(d for d in a.diger_klasorler if d.name.upper().startswith("DERS"))
            _faaliyet_ekle_ya_da_guncelle(
                t.Faaliyet("17.4", adet=len(o.son_uc_yil), docent_sonrasi=True,
                           kimlik=a.klasor_kimligi(ders)),
                lambda f: f.kod == "17.4")
            st.rerun()
    with d2:
        if st.session_state.get("v_docent_unvan"):
            st.caption(f"Md. 11(7) doçentlik sonrası yarıyıl: **{len(o.unvan_sonrasi)}** (≥4 gerekli)")
            st.button("Sayıyı Aday Bilgileri'ne yaz", key="kt_ders117",
                      on_click=_ders_sayisi_cb, args=(len(o.unvan_sonrasi),))
        else:
            st.caption("Md. 11(7) için doçentlik unvan tarihini girin.")
    if st.session_state.get("v_kadro") == "profesor" and len(o.unvan_sonrasi) < 4:
        st.warning("⚠️ Doçentlik sonrası ders belgeleri kanıt klasöründe 4 dönemden az. Son "
                   "dönemlerin ders görevlendirme belgelerini DERS_Verilen_Dersler klasörüne "
                   "ekleyin (dosya adında dönem olsun, örn. 2024-2025_GUZ.pdf).")


def _klasorden_ekle_bolumu(a: KanitArsivi):
    from kanit.oneri import KLASOR_KODLARI
    st.markdown("**4. Klasörden faaliyet ekle** (proje, hakemlik, idari görev…)")
    klasorler = [d for d in a.baglanabilir_klasorler() if not d.name.upper().startswith("DERS")]
    if not klasorler:
        st.caption("Bağlanabilecek klasör yok.")
        return
    e1, e2, e3 = st.columns([3, 2, 1])
    with e1:
        sec = st.selectbox("Klasör", options=klasorler, key="kt_klasor",
                           format_func=lambda d: str(d.relative_to(a.kok)))
    onek = sec.relative_to(a.kok).parts[0].split("_")[0].upper()
    kodlar = KLASOR_KODLARI.get(onek, list(t.EK2_PUANLAR))
    with e2:
        kod = st.selectbox("EK-2 kodu", options=kodlar, key="kt_kod",
                           format_func=lambda k: f"{k} – {t.EK2_PUANLAR[k]['ad'][:40]}")
    with e3:
        adet = st.number_input("Adet", min_value=1, value=1, key="kt_adet")
    st.caption("Klasördeki dosyalar: "
               + ", ".join(p.name for p in sorted(sec.rglob("*")) if p.is_file())[:300])
    if st.button("Faaliyet olarak ekle", key="kt_klasor_ekle"):
        st.session_state.faaliyetler.append(t.Faaliyet(kod, adet=int(adet),
                                                       kimlik=a.klasor_kimligi(sec)))
        st.rerun()


def doldurma_bolumu(a: KanitArsivi | None) -> None:
    """Faaliyetler sekmesindeki 'Kanıt klasöründen doldur' bölümü."""
    if a is None:
        return
    with st.expander("🗂️ Kanıt klasöründen doldur (tarih, atıf, ders, klasörden faaliyet)"):
        _tarih_bolumu()
        st.divider()
        _atif_bolumu(a)
        st.divider()
        _ders_bolumu(a)
        st.divider()
        _klasorden_ekle_bolumu(a)


# ── Kanıt denetimi (sonuç ekranı) ──────────────────────────────────────────
def denetim_bolumu(faaliyetler, a: KanitArsivi | None) -> list:
    """Sonuç ekranında eksik kanıt uyarıları; uyarı listesini döndürür (PDF için)."""
    if a is None:
        return []
    import pandas as pd
    from kanit.denetim import denetle
    uyarilar = denetle(faaliyetler, a)
    st.markdown('<div class="card-title">KANIT DENETİMİ</div>', unsafe_allow_html=True)
    if not uyarilar:
        st.success("✓ Puan alan tüm faaliyetlerin kanıtları kanıt klasöründe görünüyor.")
        return uyarilar
    st.warning(f"⚠️ {len(uyarilar)} faaliyetin kanıtı eksik görünüyor. Puan hesabı değişmez; "
               "ancak yönerge (Md. 7) tüm faaliyetlerin belgelenmesini şart koşar.")
    st.dataframe(pd.DataFrame([{"#": u.sira, "AVES": u.aves_kod or "—", "EK-2": u.kod,
                                "Faaliyet": u.ad[:45], "Eksik": " · ".join(u.eksikler)}
                               for u in uyarilar]), hide_index=True, use_container_width=True)
    return uyarilar
