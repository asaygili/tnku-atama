"""
Streamlit arayüzünün kanıt arşivi bölümleri (yalnızca yerelde çalışır).

Kanıt klasörü bulunamazsa (örn. Streamlit Cloud) bu bölümler kendiliğinden gizlenir;
program kanıt klasörü olmadan eskisi gibi çalışır.
"""

from __future__ import annotations

import os
import sys
import time
from datetime import date
from pathlib import Path

import streamlit as st

import arayuz_tema as ui
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
    ui.kart_basligi("KANIT KLASÖRÜ (YEREL)")
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
            if st.button("Klasörü aç", key=f"kac_{didx}", use_container_width=True, help="Bu faaliyetin kanıt klasörünü Dosya Gezgini'nde açar."):
                dosya_ac(k.klasor)
        with c3:
            if k.tam_metin and st.button("Tam metni aç", key=f"tac_{didx}",
                                         use_container_width=True, help="Yayının tam metin PDF'ini açar."):
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
        if st.button("Klasörleri yeniden adlandır", key="kanit_numara", help="AVES'teki sıra değiştiği için kanıt klasörlerinin kodlarını (UM01, UB03…) günceller. Dosyalara dokunulmaz."):
            kk.numara_uygula(a, plan)
            st.success(f"{len(plan)} klasör yeniden adlandırıldı.")
            st.rerun()
    eksik = kk.eksik_klasorler(a, faaliyetler)
    if eksik:
        st.info(f"📁 AVES'teki {len(eksik)} faaliyetin kanıt klasörü yok: "
                + ", ".join(f.aves_kod for f in eksik[:20]) + ("…" if len(eksik) > 20 else ""))
        if st.button("Eksik klasörleri oluştur", key="kanit_olustur", help='Kanıt klasörü olmayan yayınlar için künyeli boş klasör açar; belgeleri sonra içine koyarsınız.'):
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


ENDEKS_ADI = {"5.1": "5.1 SCI/SSCI/AHCI", "5.2": "5.2 ESCI/Scopus", "5.5": "5.5 TR Dizin",
              "5.7": "5.7 Uluslararası kitap (BKCI)"}
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
        internet = st.checkbox("Crossref'i kullan (internet)", value=True, key="kt_crossref", help="DOI'si olan yayınların tarihini Crossref'ten alır (internet gerekir). Kapalıysa AVES künyesindeki tarih kullanılır.")
    with c2:
        if st.button("Tarihleri doldur", disabled=not bos, key="kt_tarih",
                     use_container_width=True, help='Tarihi boş olan yayınlara yayın tarihini otomatik yazar. Doçentlik öncesi/sonrası ayrımı için gereklidir.'):
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
    if st.button("Atıfları kanıt klasöründen say", key="kt_atif_say", help='Yayın klasörlerinizin atiflar\\ alt klasörlerindeki atıf yapan yayınları sayar; endeksi ve öz atıfları ayırır.'):
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
                                    format_func=BELIRSIZ_SECENEK.get, help="Endeksi okunamayan atıfların hangi EK-2 koduyla sayılacağı. Emin değilseniz 'Ekleme' seçin.")
    with b2:
        scholar_kaldir = st.checkbox(
            "Google Scholar'dan gelen atıf (5.1) ve h-endeks (5.9) satırlarını kaldır",
            value=True, key="kt_scholar",
            help="AVES aktarımı Scholar atıf sayısını tek bir 5.1 satırı olarak ekler; "
                 "kanıtlı sayım onun yerine geçer.")
    if st.button("Faaliyet listesine uygula", key="kt_atif_uygula", type="primary", help='Sayılan atıfları EK-2 5.x satırları olarak faaliyet listesine ekler (önceki atıf satırlarının yerine geçer).'):
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


def _wos_bolumu(a: KanitArsivi):
    import pandas as pd
    from collections import Counter
    from kanit import wos
    st.markdown("**2b. Web of Science atıf dışa aktarımından atıf klasörleri**")
    st.caption("WoS: yayınlarınız → Create Citation Report → Citing articles (Without self-citations) "
               "→ Web of Science Index süzgeci (SCI-EXPANDED, SSCI, A&HCI, ESCI, BKCI) → Export → "
               "'Tab delimited file', Record content: 'Full Record and Cited References'.")
    if (a.kok / wos.INDIRILECEK_LISTESI).exists():
        if st.button("Tam metni eksik atıflar için açık erişimi yeniden dene", key="kt_wos_yeniden", help="Tam metni olmayan atıflar için açık erişimli PDF'i yeniden arar ve bulursa indirir."):
            cubuk = st.progress(0.0, text="Açık erişim aranıyor…")
            sayac = wos.eksikleri_indir(
                a, ilerleme=lambda i, n, p: cubuk.progress(i / n, text=f"{i}/{n}"))
            st.success(f"İndirilen: {sayac['indirildi']} · hâlâ eksik: {sayac['indirilemedi']}")
        st.caption(f"MDPI, PeerJ, Wiley gibi siteler otomatik indirmeyi engeller. "
                   f"{wos.INDIRILECEK_LISTESI} listesindeki 'PDF bağlantısı'na tarayıcınızda "
                   "tıklayıp indirin, sonra indirilen klasörü aşağıda seçin: PDF'ler DOI'lerine "
                   "göre ilgili atıf klasörüne yerleştirilir.")
        y1, y2 = st.columns([3, 1])
        with y1:
            ind = st.text_input("İndirilen PDF'lerin klasörü", key="kt_indirilen",
                                value=str(Path.home() / "Downloads"), help="Tarayıcıdan indirdiğiniz atıf PDF'lerinin bulunduğu klasör (genellikle İndirilenler).")
        with y2:
            if st.button("Klasörlere yerleştir", key="kt_yerlestir",
                         disabled=not Path(ind).is_dir(), help="Bu klasördeki PDF'leri ilk sayfalarındaki DOI ya da başlığa göre doğru atıf klasörüne kopyalar."):
                sayac = wos.indirilenleri_yerlestir(a, Path(ind))
                st.session_state.pop("_kt_atiflar", None)
                st.success(f"Yerleştirilen: {sayac['yerleştirildi']} · eşleşmeyen PDF: "
                           f"{sayac['eşleşmedi']}")
                guncel = a.kok / (Path(wos.INDIRILECEK_LISTESI).stem + " (güncel).xlsx")
                if guncel.exists() and guncel.stat().st_mtime > time.time() - 60:
                    st.info(f"{wos.INDIRILECEK_LISTESI} Excel'de açık olduğu için güncel liste "
                            f"'{guncel.name}' adıyla kaydedildi.")
    yuklenen = st.file_uploader("WoS dışa aktarım dosyası (.txt / .xlsx)", type=["txt", "xlsx"],
                                accept_multiple_files=True, key="kt_wos_dosya", help="Web of Science'tan indirdiğiniz 'atıf yapan yayınlar' dosyasını buraya sürükleyin.")
    if not yuklenen:
        return
    hedef_klasor = a.kok / "_WoS"
    hedef_klasor.mkdir(exist_ok=True)
    kayitlar = []
    for dosya in yuklenen:
        yol = hedef_klasor / dosya.name
        yol.write_bytes(dosya.getvalue())
        try:
            kayitlar += wos.oku(yol)
        except ValueError as e:
            st.error(f"{dosya.name}: {e}")
    if not kayitlar:
        return
    w1, w2 = st.columns(2)
    with w1:
        esci = st.checkbox("ESCI (5.2) ve Book Citation Index (5.7) atıflarını da ekle",
                           value=True, key="kt_wos_esci", help='İşaretliyse yalnızca SCI değil ESCI ve kitap (BKCI) atıfları da klasörlenir.')
    with w2:
        indir = st.checkbox("Açık erişimli tam metinleri indir", value=True, key="kt_wos_indir", help="Atıf yapan yayın açık erişimliyse PDF'ini de indirip klasörüne koyar.")
    soyad = ((st.session_state.get("v_ad", "") or "").split() or [""])[-1]
    plan = wos.plan_olustur(a, kayitlar, soyad, ("5.1", "5.2", "5.7") if esci else ("5.1",))
    tablo = {}
    for p in plan:
        if p.hedef is not None:
            tablo.setdefault(p.hedef.aves_kod, Counter())[p.durum] += 1
    st.dataframe(pd.DataFrame([{"Yayın": k, "Yeni": c["yeni"], "Zaten var": c["zaten var"],
                                "Öz atıf": c["öz atıf"], "Kapsam dışı": c["kapsam dışı"]}
                               for k, c in sorted(tablo.items())]),
                 hide_index=True, use_container_width=True)
    esles = sum(1 for p in plan if p.durum == "eşleşmedi")
    yeni = sum(1 for p in plan if p.durum == "yeni")
    st.caption(f"{len(kayitlar)} WoS kaydı · yeni atıf klasörü: {yeni}"
               + (f" · hiçbir yayınınızla eşleşmeyen: {esles} (kaynakçada DOI / cilt-sayfa "
                  "bulunamadı)" if esles else ""))
    if st.button(f"{yeni} atıf klasörünü oluştur", key="kt_wos_uygula", disabled=not yeni,
                 type="primary", help='Yeni bulunan her atıf yapan yayın için ilgili yayınınızın atiflar\\ klasöründe bir alt klasör açar.'):
        cubuk = st.progress(0.0, text="Atıf klasörleri oluşturuluyor…")
        sayac = wos.uygula(plan, a, indir=indir,
                           ilerleme=lambda i, n, p: cubuk.progress(i / n, text=f"{i}/{n} {p.wos.baslik[:60]}"))
        st.session_state.pop("_kt_atiflar", None)       # sayım yenilensin
        st.success(f"{sayac['tam metin indirildi'] + sayac['tam metin indirilecek']} klasör oluşturuldu · "
                   f"açık erişimli tam metin: {sayac['tam metin indirildi']} · "
                   f"indirmeniz gereken: {sayac['tam metin indirilecek']}"
                   + (f" (liste: {a.kok / wos.INDIRILECEK_LISTESI})"
                      if sayac["tam metin indirilecek"] else "")
                   + ". Şimdi 'Atıfları kanıt klasöründen say' ile sayımı yenileyin.")


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
        if st.button("17.4 satırını ekle / güncelle", key="kt_ders174", disabled=not o.son_uc_yil, help='Ders klasörlerinden bulunan son üç yıldaki dönem sayısıyla EK-2 17.4 satırını ekler.'):
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
                      on_click=_ders_sayisi_cb, args=(len(o.unvan_sonrasi),), help="Doçentlik sonrası bulunan ders dönemi sayısını Aday Bilgileri'ndeki ilgili alana yazar.")
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
                           format_func=lambda d: str(d.relative_to(a.kok)), help='Faaliyet olarak eklemek istediğiniz kanıt klasörü (proje, hakemlik, idari görev…).')
    onek = sec.relative_to(a.kok).parts[0].split("_")[0].upper()
    kodlar = KLASOR_KODLARI.get(onek, list(t.EK2_PUANLAR))
    with e2:
        kod = st.selectbox("EK-2 kodu", options=kodlar, key="kt_kod",
                           format_func=lambda k: f"{k} – {t.EK2_PUANLAR[k]['ad'][:40]}", help='Bu klasördeki faaliyetin EK-2 kodu.')
    with e3:
        adet = st.number_input("Adet", min_value=1, value=1, key="kt_adet", help='Bu klasördeki faaliyetin adedi (yıl, dönem ya da sayı).')
    st.caption("Klasördeki dosyalar: "
               + ", ".join(p.name for p in sorted(sec.rglob("*")) if p.is_file())[:300])
    if st.button("Faaliyet olarak ekle", key="kt_klasor_ekle", help='Seçtiğiniz klasörü, seçtiğiniz EK-2 koduyla faaliyet listesine ekler ve kanıt olarak bağlar.'):
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
        _wos_bolumu(a)
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
    ui.kart_basligi("KANIT DENETİMİ")
    if not uyarilar:
        st.success("✓ Puan alan tüm faaliyetlerin kanıtları kanıt klasöründe görünüyor.")
        return uyarilar
    st.warning(f"⚠️ {len(uyarilar)} faaliyetin kanıtı eksik görünüyor. Puan hesabı değişmez; "
               "ancak yönerge (Md. 7) tüm faaliyetlerin belgelenmesini şart koşar.")
    st.dataframe(pd.DataFrame([{"#": u.sira, "AVES": u.aves_kod or "—", "EK-2": u.kod,
                                "Faaliyet": u.ad[:45], "Eksik": " · ".join(u.eksikler)}
                               for u in uyarilar]), hide_index=True, use_container_width=True)
    return uyarilar


# ── Aşama 3: başvuru dosyası (USB klasörü + birleşik PDF) ──────────────────
GENEL_BELGE_KLASORLERI = ("_Docentlik_Basvuru_Belgeleri", "_Kisisel_Belgeler", "_Genel_Belgeler",
                          "_Atama_2019_Basvuru_Belgeleri")
GENEL_BELGE_ONSECIM = ("yabanci dil", "yabancı dil", "doktora", "diploma", "docentlik belgesi",
                       "doçentlik belgesi", "ozgecmis", "özgeçmiş")


def _genel_belge_adaylari(a: KanitArsivi) -> list[Path]:
    sonuc = []
    for ad in GENEL_BELGE_KLASORLERI:
        d = a.kok / ad
        if d.is_dir():
            sonuc += sorted(p for p in d.rglob("*") if p.is_file()
                            and p.suffix.lower() in (".pdf", ".jpg", ".jpeg", ".png", ".docx", ".doc"))
    return sonuc


def paket_bolumu(aday, sonuc, a: KanitArsivi | None, rapor_pdf) -> None:
    """Sonuç ekranında başvuru dosyası hazırlama. rapor_pdf: (aday, sonuc) → bytes."""
    if a is None:
        return
    from kanit import paket
    ui.kart_basligi("BAŞVURU DOSYASI (USB KLASÖRÜ + BİRLEŞİK PDF)")
    st.caption("Puan alan faaliyetler EK-2 sırasıyla, tam metin ve kanıtlarıyla birlikte hazırlanır "
               "(Md. 6(1): fiziksel dosya + USB). Kaynak klasörlere dokunulmaz.")
    s1, s2 = st.columns(2)
    with s1:
        atif_k = st.checkbox("Atıf kanıtlarını ekle", value=True, key="pk_atif", help='Atıf yapan yayınların ilk sayfası ve atıf sayfası dosyaya eklenir.')
        atif_tam = st.checkbox("Yalnızca tam metni olan atıfları ekle", value=False, key="pk_atif_tam",
                               help="Tam metni olan atıflar her durumda önce gelir. İşaretlenirse "
                                    "yalnızca WoS kaydıyla belgelenen atıflar dosyaya girmez "
                                    "(puanda sayılmaya devam eder; kalemde not düşülür).")
        oncesi = st.checkbox("Doçentlik başvurusu öncesi faaliyetleri de ekle", value=True,
                             key="pk_oncesi", help='Kapalıysa yalnızca doçentlik başvurusu sonrası faaliyetlerin kanıtları dosyaya girer.')
    with s2:
        kitap = st.checkbox("Bildiri kitaplarının tamamını ekle (yoksa kesilmiş sayfalar)",
                            value=False, key="pk_kitap", help='Kapalıysa bildiri kitabından yalnızca kapak, künye ve bildirinizin sayfaları alınır (dosya küçük kalır).')
        hafif = st.checkbox("Birleşik PDF'i hafiflet (taranmış belgeler 110 dpi)", value=True,
                            key="pk_hafif", help="USB klasöründeki dosyalar özgün kalır; tam "
                                                  "metinlere dokunulmaz.")
    adaylar = _genel_belge_adaylari(a)
    onsecim = [p for p in adaylar
               if any(x in p.name.lower().replace("ı", "i") for x in GENEL_BELGE_ONSECIM)]
    genel = st.multiselect("Genel belgeler (dosyanın başına eklenir)", options=adaylar,
                           default=onsecim, key="pk_genel",
                           format_func=lambda p: str(p.relative_to(a.kok)), help='Özgeçmiş, diploma, yabancı dil belgesi gibi her başvuruda istenen belgeler.')
    cikti = st.text_input("Çıktı klasörü", value=str(a.kok / "_Basvuru_Dosyalari"),
                          key="pk_cikti", help='Başvuru dosyasının (USB klasörü ve birleşik PDF) kaydedileceği yer.')
    if st.button("📦 Başvuru dosyasını hazırla", type="primary", key="pk_hazirla", help="Puan alan faaliyetleri kanıtlarıyla birlikte EK-2 sırasına dizer; USB'ye kopyalanacak klasörü ve yazdırılacak tek PDF'i oluşturur."):
        ayar = paket.PaketAyarlari(atif_kanitlari=atif_k, docent_oncesi=oncesi,
                                   atif_yalniz_tam_metin=atif_tam,
                                   tam_bildiri_kitabi=kitap, hafiflet=hafif, genel_belgeler=genel)
        with st.spinner("Başvuru dosyası hazırlanıyor… (büyük arşivlerde birkaç dakika sürebilir)"):
            try:
                st.session_state["_pk_sonuc"] = paket.paket_olustur(
                    aday, sonuc, a, Path(cikti), rapor_pdf(aday, sonuc), ayar)
            except Exception as e:  # noqa: BLE001 – kullanıcıya göster
                st.session_state["_pk_sonuc"] = None
                st.error(f"Başvuru dosyası hazırlanamadı: {e}")
    ps = st.session_state.get("_pk_sonuc")
    if ps is None:
        return
    usb_mb = sum(p.stat().st_size for p in ps.klasor.rglob("*") if p.is_file()) / 1e6
    st.success(f"✅ {len(ps.kalemler)} faaliyet · birleşik PDF {ps.sayfa} sayfa, "
               f"{ps.boyut_mb:.0f} MB · USB klasörü {usb_mb:.0f} MB\n\n`{ps.klasor}`")
    b1, b2 = st.columns(2)
    with b1:
        if st.button("📂 Klasörü aç", key="pk_klasor_ac", use_container_width=True, help="Hazırlanan USB klasörünü Dosya Gezgini'nde açar."):
            dosya_ac(ps.klasor)
    with b2:
        if st.button("📄 Birleşik PDF'i aç", key="pk_pdf_ac", use_container_width=True, help="Yazdırılmaya hazır birleşik PDF'i açar."):
            dosya_ac(ps.pdf)
    eksikli = [k for k in ps.kalemler if k.eksikler or not k.dosyalar]
    if eksikli:
        st.warning(f"{len(eksikli)} faaliyetin kanıtı eksik; klasörlerine EKSIK.txt yazıldı.")
    yanlis = [y for k in ps.kalemler for y in k.yanlis_yer]
    if yanlis:
        with st.expander(f"Başka bir yayına ait göründüğü için dahil edilmeyen {len(yanlis)} dosya"):
            st.caption("Bu dosyalar kanıt arşivinde yanlış klasörde duruyor olabilir.")
            for y in yanlis:
                st.caption(y)
    if ps.pdf_disi:
        with st.expander(f"Birleşik PDF'e alınmayan {len(ps.pdf_disi)} dosya (USB'de mevcut)"):
            for y in ps.pdf_disi:
                st.caption(y)
