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
import tnku_atama as t

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

# ─────────────────────────────────────────────────────────────────────────────
# Özel CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.header-bar {
    background: #1A2B4A;
    padding: 14px 22px;
    border-radius: 8px;
    margin-bottom: 18px;
}
.header-bar h2 { color: white; margin: 0 0 2px 0; font-size: 1.25em; }
.header-bar small { color: #A8C8F0; font-size: 0.82em; }
.sonuc-ok   { background:#1A7A3A; color:white; padding:14px; border-radius:6px;
              text-align:center; font-size:1.1em; font-weight:bold; margin:8px 0; }
.sonuc-fail { background:#C0392B; color:white; padding:14px; border-radius:6px;
              text-align:center; font-size:1.1em; font-weight:bold; margin:8px 0; }
.kriter-ok   { background:#E8F5E9; border-left:4px solid #1A7A3A;
               padding:6px 14px; margin:2px 0; border-radius:0 4px 4px 0;
               font-size:0.9em; }
.kriter-fail { background:#FFEBEE; border-left:4px solid #C0392B;
               padding:6px 14px; margin:2px 0; border-radius:0 4px 4px 0;
               font-size:0.9em; }
.kriter-info { background:#FFF8E1; border-left:4px solid #F9A825;
               padding:6px 14px; margin:2px 0; border-radius:0 4px 4px 0;
               font-size:0.9em; }
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
    8: "TV–Sinema–Tasarım",
    9: "Sanat ve Tasarım",
    10: "Sportif Etkinlikler",
    11: "Patentler ve Girişimler",
    12: "Projeler",
    13: "Çalıştay / Kongre (max 20p)",
    14: "Ödüller",
    15: "Kazı Çalışmaları",
    16: "Yurt Dışı Deneyimi",
    17: "Eğitim–Öğretim",
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
    "Tescilli (tam puan)":            "tescilli",
    "Araştırma raporu almış (×0.5)":  "arastirma_raporu",
    "Başvuru aşaması (×0.25)":        "basvuru",
}


# ─────────────────────────────────────────────────────────────────────────────
# Yardımcı Fonksiyonlar
# ─────────────────────────────────────────────────────────────────────────────

def _tur_renk(val: str) -> str:
    """DataFrame stillemesi için puan türüne göre renk."""
    return ("background-color: #EAF4E8" if val == "PUAN-1"
            else "background-color: #EAF0FA")


def _aday_olustur() -> t.AdayBilgi:
    """Session state'teki widget değerlerinden AdayBilgi nesnesi oluşturur."""
    alan_raw = st.session_state.get("v_alan", "ALAN-1")
    alan = "ALAN-1" if "ALAN-1" in alan_raw else "ALAN-2"
    kadro = st.session_state.get("v_kadro", "dr_ilk")
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
    """Mevcut faaliyetleri DataFrame satırlarına dönüştürür."""
    rows = []
    for i, f in enumerate(st.session_state.faaliyetler):
        bilgi_f = t.EK2_PUANLAR.get(f.kod, {})
        p_f, _ = t.faaliyet_puan_hesapla(f)
        p1_f   = t.is_puan1(f.kod, kadro_su)
        grup   = bilgi_f.get("grup", 0)
        ek     = f.q_degeri or {
            "tescilli": "Tescil",
            "arastirma_raporu": "ArRapor",
            "basvuru": "Baş.",
        }.get(f.patent_durum or "", "")
        rows.append({
            "#":       i + 1,
            "Kod":     f.kod,
            "Faaliyet": bilgi_f.get("ad", "")[:60],
            "Adet":    f.adet,
            "Top.Yz.": f.toplam_yazar if grup in {1, 2, 3} else "–",
            "Sıra":    ("Sor/Sny" if f.sorumlu_veya_senyör else str(f.yazar_sirasi))
                       if grup in {1, 2, 3} else "–",
            "Q/Pat.":  ek,
            "Puan":    round(p_f, 2),
            "Tür":     "PUAN-1" if p1_f else "PUAN-2",
            "Doç.Sn.": "✓" if f.docent_sonrasi else "",
        })
    return rows


def _bul_font(dosya: str) -> str | None:
    klasorler = [
        r"C:\Windows\Fonts",
        r"C:\Windows\fonts",
        os.path.expanduser("~/.fonts"),
        "/usr/share/fonts/truetype/dejavu",
        "/System/Library/Fonts",
    ]
    for k in klasorler:
        yol = os.path.join(k, dosya)
        if os.path.exists(yol):
            return yol
    return None


def _pdf_bytes(aday: t.AdayBilgi, sonuc: dict) -> bytes:
    """PDF raporu oluşturup bytes olarak döndürür."""
    buf = io.BytesIO()

    fr, fb = "Helvetica", "Helvetica-Bold"
    for fn, bn in [("arial.ttf", "arialbd.ttf"),
                   ("Arial.ttf", "ArialBold.ttf"),
                   ("DejaVuSans.ttf", "DejaVuSans-Bold.ttf")]:
        ry = _bul_font(fn)
        if ry:
            try:
                pdfmetrics.registerFont(TTFont("TRR", ry))
                by = _bul_font(bn)
                if by:
                    pdfmetrics.registerFont(TTFont("TRB", by))
                    fb = "TRB"
                fr = "TRR"
                break
            except Exception:
                pass

    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=1.8 * cm, rightMargin=1.8 * cm,
        topMargin=2 * cm, bottomMargin=1.8 * cm,
    )

    def sty(name, sz=9, bold=False, **kw):
        return ParagraphStyle(name, fontName=fb if bold else fr,
                              fontSize=sz, leading=sz + 4, **kw)

    s_title = sty("t", 14, True, textColor=colors.HexColor("#1A2B4A"),
                  alignment=1, spaceAfter=3)
    s_sub   = sty("s", 9, False, textColor=colors.HexColor("#2E5DA3"),
                  alignment=1, spaceAfter=10)
    s_sec   = sty("sc", 11, True, textColor=colors.HexColor("#2E5DA3"),
                  spaceBefore=10, spaceAfter=4)
    s_xs    = sty("xs", 8, False, textColor=colors.HexColor("#555555"))

    def tbl_style(hdr_color=None):
        hdr_color = hdr_color or colors.HexColor("#2E5DA3")
        return TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0), hdr_color),
            ("TEXTCOLOR",     (0, 0), (-1, 0), colors.white),
            ("FONTNAME",      (0, 0), (-1, 0), fb),
            ("FONTSIZE",      (0, 0), (-1, 0), 8),
            ("TOPPADDING",    (0, 0), (-1, 0), 6),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
            ("FONTNAME",      (0, 1), (-1, -1), fr),
            ("FONTSIZE",      (0, 1), (-1, -1), 8),
            ("TOPPADDING",    (0, 1), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 3),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.white, colors.HexColor("#F4F7FF")]),
            ("GRID",          (0, 0), (-1, -1), 0.3, colors.HexColor("#CCCCCC")),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ])

    kadro_adi = {
        "dr_ilk":     "Dr. Öğretim Üyesi – İlk Atanma",
        "dr_yeniden": f"Dr. Öğretim Üyesi – Yeniden Atanma ({aday.yeniden_sure} Yıl)",
        "docent":     "Doçent",
        "profesor":   "Profesör",
    }.get(aday.kadro_turu, "–")

    pnlar  = sonuc["puanlar"]
    genel  = sonuc["genel_sonuc"]
    W, _H  = A4

    elems = []
    elems.append(Paragraph("TEKIRDAĞ NAMIK KEMAL ÜNİVERSİTESİ", s_title))
    elems.append(Paragraph("Öğretim Üyeliği – Atama Puanlama Raporu", s_sub))
    elems.append(Paragraph("EYS-YNG-129  |  28.03.2025", s_xs))
    elems.append(HRFlowable(width="100%", thickness=2,
                             color=colors.HexColor("#2E5DA3")))
    elems.append(Spacer(1, 8))

    ad_data = [
        ["Aday", "Alan", "Kadro", "Tarih"],
        [aday.ad_soyad, aday.alan, kadro_adi,
         datetime.date.today().strftime("%d.%m.%Y")],
    ]
    at = Table(ad_data, colWidths=[3.5 * cm, 3.5 * cm, 8 * cm, 2.5 * cm])
    at.setStyle(tbl_style())
    elems.append(at)
    elems.append(Spacer(1, 10))

    gtxt = ("✓  TÜM KRİTERLER SAĞLANIYOR – BAŞVURU YAPILABİLİR"
            if genel else
            "✗  BAZI KRİTERLER SAĞLANMIYOR – BAŞVURU YAPILAMAZ")
    gc = colors.HexColor("#1A7A3A") if genel else colors.HexColor("#C0392B")
    gt = Table([[gtxt]], colWidths=[W - 3.6 * cm])
    gt.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), gc),
        ("TEXTCOLOR",     (0, 0), (-1, -1), colors.white),
        ("FONTNAME",      (0, 0), (-1, -1), fb),
        ("FONTSIZE",      (0, 0), (-1, -1), 11),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    elems.append(gt)
    elems.append(Spacer(1, 10))

    elems.append(Paragraph("PUAN ÖZETİ", s_sec))
    pdata = [
        ["Puan Türü", "Değer"],
        ["PUAN-1  (EK-2 bölüm 1–6 kapsamı)",    f"{pnlar['puan1']:.2f}"],
        ["PUAN-2  (EK-2 tamamı – kalan)",         f"{pnlar['puan2']:.2f}"],
        ["TOPLAM PUAN",                           f"{pnlar['toplam']:.2f}"],
    ]
    pts = tbl_style()
    pts.add("FONTNAME",   (0, 3), (-1, 3), fb)
    pts.add("FONTSIZE",   (0, 3), (-1, 3), 10)
    pts.add("BACKGROUND", (0, 3), (-1, 3), colors.HexColor("#D6E4F7"))
    pt = Table(pdata, colWidths=[13 * cm, 4.5 * cm])
    pt.setStyle(pts)
    elems.append(pt)
    elems.append(Spacer(1, 10))

    elems.append(Paragraph("KRİTER KONTROL SONUÇLARI", s_sec))
    kdata = [["#", "Kriter", "Durum", "Not"]]
    for i, kr in enumerate(sonuc["kriterler"], 1):
        ok = "✓" in kr["durum"]
        kdata.append([
            str(i), kr["kriter"],
            "✓ SAĞLANIYOR" if ok else "✗ SAĞLANMIYOR",
            kr["notlar"],
        ])
    kts = tbl_style()
    for ri, kr in enumerate(sonuc["kriterler"], 1):
        ok = "✓" in kr["durum"]
        info = "(f) Bilgi:" in kr["kriter"]
        if info:
            bg = colors.HexColor("#FFF8E1")
            tc = colors.HexColor("#F57F17")
        elif ok:
            bg = colors.HexColor("#E8F5E9")
            tc = colors.HexColor("#1A7A3A")
        else:
            bg = colors.HexColor("#FFEBEE")
            tc = colors.HexColor("#C0392B")
        kts.add("BACKGROUND", (0, ri), (-1, ri), bg)
        kts.add("TEXTCOLOR",  (2, ri), (2, ri),  tc)
        kts.add("FONTNAME",   (2, ri), (2, ri),  fb)
    kt = Table(kdata, colWidths=[0.7 * cm, 9.5 * cm, 3 * cm, 4.3 * cm])
    kt.setStyle(kts)
    elems.append(kt)
    elems.append(Spacer(1, 10))

    elems.append(Paragraph("FAALİYET DETAYI", s_sec))
    fdata = [["Kod", "Faaliyet", "Adet", "Puan", "Tür"]]
    for d in pnlar["detaylar"]:
        fdata.append([
            d["kod"], d["ad"][:70], str(d["adet"]),
            f"{d['puan']:.2f}",
            "PUAN-1" if d["puan1_mi"] else "PUAN-2",
        ])
    fts = tbl_style()
    for ri, d in enumerate(pnlar["detaylar"], 1):
        fts.add("BACKGROUND", (0, ri), (-1, ri),
                colors.HexColor("#EAF4E8") if d["puan1_mi"]
                else colors.HexColor("#EAF0FA"))
    ft = Table(fdata, colWidths=[1.2 * cm, 11 * cm, 1 * cm, 1.5 * cm, 2 * cm])
    ft.setStyle(fts)
    elems.append(ft)
    elems.append(Spacer(1, 14))

    elems.append(HRFlowable(width="100%", thickness=0.4,
                             color=colors.HexColor("#AAAAAA")))
    elems.append(Spacer(1, 4))
    elems.append(Paragraph(
        "Bu rapor TNKÜ EYS-YNG-129 yönergesi kapsamında otomatik olarak "
        "oluşturulmuştur. Resmi başvurularda ilgili birime danışınız.", s_xs))

    doc.build(elems)
    buf.seek(0)
    return buf.read()


# ─────────────────────────────────────────────────────────────────────────────
# Başlık
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="header-bar">
  <h2>TNKÜ &nbsp;·&nbsp; Öğretim Üyeliği Kadrosu – Atama Puanlama Sistemi</h2>
  <small>EYS-YNG-129 &nbsp;·&nbsp; 28.03.2025 &nbsp;·&nbsp;
  Tekirdağ Namık Kemal Üniversitesi</small>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Sekmeler
# ─────────────────────────────────────────────────────────────────────────────
tab1, tab2 = st.tabs([
    "📋  1 · Aday Bilgileri",
    "➕  2 · Faaliyetler",
])

# ═══════════════════════════════════════ TAB 1 – ADAY BİLGİLERİ ══════════════
with tab1:

    col_kimlik, col_kadro = st.columns(2)

    with col_kimlik:
        st.subheader("Kimlik Bilgileri")
        st.text_input("Ad Soyad", key="v_ad", placeholder="Adınız Soyadınız")
        st.selectbox("Akademik Alan", key="v_alan", options=[
            "ALAN-1  –  Fen / Sağlık / Müh. / Matematik vb.",
            "ALAN-2  –  Sosyal / İdari / Eğitim / Güzel Sanatlar vb.",
        ])
        st.checkbox(
            "Güzel Sanatlar alanı  (PUAN-1 için %50 yeterli)",
            key="v_guzel",
        )

    with col_kadro:
        st.subheader("Kadro Türü")
        st.radio(
            "Başvuru yapılan kadro",
            key="v_kadro",
            options=["dr_ilk", "dr_yeniden", "docent", "profesor"],
            format_func=lambda x: KADRO_ADI[x],
        )
        if st.session_state.get("v_kadro") == "dr_yeniden":
            st.selectbox(
                "Yeniden Atama Süresi",
                key="v_sure",
                options=[3, 2, 1],
                format_func=lambda x: f"{x} Yıl",
            )

    st.divider()
    st.subheader("Genel Koşullar")

    gc1, gc2, gc3 = st.columns(3)
    with gc1:
        st.checkbox("Doktora / Uzmanlık / Yeterlilik", key="v_doktora",
                    help="Tıp uzm., Diş Hek. uzm., Eczacılık uzm. veya Güzel Sanatlar yeterlilik")
        st.checkbox("ÜAK Doçent unvanı", key="v_uak",
                    help="Üniversitelerarası Kuruldan alınmış doçentlik unvanı")
    with gc2:
        st.checkbox("ÜAK sözlü sınavına girdi ve başarılı oldu", key="v_sifahi",
                    help="Doçent için zorunlu · Profesör'de işaretlenmezse: örnek ders zorunlu + puan eşikleri %20 artar")
        st.checkbox("Örnek ders 'Başarılı'", key="v_ornek",
                    help="Dr. Öğr. Üyesi için zorunlu; sözlü sınavsız Profesör başvurusunda da zorunlu")
    with gc3:
        st.checkbox("Başlıca Araştırma Eseri eklendi", key="v_baslica",
                    help="Prof. başvurusu için zorunlu; doçent sonrası, başlıca yazar")
        st.checkbox("Çalışma alanı yabancı dil bölümü", key="v_ydbol",
                    help="Bu durumda YÖKDİL/YDS puanı ≥85 aranır")

    dl1, dl2, dl3 = st.columns(3)
    with dl1:
        st.number_input(
            "YÖKDİL / YDS Puanı", key="v_ydpuan",
            min_value=0.0, max_value=100.0, step=0.5,
            help="Dr. Öğr. Üyesi ≥60  |  Doçent/Prof. ≥65  |  Yab. Dil Böl. ≥85",
        )
    with dl2:
        st.number_input(
            "Farklı yarıyıl ders sayısı", key="v_ders",
            min_value=0, max_value=60, step=1,
            help="Doçent ve Prof. için ≥4 farklı yarıyıl gerekli",
        )
    with dl3:
        st.number_input(
            "Doçent sonrası yükseköğretimde süre (yıl)", key="v_docsure",
            min_value=0.0, max_value=40.0, step=0.5,
            help="Prof. için ≥2.5 yıl gerekli",
        )

# ═══════════════════════════════════════ TAB 2 – FAALİYETLER ════════════════
with tab2:

    left_col, right_col = st.columns([1, 3])

    with left_col:
        st.markdown("**Kategori**")
        grup_no: int = st.radio(
            "Kategori",
            options=list(GRUPLAR.keys()),
            format_func=lambda x: f"{x:>2}. {GRUPLAR[x]}",
            key="v_grup",
            label_visibility="collapsed",
        )

    with right_col:
        st.subheader(f"Faaliyet Ekle — {GRUPLAR[grup_no]}")

        ilgili = sorted(
            [(k, v) for k, v in t.EK2_PUANLAR.items() if v["grup"] == grup_no],
            key=lambda x: [int(s) if s.isdigit() else s
                           for s in x[0].replace(".", " ").split()],
        )

        if not ilgili:
            st.info("Bu kategoride kayıtlı faaliyet bulunamadı.")
        else:
            faaliyet_options = {
                f"{k}  –  {v['ad']}  [{v['taban']} puan]": k
                for k, v in ilgili
            }
            secili_label: str = st.selectbox(
                "Faaliyet", options=list(faaliyet_options.keys()), key="v_fkod",
            )
            secili_kod = faaliyet_options[secili_label]
            bilgi      = t.EK2_PUANLAR[secili_kod]

            # ── Adet / Yıl ──────────────────────────────────────────────────
            adet_label = "Yıl" if grup_no == 18 else "Adet"
            adet: int = st.number_input(
                adet_label, min_value=1, max_value=999, value=1, key="v_adet",
            )

            # ── Yazar bilgileri (grup 1, 2, 3) ──────────────────────────────
            toplam_yazar, yazar_sirasi, sorumlu = 1, 1, False
            if grup_no in {1, 2, 3}:
                yc1, yc2, yc3 = st.columns(3)
                with yc1:
                    toplam_yazar = st.number_input(
                        "Toplam Yazar", min_value=1, max_value=50, value=1, key="v_tyazar",
                    )
                with yc2:
                    yazar_sirasi = st.number_input(
                        "Yazar Sırası", min_value=1, max_value=50, value=1, key="v_syazar",
                    )
                with yc3:
                    sorumlu = st.checkbox("Sorumlu / Senyör Yazar", key="v_sorumlu")

            # ── Q değeri ────────────────────────────────────────────────────
            q_val: str | None = None
            if bilgi.get("q_carpan"):
                q_val = st.radio(
                    "Dergi Kuartilin (Q)",
                    options=["Q1", "Q2", "Q3", "Q4"],
                    horizontal=True,
                    key="v_q",
                    help="Q1→×2  |  Q2→×1.5  |  Q3→×1.25  |  Q4→×1",
                )

            # ── Patent durumu ────────────────────────────────────────────────
            patent_durum: str | None = None
            if secili_kod in ("11.1", "11.7"):
                patent_label = st.radio(
                    "Patent Durumu",
                    options=list(PATENT_MAP.keys()),
                    horizontal=True,
                    key="v_patent",
                )
                patent_durum = PATENT_MAP[patent_label]

            # ── Ek seçenekler ───────────────────────────────────────────────
            ex1, ex2 = st.columns(2)
            ikinci_dan = False
            with ex1:
                if secili_kod in ("17.1", "17.2"):
                    ikinci_dan = st.checkbox(
                        "İkinci Danışman (yarı puan)", key="v_ikinci",
                    )
            with ex2:
                docsn: bool = st.checkbox("Doçentlik Sonrası Faaliyet", key="v_docsn")

            # ── Tahmini puan ─────────────────────────────────────────────────
            f_tmp = t.Faaliyet(
                kod=secili_kod,
                adet=adet,
                toplam_yazar=toplam_yazar,
                yazar_sirasi=yazar_sirasi,
                sorumlu_veya_senyör=sorumlu,
                q_degeri=q_val,
                patent_durum=patent_durum,
                ikinci_danisман=ikinci_dan,
                docent_sonrasi=docsn,
            )
            p_tmp, _ = t.faaliyet_puan_hesapla(f_tmp)
            p1_mi    = t.is_puan1(secili_kod, st.session_state.get("v_kadro", "dr_ilk"))
            tur_str  = "PUAN-1" if p1_mi else "PUAN-2"

            info_col, btn_col = st.columns([3, 1])
            with info_col:
                st.info(f"Tahmini puan: **{p_tmp:.2f}**  ·  Puan Türü: **{tur_str}**")
            with btn_col:
                if st.button("➕  Ekle", type="primary", use_container_width=True):
                    st.session_state.faaliyetler.append(t.Faaliyet(
                        kod=secili_kod,
                        adet=adet,
                        toplam_yazar=toplam_yazar,
                        yazar_sirasi=yazar_sirasi,
                        sorumlu_veya_senyör=sorumlu,
                        q_degeri=q_val,
                        patent_durum=patent_durum,
                        ikinci_danisман=ikinci_dan,
                        docent_sonrasi=docsn,
                    ))
                    st.rerun()

    # ── Eklenen Faaliyetler Tablosu ──────────────────────────────────────────
    st.divider()
    flist     = st.session_state.faaliyetler
    ham_top   = sum(t.faaliyet_puan_hesapla(f)[0] for f in flist)
    kadro_su  = st.session_state.get("v_kadro", "dr_ilk")

    tbl_h1, tbl_h2 = st.columns([4, 1])
    with tbl_h1:
        st.subheader(f"Eklenen Faaliyetler  ({len(flist)} adet)")
    with tbl_h2:
        st.metric("Ham Toplam", f"{ham_top:.2f} puan")

    if flist:
        rows = _faaliyet_satirlari(kadro_su)
        df   = pd.DataFrame(rows).set_index("#")
        st.dataframe(
            df.style.map(_tur_renk, subset=["Tür"]),
            use_container_width=True,
            height=min(420, 50 + 36 * len(rows)),
        )

        del1, del2 = st.columns([2, 2])
        with del1:
            sil_no = st.number_input(
                "Silinecek # numarası",
                min_value=1, max_value=len(flist), step=1, key="v_sil_idx",
            )
            if st.button("🗑  Seçiliyi Sil"):
                st.session_state.faaliyetler.pop(int(sil_no) - 1)
                st.rerun()
        with del2:
            st.write("")
            st.write("")
            if st.button("🗑🗑  Tümünü Temizle"):
                st.session_state.faaliyetler = []
                st.rerun()
    else:
        st.info("Henüz faaliyet eklenmedi. Sol taraftan kategori seçip faaliyet ekleyin.")

# ─────────────────────────────────────────────────────────────────────────────
# HESAPLA + PDF — Sekmeler dışında, her zaman görünür
# ─────────────────────────────────────────────────────────────────────────────
st.divider()
foot1, foot2, foot3 = st.columns([3, 1, 1])

with foot1:
    n_f = len(st.session_state.faaliyetler)
    if n_f:
        st.caption(f"📋  {n_f} faaliyet girildi.")
    else:
        st.caption("📋  Henüz faaliyet eklenmedi. '2 · Faaliyetler' sekmesinden ekleyin.")

with foot2:
    if st.button("▶  HESAPLA", type="primary", use_container_width=True):
        if not st.session_state.faaliyetler:
            st.error("Önce en az bir faaliyet ekleyin.")
        else:
            aday = _aday_olustur()
            st.session_state.son_aday = aday
            st.session_state.sonuc    = t.kriter_kontrol(aday)
            st.rerun()

with foot3:
    if st.session_state.sonuc and st.session_state.son_aday:
        if PDF_OK:
            pdf_data = _pdf_bytes(st.session_state.son_aday, st.session_state.sonuc)
            isim     = st.session_state.son_aday.ad_soyad.replace(" ", "_")
            st.download_button(
                label="⬇  PDF İndir",
                data=pdf_data,
                file_name=f"TNKU_{isim}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        else:
            st.caption("PDF için: `pip install reportlab`")

# ═══════════════════════════════════════ SONUÇLAR ════════════════════════════
sonuc    = st.session_state.sonuc
son_aday = st.session_state.son_aday

if sonuc is not None and son_aday is not None:
    st.divider()
    pnlar = sonuc["puanlar"]
    genel = sonuc["genel_sonuc"]

    kadro_adi_tam = {
        "dr_ilk":     "Dr. Öğretim Üyesi – İlk Atanma",
        "dr_yeniden": f"Dr. Öğretim Üyesi – Yeniden Atanma ({son_aday.yeniden_sure} Yıl)",
        "docent":     "Doçent",
        "profesor":   "Profesör",
    }.get(son_aday.kadro_turu, "–")

    # ── Genel sonuç bandı ────────────────────────────────────────────────────
    gtxt = ("✓  TÜM KRİTERLER SAĞLANIYOR – BAŞVURU YAPILABİLİR"
            if genel else
            "✗  BAZI KRİTERLER SAĞLANMIYOR – BAŞVURU YAPILAMAZ")
    st.markdown(
        f'<div class="{"sonuc-ok" if genel else "sonuc-fail"}">{gtxt}</div>',
        unsafe_allow_html=True,
    )

    # ── Aday özeti ───────────────────────────────────────────────────────────
    sc1, sc2, sc3, sc4 = st.columns(4)
    sc1.metric("Aday",  son_aday.ad_soyad)
    sc2.metric("Alan",  son_aday.alan)
    sc3.metric("Kadro", kadro_adi_tam)
    sc4.metric("Tarih", datetime.date.today().strftime("%d.%m.%Y"))

    st.divider()

    # ── Puan özeti ───────────────────────────────────────────────────────────
    pc1, pc2, pc3 = st.columns(3)
    pc1.metric("PUAN-1  (EK-2: 1.1–1.6 kapsamı)", f"{pnlar['puan1']:.2f}")
    pc2.metric("PUAN-2  (EK-2 tamamı – kalan)",   f"{pnlar['puan2']:.2f}")
    pc3.metric("TOPLAM PUAN",                      f"{pnlar['toplam']:.2f}")

    st.divider()

    # ── Kriter kontrol ───────────────────────────────────────────────────────
    st.subheader("Kriter Kontrol Sonuçları")
    for kr in sonuc["kriterler"]:
        ok        = "✓" in kr["durum"]
        info_only = "(f) Bilgi:" in kr["kriter"]
        if info_only:
            css, icon = "kriter-info", "ℹ️"
        elif ok:
            css, icon = "kriter-ok",  "✓"
        else:
            css, icon = "kriter-fail", "✗"
        not_str = (f"  <small style='color:#555'>({kr['notlar']})</small>"
                   if kr["notlar"] else "")
        st.markdown(
            f'<div class="{css}"><b>{icon}</b>&nbsp;&nbsp;{kr["kriter"]}{not_str}</div>',
            unsafe_allow_html=True,
        )

    st.divider()

    # ── Faaliyet detayı ──────────────────────────────────────────────────────
    st.subheader("Faaliyet Detayı")
    drows = [
        {
            "Kod":      d["kod"],
            "Faaliyet": d["ad"][:65],
            "Adet":     d["adet"],
            "Puan":     round(d["puan"], 2),
            "Tür":      "PUAN-1" if d["puan1_mi"] else "PUAN-2",
        }
        for d in pnlar["detaylar"]
    ]
    if drows:
        ddf = pd.DataFrame(drows)
        st.dataframe(
            ddf.style.map(_tur_renk, subset=["Tür"]),
            use_container_width=True,
            height=min(420, 50 + 36 * len(drows)),
        )
