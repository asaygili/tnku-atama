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
# Google Analytics
# ─────────────────────────────────────────────────────────────────────────────
components.html("""
<script async src="https://www.googletagmanager.com/gtag/js?id=G-QJFQV27KN5"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-QJFQV27KN5');
</script>
""", height=0)

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
        rows.append({
            "#":        i + 1,
            "Kod":      f.kod,
            "Faaliyet": bilgi_f.get("ad", "")[:55],
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
        r"C:\Windows\fonts",
        # Linux – DejaVu (packages.txt: fonts-dejavu-core)
        "/usr/share/fonts/truetype/dejavu",
        "/usr/share/fonts/dejavu",
        "/usr/share/fonts/truetype/ttf-dejavu",
        # Linux – Liberation
        "/usr/share/fonts/truetype/liberation",
        "/usr/share/fonts/liberation",
        # Linux – Ubuntu genel
        "/usr/share/fonts/truetype",
        "/usr/share/fonts",
        # macOS
        "/System/Library/Fonts",
        "/Library/Fonts",
        # Kullanıcı
        os.path.expanduser("~/.fonts"),
        os.path.expanduser("~/Library/Fonts"),
        # Uygulamanın yanındaki fonts/ klasörü
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts"),
    ]
    for k in klasorler:
        yol = os.path.join(k, dosya)
        if os.path.exists(yol):
            return yol
    return None


def _kaydet_font(isim: str, dosya: str) -> bool:
    """Fontu kaydet; zaten kayıtlıysa sessizce geç."""
    try:
        pdfmetrics.getFont(isim)
        return True          # zaten kayıtlı
    except Exception:
        pass
    yol = _bul_font(dosya)
    if not yol:
        return False
    try:
        pdfmetrics.registerFont(TTFont(isim, yol))
        return True
    except Exception:
        return False


def _pdf_bytes(aday: t.AdayBilgi, sonuc: dict) -> bytes:
    buf = io.BytesIO()

    # Normal + Bold çiftlerini dene; ilk başarılı çifti kullan
    fr, fb = "Helvetica", "Helvetica-Bold"
    for (fn, fin), (bn, bin_) in [
        (("TRR_dv",  "DejaVuSans.ttf"),       ("TRB_dv",  "DejaVuSans-Bold.ttf")),
        (("TRR_lib", "LiberationSans-Regular.ttf"), ("TRB_lib", "LiberationSans-Bold.ttf")),
        (("TRR_ar",  "arial.ttf"),             ("TRB_ar",  "arialbd.ttf")),
        (("TRR_AR",  "Arial.ttf"),             ("TRB_AR",  "ArialBold.ttf")),
    ]:
        if _kaydet_font(fn, fin):
            fr = fn
            if _kaydet_font(bn, bin_):
                fb = bn
            break

    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=1.8 * cm, rightMargin=1.8 * cm,
        topMargin=2 * cm,    bottomMargin=1.8 * cm,
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
            ("BACKGROUND",     (0, 0), (-1, 0),  hdr_color),
            ("TEXTCOLOR",      (0, 0), (-1, 0),  colors.white),
            ("FONTNAME",       (0, 0), (-1, 0),  fb),
            ("FONTSIZE",       (0, 0), (-1, 0),  8),
            ("TOPPADDING",     (0, 0), (-1, 0),  6),
            ("BOTTOMPADDING",  (0, 0), (-1, 0),  6),
            ("FONTNAME",       (0, 1), (-1, -1), fr),
            ("FONTSIZE",       (0, 1), (-1, -1), 8),
            ("TOPPADDING",     (0, 1), (-1, -1), 3),
            ("BOTTOMPADDING",  (0, 1), (-1, -1), 3),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.white, colors.HexColor("#F4F7FF")]),
            ("GRID",           (0, 0), (-1, -1), 0.3, colors.HexColor("#CCCCCC")),
            ("VALIGN",         (0, 0), (-1, -1), "MIDDLE"),
        ])

    kadro_adi = {
        "dr_ilk":     "Dr. Ogretim Uyesi - Ilk Atanma",
        "dr_yeniden": f"Dr. Ogretim Uyesi - Yeniden Atanma ({aday.yeniden_sure} Yil)",
        "docent":     "Docent",
        "profesor":   "Profesor",
    }.get(aday.kadro_turu, "-")

    pnlar = sonuc["puanlar"]
    genel = sonuc["genel_sonuc"]
    W, _H = A4

    elems = []
    elems.append(Paragraph("TEKIRDAG NAMIK KEMAL UNIVERSITESI", s_title))
    elems.append(Paragraph("Ogretim Uyeligi - Atama Puanlama Raporu", s_sub))
    elems.append(Paragraph("EYS-YNG-129  |  28.03.2025", s_xs))
    elems.append(HRFlowable(width="100%", thickness=2,
                             color=colors.HexColor("#2E5DA3")))
    elems.append(Spacer(1, 8))

    ad_data = [
        ["Aday", "Alan", "Kadro", "Tarih"],
        [aday.ad_soyad, aday.alan, kadro_adi,
         datetime.date.today().strftime("%d.%m.%Y")],
    ]
    at = Table(ad_data, colWidths=[3.5*cm, 3.5*cm, 8*cm, 2.5*cm])
    at.setStyle(tbl_style())
    elems.append(at)
    elems.append(Spacer(1, 10))

    gtxt = ("TUM KRITERLER SAGLANIYOR - BASVURU YAPILABILIR"
            if genel else
            "BAZI KRITERLER SAGLANMIYOR - BASVURU YAPILAMAZ")
    gc = colors.HexColor("#1A7A3A") if genel else colors.HexColor("#C0392B")
    gt = Table([[gtxt]], colWidths=[W - 3.6*cm])
    gt.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), gc),
        ("TEXTCOLOR",     (0,0), (-1,-1), colors.white),
        ("FONTNAME",      (0,0), (-1,-1), fb),
        ("FONTSIZE",      (0,0), (-1,-1), 11),
        ("ALIGN",         (0,0), (-1,-1), "CENTER"),
        ("TOPPADDING",    (0,0), (-1,-1), 10),
        ("BOTTOMPADDING", (0,0), (-1,-1), 10),
    ]))
    elems.append(gt)
    elems.append(Spacer(1, 10))

    elems.append(Paragraph("PUAN OZETI", s_sec))
    pdata = [
        ["Puan Turu", "Deger"],
        ["PUAN-1  (EK-2 bolum 1-6 kapsami)", f"{pnlar['puan1']:.2f}"],
        ["PUAN-2  (EK-2 tamami - kalan)",     f"{pnlar['puan2']:.2f}"],
        ["TOPLAM PUAN",                       f"{pnlar['toplam']:.2f}"],
    ]
    pts = tbl_style()
    pts.add("FONTNAME",   (0, 3), (-1, 3), fb)
    pts.add("FONTSIZE",   (0, 3), (-1, 3), 10)
    pts.add("BACKGROUND", (0, 3), (-1, 3), colors.HexColor("#D6E4F7"))
    pt = Table(pdata, colWidths=[13*cm, 4.5*cm])
    pt.setStyle(pts)
    elems.append(pt)
    elems.append(Spacer(1, 10))

    elems.append(Paragraph("KRITER KONTROL SONUCLARI", s_sec))
    kdata = [["#", "Kriter", "Durum", "Not"]]
    for i, kr in enumerate(sonuc["kriterler"], 1):
        ok = "✓" in kr["durum"]
        kdata.append([
            str(i), kr["kriter"],
            "SAGLANIYOR" if ok else "SAGLANMIYOR",
            kr["notlar"],
        ])
    kts = tbl_style()
    for ri, kr in enumerate(sonuc["kriterler"], 1):
        ok   = "✓" in kr["durum"]
        info = "(f) Bilgi:" in kr["kriter"]
        bg = (colors.HexColor("#FFF8E1") if info else
              colors.HexColor("#E8F5E9") if ok else
              colors.HexColor("#FFEBEE"))
        tc = (colors.HexColor("#F57F17") if info else
              colors.HexColor("#1A7A3A") if ok else
              colors.HexColor("#C0392B"))
        kts.add("BACKGROUND", (0, ri), (-1, ri), bg)
        kts.add("TEXTCOLOR",  (2, ri), (2, ri),  tc)
        kts.add("FONTNAME",   (2, ri), (2, ri),  fb)
    kt = Table(kdata, colWidths=[0.7*cm, 9.5*cm, 3*cm, 4.3*cm])
    kt.setStyle(kts)
    elems.append(kt)
    elems.append(Spacer(1, 10))

    elems.append(Paragraph("FAALIYET DETAYI", s_sec))
    fdata = [["Kod", "Faaliyet", "Adet", "Puan", "Tur"]]
    for d in pnlar["detaylar"]:
        fdata.append([d["kod"], d["ad"][:70], str(d["adet"]),
                      f"{d['puan']:.2f}",
                      "PUAN-1" if d["puan1_mi"] else "PUAN-2"])
    fts = tbl_style()
    for ri, d in enumerate(pnlar["detaylar"], 1):
        fts.add("BACKGROUND", (0, ri), (-1, ri),
                colors.HexColor("#EAF4E8") if d["puan1_mi"]
                else colors.HexColor("#EAF0FA"))
    ft = Table(fdata, colWidths=[1.2*cm, 11*cm, 1*cm, 1.5*cm, 2*cm])
    ft.setStyle(fts)
    elems.append(ft)
    elems.append(Spacer(1, 14))

    elems.append(HRFlowable(width="100%", thickness=0.4,
                             color=colors.HexColor("#AAAAAA")))
    elems.append(Spacer(1, 4))
    elems.append(Paragraph(
        "Bu rapor TNKU EYS-YNG-129 yonergesi kapsaminda otomatik olarak "
        "olusturulmustur. Resmi basvurularda ilgili birime danisiniz.", s_xs))

    doc.build(elems)
    buf.seek(0)
    return buf.read()


# ─────────────────────────────────────────────────────────────────────────────
# Başlık
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="header-bar">
  <h2>🎓&nbsp; TNKÜ &nbsp;·&nbsp; Öğretim Üyeliği Atama Puanlama Sistemi</h2>
  <small>EYS-YNG-129 &nbsp;·&nbsp; 28.03.2025 &nbsp;·&nbsp;
  Tekirdağ Namık Kemal Üniversitesi</small>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Sekmeler
# ─────────────────────────────────────────────────────────────────────────────
tab1, tab2 = st.tabs([
    "📋  Aday Bilgileri",
    "➕  Faaliyetler",
])

# ═══════════════════════════════════════ TAB 1 – ADAY BİLGİLERİ ══════════════
with tab1:
    col_kimlik, col_kadro = st.columns([1, 1], gap="large")

    with col_kimlik:
        st.markdown('<div class="card-title">KİMLİK BİLGİLERİ</div>',
                    unsafe_allow_html=True)
        st.text_input("Ad Soyad", key="v_ad", placeholder="Adınız Soyadınız")
        st.selectbox("Akademik Alan", key="v_alan", options=[
            "ALAN-1  –  Fen / Sağlık / Müh. / Matematik vb.",
            "ALAN-2  –  Sosyal / İdari / Eğitim / Güzel Sanatlar vb.",
        ])
        st.checkbox("Güzel Sanatlar alanı  (PUAN-1 için %50 yeterli)",
                    key="v_guzel")

    with col_kadro:
        st.markdown('<div class="card-title">KADRO TÜRÜ</div>',
                    unsafe_allow_html=True)
        st.radio(
            "Başvuru yapılan kadro",
            key="v_kadro",
            options=["dr_ilk", "dr_yeniden", "docent", "profesor"],
            format_func=lambda x: KADRO_ADI[x],
        )
        if st.session_state.get("v_kadro") == "dr_yeniden":
            st.selectbox("Yeniden Atama Süresi", key="v_sure",
                         options=[3, 2, 1],
                         format_func=lambda x: f"{x} Yıl")

    st.divider()
    st.markdown('<div class="card-title">GENEL KOŞULLAR</div>',
                unsafe_allow_html=True)

    gc1, gc2, gc3 = st.columns(3, gap="medium")
    with gc1:
        st.checkbox("Doktora / Uzmanlık / Yeterlilik", key="v_doktora",
                    help="Tıp uzm., Diş Hek. uzm., Eczacılık uzm. veya Güzel Sanatlar yeterlilik")
        st.checkbox("ÜAK Doçent unvanı", key="v_uak",
                    help="Üniversitelerarası Kuruldan alınmış doçentlik unvanı")
    with gc2:
        st.checkbox("ÜAK sözlü sınavı başarılı", key="v_sifahi",
                    help="Doçent için zorunlu · Profesör'de işaretlenmezse puan eşikleri %20 artar")
        st.checkbox("Örnek ders 'Başarılı'", key="v_ornek",
                    help="Dr. Öğr. Üyesi için zorunlu; sözlü sınavsız Profesör için de zorunlu")
    with gc3:
        st.checkbox("Başlıca Araştırma Eseri eklendi", key="v_baslica",
                    help="Prof. başvurusu için zorunlu; doçent sonrası, başlıca yazar")
        st.checkbox("Çalışma alanı yabancı dil bölümü", key="v_ydbol",
                    help="Bu durumda YÖKDİL/YDS puanı ≥85 aranır")

    st.divider()
    st.markdown('<div class="card-title">SAYISAL BİLGİLER</div>',
                unsafe_allow_html=True)
    dl1, dl2, dl3 = st.columns(3, gap="medium")
    with dl1:
        st.number_input("YÖKDİL / YDS Puanı", key="v_ydpuan",
                        min_value=0.0, max_value=100.0, step=0.5,
                        help="Dr. Öğr. Üyesi ≥60  |  Doçent/Prof. ≥65  |  Yab. Dil Böl. ≥85")
    with dl2:
        st.number_input("Farklı yarıyıl ders sayısı", key="v_ders",
                        min_value=0, max_value=60, step=1,
                        help="Doçent ve Prof. için ≥4 farklı yarıyıl gerekli")
    with dl3:
        st.number_input("Doçent sonrası yükseköğretim süresi (yıl)", key="v_docsure",
                        min_value=0.0, max_value=40.0, step=0.5,
                        help="Prof. için ≥2.5 yıl gerekli")

# ═══════════════════════════════════════ TAB 2 – FAALİYETLER ════════════════
with tab2:
    left_col, right_col = st.columns([1, 3], gap="large")

    with left_col:
        st.markdown('<div class="card-title">KATEGORİ</div>',
                    unsafe_allow_html=True)
        grup_no: int = st.radio(
            "Kategori",
            options=list(GRUPLAR.keys()),
            format_func=lambda x: f"{x:>2}. {GRUPLAR[x]}",
            key="v_grup",
            label_visibility="collapsed",
        )

    with right_col:
        st.markdown(
            f'<div class="card-title">FAAALİYET EKLE &nbsp;—&nbsp; {GRUPLAR[grup_no]}</div>',
            unsafe_allow_html=True,
        )

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

            adet_label = "Yıl" if grup_no == 18 else "Adet"
            adet: int  = st.number_input(adet_label, min_value=1,
                                         max_value=999, value=1, key="v_adet")

            toplam_yazar, yazar_sirasi, sorumlu = 1, 1, False
            if grup_no in {1, 2, 3}:
                yc1, yc2, yc3 = st.columns(3)
                with yc1:
                    toplam_yazar = st.number_input("Toplam Yazar", min_value=1,
                                                   max_value=50, value=1, key="v_tyazar")
                with yc2:
                    yazar_sirasi = st.number_input("Yazar Sırası", min_value=1,
                                                   max_value=50, value=1, key="v_syazar")
                with yc3:
                    sorumlu = st.checkbox("Sorumlu / Senyör", key="v_sorumlu")

            q_val: str | None = None
            if bilgi.get("q_carpan"):
                q_val = st.radio("Dergi Kuartili (Q)",
                                 options=["Q1", "Q2", "Q3", "Q4"],
                                 horizontal=True, key="v_q",
                                 help="Q1→x2  |  Q2→x1.5  |  Q3→x1.25  |  Q4→x1")

            patent_durum: str | None = None
            if secili_kod in ("11.1", "11.7"):
                patent_durum = PATENT_MAP[st.radio(
                    "Patent Durumu", options=list(PATENT_MAP.keys()),
                    horizontal=True, key="v_patent")]

            ex1, ex2 = st.columns(2)
            ikinci_dan = False
            with ex1:
                if secili_kod in ("17.1", "17.2"):
                    ikinci_dan = st.checkbox("İkinci Danışman (yarı puan)",
                                             key="v_ikinci")
            with ex2:
                docsn: bool = st.checkbox("Doçentlik Sonrası Faaliyet",
                                          key="v_docsn")

            f_tmp = t.Faaliyet(
                kod=secili_kod, adet=adet,
                toplam_yazar=toplam_yazar, yazar_sirasi=yazar_sirasi,
                sorumlu_veya_senyör=sorumlu, q_degeri=q_val,
                patent_durum=patent_durum,
                ikinci_danisман=ikinci_dan, docent_sonrasi=docsn,
            )
            p_tmp, _ = t.faaliyet_puan_hesapla(f_tmp)
            p1_mi    = t.is_puan1(secili_kod,
                                  st.session_state.get("v_kadro", "dr_ilk"))
            tur_str  = "PUAN-1" if p1_mi else "PUAN-2"
            tur_renk = "#1A7A3A" if p1_mi else "#2E5DA3"

            ic1, ic2 = st.columns([3, 1])
            with ic1:
                st.markdown(
                    f"<div style='background:#F8FAFF;border:1px solid #DBEAFE;"
                    f"border-radius:8px;padding:10px 14px;font-size:0.9em;'>"
                    f"Tahmini puan: <b style='font-size:1.1em'>{p_tmp:.2f}</b>"
                    f"&nbsp;&nbsp;·&nbsp;&nbsp;"
                    f"<span style='color:{tur_renk};font-weight:600'>{tur_str}</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
            with ic2:
                if st.button("➕  Ekle", type="primary",
                             use_container_width=True):
                    st.session_state.faaliyetler.append(t.Faaliyet(
                        kod=secili_kod, adet=adet,
                        toplam_yazar=toplam_yazar, yazar_sirasi=yazar_sirasi,
                        sorumlu_veya_senyör=sorumlu, q_degeri=q_val,
                        patent_durum=patent_durum,
                        ikinci_danisман=ikinci_dan, docent_sonrasi=docsn,
                    ))
                    st.rerun()

    # ── Eklenen Faaliyetler ──────────────────────────────────────────────────
    st.divider()
    flist    = st.session_state.faaliyetler
    ham_top  = sum(t.faaliyet_puan_hesapla(f)[0] for f in flist)
    kadro_su = st.session_state.get("v_kadro", "dr_ilk")

    tbl_h1, tbl_h2 = st.columns([4, 1])
    with tbl_h1:
        st.markdown(
            f'<div class="card-title">EKLENMİŞ FAALİYETLER'
            f'&nbsp;<span style="background:#2E5DA3;color:white;padding:2px 10px;'
            f'border-radius:12px;font-size:0.9em">{len(flist)}</span></div>',
            unsafe_allow_html=True,
        )
    with tbl_h2:
        st.metric("Ham Toplam", f"{ham_top:.2f}")

    if flist:
        rows = _faaliyet_satirlari(kadro_su)
        df   = pd.DataFrame(rows).set_index("#")
        st.dataframe(
            df.style.map(_tur_renk, subset=["Tur"]),
            use_container_width=True,
            height=min(420, 50 + 36 * len(rows)),
        )
        del1, del2 = st.columns([2, 2])
        with del1:
            sil_no = st.number_input("Silinecek # numarası", min_value=1,
                                     max_value=len(flist), step=1,
                                     key="v_sil_idx")
            if st.button("🗑  Seçiliyi Sil"):
                st.session_state.faaliyetler.pop(int(sil_no) - 1)
                st.rerun()
        with del2:
            st.write("")
            st.write("")
            if st.button("🗑  Tümünü Temizle"):
                st.session_state.faaliyetler = []
                st.rerun()
    else:
        st.info("Henüz faaliyet eklenmedi. Sol taraftan kategori seçip faaliyet ekleyin.")

# ─────────────────────────────────────────────────────────────────────────────
# HESAPLA + PDF çubuğu
# ─────────────────────────────────────────────────────────────────────────────
st.divider()
n_f = len(st.session_state.faaliyetler)

bar1, bar2, bar3 = st.columns([3, 1, 1], gap="small")

with bar1:
    if n_f:
        st.markdown(
            f"<div style='padding:8px 0;color:#475569;font-size:0.9em'>"
            f"<span class='faaliyet-badge'>{n_f}</span> "
            f"faaliyet girildi. Sonuçları görmek için <b>HESAPLA</b>'ya basın."
            f"</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<div style='padding:8px 0;color:#94A3B8;font-size:0.9em'>"
            "Faaliyetler sekmesinden faaliyet ekleyin, ardından HESAPLA'ya basın."
            "</div>",
            unsafe_allow_html=True,
        )

with bar2:
    if st.button("▶  HESAPLA", type="primary", use_container_width=True):
        if not st.session_state.faaliyetler:
            st.error("Önce en az bir faaliyet ekleyin.")
        else:
            aday = _aday_olustur()
            st.session_state.son_aday = aday
            st.session_state.sonuc    = t.kriter_kontrol(aday)
            st.rerun()

with bar3:
    if st.session_state.sonuc and st.session_state.son_aday and PDF_OK:
        pdf_data = _pdf_bytes(st.session_state.son_aday,
                              st.session_state.sonuc)
        isim = st.session_state.son_aday.ad_soyad.replace(" ", "_")
        st.download_button(
            label="⬇  PDF İndir",
            data=pdf_data,
            file_name=f"TNKU_{isim}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
    elif not PDF_OK and st.session_state.sonuc:
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

    # ── Sonuç bandı ──────────────────────────────────────────────────────────
    ikon  = "✅" if genel else "❌"
    gtxt  = ("TÜM KRİTERLER SAĞLANIYOR – BAŞVURU YAPILABİLİR"
             if genel else
             "BAZI KRİTERLER SAĞLANMIYOR – BAŞVURU YAPILAMAZ")
    cls   = "sonuc-ok" if genel else "sonuc-fail"
    st.markdown(f'<div class="{cls}">{ikon}  {gtxt}</div>',
                unsafe_allow_html=True)

    # ── Aday özeti ───────────────────────────────────────────────────────────
    sc1, sc2, sc3, sc4 = st.columns(4, gap="small")
    sc1.metric("Aday",  son_aday.ad_soyad)
    sc2.metric("Alan",  son_aday.alan)
    sc3.metric("Kadro", kadro_adi_tam)
    sc4.metric("Tarih", datetime.date.today().strftime("%d.%m.%Y"))

    st.divider()

    # ── Puan kutuları ─────────────────────────────────────────────────────────
    st.markdown('<div class="card-title">PUAN ÖZETİ</div>',
                unsafe_allow_html=True)
    pc1, pc2, pc3 = st.columns(3, gap="medium")
    with pc1:
        st.markdown(
            f"<div class='puan-kutu'>"
            f"<div class='label'>PUAN-1 (EK-2: 1.1–1.6)</div>"
            f"<div class='value'>{pnlar['puan1']:.2f}</div>"
            f"</div>", unsafe_allow_html=True)
    with pc2:
        st.markdown(
            f"<div class='puan-kutu'>"
            f"<div class='label'>PUAN-2 (EK-2 tamamı)</div>"
            f"<div class='value'>{pnlar['puan2']:.2f}</div>"
            f"</div>", unsafe_allow_html=True)
    with pc3:
        st.markdown(
            f"<div class='puan-kutu toplam'>"
            f"<div class='label'>TOPLAM PUAN</div>"
            f"<div class='value'>{pnlar['toplam']:.2f}</div>"
            f"</div>", unsafe_allow_html=True)

    st.divider()

    # ── Kriter kontrol ───────────────────────────────────────────────────────
    st.markdown('<div class="card-title">KRİTER KONTROL SONUÇLARI</div>',
                unsafe_allow_html=True)
    for kr in sonuc["kriterler"]:
        ok        = "✓" in kr["durum"]
        info_only = "(f) Bilgi:" in kr["kriter"]
        if info_only:
            css, ikon2 = "kriter-info", "ℹ️"
        elif ok:
            css, ikon2 = "kriter-ok",  "✓"
        else:
            css, ikon2 = "kriter-fail", "✗"
        not_str = (f"&nbsp;&nbsp;<small style='color:#6B7280'>— {kr['notlar']}</small>"
                   if kr["notlar"] else "")
        st.markdown(
            f'<div class="{css}"><b>{ikon2}</b>&nbsp;&nbsp;'
            f'{kr["kriter"]}{not_str}</div>',
            unsafe_allow_html=True,
        )

    st.divider()

    # ── Faaliyet detayı ──────────────────────────────────────────────────────
    st.markdown('<div class="card-title">FAALİYET DETAYI</div>',
                unsafe_allow_html=True)
    drows = [
        {
            "Kod":      d["kod"],
            "Faaliyet": d["ad"][:60],
            "Adet":     d["adet"],
            "Puan":     round(d["puan"], 2),
            "Tur":      "PUAN-1" if d["puan1_mi"] else "PUAN-2",
        }
        for d in pnlar["detaylar"]
    ]
    if drows:
        ddf = pd.DataFrame(drows)
        st.dataframe(
            ddf.style.map(_tur_renk, subset=["Tur"]),
            use_container_width=True,
            height=min(420, 50 + 36 * len(drows)),
        )

    st.markdown(
        "<div style='text-align:center;color:#94A3B8;font-size:0.78em;"
        "padding:16px 0 4px'>EYS-YNG-129 · TNKÜ · Otomatik hesaplama aracıdır,"
        " resmi başvurularda ilgili birime danışınız.</div>",
        unsafe_allow_html=True,
    )
