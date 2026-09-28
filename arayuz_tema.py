"""
Arayüzün görsel katmanı: başlık bandı, adım çubuğu, "nasıl kullanılır" rehberi,
bölüm başlıkları ve ek stil. Hesaplamayla ilgili hiçbir şey içermez.
"""

from __future__ import annotations

import html

import streamlit as st

CSS = """
<style>
:root {
  --lacivert: #16325C; --mavi: #1F4E8C; --acik-mavi: #E8F0FB; --kenar: #DCE3EE;
  --yazi: #1E293B; --soluk: #64748B; --yesil: #1A7A3A; --zemin: #F4F6FA;
}
.stApp { background: var(--zemin); }
.stMainBlockContainer { max-width: 1180px; }

/* ── Başlık bandı ── */
.hero {
  background: radial-gradient(circle at 85% 20%, rgba(255,255,255,.12), transparent 40%),
              linear-gradient(135deg, #10284D 0%, #1F4E8C 60%, #2B6CB0 100%);
  color: #fff; border-radius: 18px; padding: 22px 26px 18px; margin-bottom: 14px;
  box-shadow: 0 10px 30px rgba(16,40,77,.22);
}
.hero-ust { display: flex; align-items: center; gap: 14px; }
.hero-logo { font-size: 2.1em; line-height: 1; background: rgba(255,255,255,.14);
  border-radius: 14px; padding: 8px 10px; }
.hero h1 { color: #fff !important; font-size: clamp(1.05em, 2.6vw, 1.45em) !important;
  margin: 0 !important; padding: 0 !important; font-weight: 700; letter-spacing: -.02em; }
.hero p { color: #C7DBF5; margin: 2px 0 0; font-size: .86em; }

/* ── Adım çubuğu ── */
.adimlar { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 10px; margin-top: 16px; }
.adim { background: rgba(255,255,255,.10); border: 1px solid rgba(255,255,255,.16);
  border-radius: 12px; padding: 10px 12px; display: flex; gap: 10px; align-items: center; }
.adim .no { flex: 0 0 28px; height: 28px; border-radius: 50%; display: grid; place-items: center;
  font-weight: 700; font-size: .85em; background: rgba(255,255,255,.18); color: #fff; }
.adim.tamam .no { background: #34D399; color: #064E3B; }
.adim.sirada { border-color: #FCD34D; box-shadow: 0 0 0 1px #FCD34D inset; }
.adim.sirada .no { background: #FCD34D; color: #78350F; }
.adim .ad { font-weight: 600; font-size: .92em; color: #fff; line-height: 1.2; }
.adim .durum { font-size: .8em; color: #C7DBF5; }

/* ── Bölüm başlıkları ── */
.card-title { display: flex; align-items: center; gap: 10px; font-size: 1.05em !important;
  font-family: 'Inter', 'Segoe UI', system-ui, sans-serif !important;
  font-weight: 700 !important; text-transform: none !important; letter-spacing: -.01em !important;
  color: var(--lacivert) !important; border-bottom: none !important; margin: 6px 0 2px !important;
  padding-bottom: 0 !important; }
.card-title .ikon { width: 32px; height: 32px; border-radius: 10px; display: grid;
  place-items: center; background: var(--acik-mavi); font-size: 1.05em; }
.card-desc { color: var(--soluk); font-size: .88em; margin: 0 0 12px 42px; line-height: 1.45; }

/* ── Sekmeler: hap görünümü ── */
.stTabs [data-baseweb="tab-list"] { gap: 6px; background: #fff; padding: 6px;
  border-radius: 14px; border: 1px solid var(--kenar); box-shadow: 0 1px 3px rgba(0,0,0,.04); }
.stTabs [data-baseweb="tab"] { border-radius: 10px; padding: 8px 18px; height: auto;
  font-weight: 600; color: var(--soluk); }
.stTabs [data-baseweb="tab"][aria-selected="true"] { background: var(--mavi); color: #fff; }
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display: none; }

/* ── Kartlar (kenarlıklı kapsayıcılar) ── */
[data-testid="stVerticalBlockBorderWrapper"] { border-radius: 16px !important; background: #fff;
  box-shadow: 0 1px 3px rgba(15,23,42,.05); }

/* ── Genişletici (expander) ── */
[data-testid="stExpander"] details { border-radius: 12px !important; border-color: var(--kenar) !important;
  background: #fff; }
[data-testid="stExpander"] summary { font-weight: 600; }
[data-testid="stExpander"] summary:hover { color: var(--mavi); }

/* ── Butonlar ── */
.stButton > button, .stDownloadButton > button { border-radius: 10px !important;
  transition: transform .12s ease, box-shadow .12s ease, background .12s ease !important; }
.stButton > button[kind="secondary"] { background: #fff; border: 1px solid var(--kenar) !important; }
.stButton > button[kind="secondary"]:hover { border-color: var(--mavi) !important; color: var(--mavi) !important;
  background: var(--acik-mavi) !important; transform: translateY(-1px); }

/* ── İpuçları (help / tooltip) ── */
[data-baseweb="tooltip"] > div, [data-testid="stTooltipContent"] {
  background: #10284D !important; color: #F1F5F9 !important; border-radius: 10px !important;
  font-size: .84em !important; line-height: 1.45 !important; max-width: 320px !important;
  box-shadow: 0 8px 24px rgba(16,40,77,.28) !important; }
[data-testid="stTooltipContent"] * { color: #F1F5F9 !important; }

/* ── Uyarı kutuları ve metrikler ── */
[data-testid="stAlert"] { border-radius: 12px; }
[data-testid="stMetricValue"] { font-size: 1.35rem !important; font-weight: 700; color: var(--lacivert); }
[data-testid="stMetricValue"] > div { white-space: normal !important; overflow: visible !important; }
.eksik-ozet { background: #FFF7ED; border: 1px solid #FDBA74; border-radius: 14px; padding: 14px 18px;
  margin: 4px 0 14px; color: #7C2D12; }
.eksik-ozet b.bas { display: block; margin-bottom: 6px; color: #9A3412; }
.eksik-ozet li { margin: 3px 0; font-size: .9em; }
.eksik-ozet .not { color: #9A3412; opacity: .85; font-size: .9em; }
[data-testid="stMetric"] { background: #fff; border: 1px solid var(--kenar); border-radius: 14px;
  padding: 12px 16px; }
.bos-durum { text-align: center; padding: 26px 18px; border: 2px dashed var(--kenar);
  border-radius: 16px; background: #fff; color: var(--soluk); }
.bos-durum .buyuk { font-size: 2em; }
.bos-durum b { color: var(--lacivert); }
.sonraki { background: var(--acik-mavi); border-radius: 12px; padding: 12px 16px; color: var(--lacivert);
  font-size: .9em; margin-top: 8px; }

@media (max-width: 768px) {
  .hero { padding: 16px; border-radius: 14px; }
  .card-desc { margin-left: 0; }
  .stTabs [data-baseweb="tab"] { padding: 8px 10px; }
}
</style>
"""

# Bölüm başlığı → (ikon, kısa açıklama); GORUNEN: ekranda görünen yazılış
GORUNEN = {'KİMLİK BİLGİLERİ': 'Kimlik bilgileri',
    'AKADEMİK ALAN': 'Akademik alan',
    'KADRO TÜRÜ': 'Kadro türü',
    'GENEL KOŞULLAR': 'Genel koşullar',
    'SAYISAL BİLGİLER': 'Sayısal bilgiler',
    'AVES VERİSİNDEN OTOMATİK YÜKLE': "AVES'ten otomatik yükle", 'KATEGORİ': 'Kategori',
    'EKLENMİŞ FAALİYETLER': 'Eklenmiş faaliyetler',
    'PUAN ÖZETİ': 'Puan özeti',
    'KRİTER KONTROL SONUÇLARI': 'Kriter kontrol sonuçları',
    'FAALİYET DETAYI': 'Faaliyet detayı',
    'KANIT KLASÖRÜ (YEREL)': 'Kanıt klasörü (yerel)',
    'KANIT DENETİMİ': 'Kanıt denetimi',
    'BAŞVURU DOSYASI (USB KLASÖRÜ + BİRLEŞİK PDF)': 'Başvuru dosyası (USB klasörü + birleşik PDF)'}

BOLUMLER = {
    "KİMLİK BİLGİLERİ": ("👤", "Adınızı ve AVES özgeçmiş adresinizi yazın."),
    "AKADEMİK ALAN": ("🧭", "Temel alanınız; bazı koşullar alana göre değişir."),
    "KADRO TÜRÜ": ("🏛️", "Başvuracağınız kadroyu seçin; eşikler buna göre belirlenir."),
    "GENEL KOŞULLAR": ("✅", "Sahip olduğunuz unvan ve belgeleri işaretleyin."),
    "SAYISAL BİLGİLER": ("🔢", "Yabancı dil puanınız, ders verdiğiniz dönemler ve süreler."),
    "AVES VERİSİNDEN OTOMATİK YÜKLE": ("⚡", "Yayın, bildiri, proje, hakemlik ve idari görevlerinizi "
                                              "AVES özgeçmişinizden tek tıkla faaliyet listesine aktarın."),
    "KATEGORİ": ("🗂️", "Eklenecek faaliyetin bölümü."),
    "EKLENMİŞ FAALİYETLER": ("📋", "Listeye eklediğiniz faaliyetler. Satırı açarak düzenleyebilir ya da "
                                    "silebilirsiniz."),
    "PUAN ÖZETİ": ("📊", "Yönergeye göre hesaplanan puanlarınız."),
    "KRİTER KONTROL SONUÇLARI": ("🧾", "Başvuru koşullarının her biri: ✓ sağlanıyor, ✗ sağlanmıyor."),
    "FAALİYET DETAYI": ("🔍", "Her faaliyetin taban puanı, yazar payı ve hak ettiği puan."),
    "KANIT KLASÖRÜ (YEREL)": ("📁", "Kanıt belgelerinizin bulunduğu klasör. Faaliyet listeniz de burada "
                                    "saklanır (yalnızca kendi bilgisayarınızda)."),
    "KANIT DENETİMİ": ("🛡️", "Puan alan faaliyetlerde eksik belge var mı? (Md. 7)"),
    "BAŞVURU DOSYASI (USB KLASÖRÜ + BİRLEŞİK PDF)": ("📦", "Faaliyetleri kanıtlarıyla EK-2 sırasına dizip "
                                                           "USB klasörü ve yazdırılacak tek PDF oluşturur."),
}


def kart_basligi(baslik: str, aciklama: str | None = None, ikon: str | None = None) -> None:
    """İkonlu bölüm başlığı ve altında kısa açıklama."""
    anahtar = baslik.split("&nbsp;")[0].split(" —")[0].strip()
    v_ikon, v_acik = BOLUMLER.get(anahtar, ("•", ""))
    ikon, aciklama = ikon or v_ikon, v_acik if aciklama is None else aciklama
    gorunen = GORUNEN.get(anahtar, baslik.replace("&nbsp;", " "))
    st.markdown(f'<div class="card-title"><span class="ikon">{ikon}</span>{gorunen}</div>'
                + (f'<div class="card-desc">{aciklama}</div>' if aciklama else ""),
                unsafe_allow_html=True)


def stil_uygula() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def baslik_bandi(adimlar: list[tuple[str, str, str]]) -> None:
    """adimlar: (ad, durum metni, 'tamam' | 'sirada' | '')"""
    kutular = "".join(
        f'<div class="adim {sinif}"><div class="no">{"✓" if sinif == "tamam" else i}</div>'
        f'<div><div class="ad">{html.escape(ad)}</div><div class="durum">{html.escape(durum)}</div>'
        f"</div></div>"
        for i, (ad, durum, sinif) in enumerate(adimlar, 1))
    st.markdown(f"""
<div class="hero">
  <div class="hero-ust"><div class="hero-logo">🎓</div><div>
    <h1>Öğretim Üyeliği Atama Puanlama Sistemi</h1>
    <p>Tekirdağ Namık Kemal Üniversitesi · EYS-YNG-129 (Rev. 2, 10.08.2026)</p>
  </div></div>
  <div class="adimlar">{kutular}</div>
</div>""", unsafe_allow_html=True)


def nasil_kullanilir(yerel: bool) -> None:
    with st.expander("❓ Programı ilk kez mi kullanıyorsunuz? Nasıl kullanılır…", expanded=False):
        st.markdown(
            "**Program ne yapar?** Yayın ve faaliyetlerinizi TNKÜ atama yönergesine (EYS-YNG-129) göre "
            "puanlar; seçtiğiniz kadronun bütün koşullarını tek tek denetler ve sonucu PDF rapor olarak "
            "verir.\n\n"
            "1. **Aday Bilgileri** sekmesinde adınızı, alanınızı ve başvuracağınız kadroyu seçin; "
            "yabancı dil puanınızı ve tarihleri girin.\n"
            "2. Aynı sekmenin altındaki **AVES'ten yükle** bölümüne AVES adresinizi yazıp "
            "**⚡ Yükle ve Ekle**'ye basın. Yayınlarınız, bildirileriniz, projeleriniz, hakemlikleriniz ve "
            "idari görevleriniz otomatik eklenir.\n"
            "3. **Faaliyetler** sekmesinde listeyi kontrol edin; AVES'te olmayanları sol taraftan "
            "kategori seçip **➕ Ekle** ile ekleyin. Bir satırı açıp düzeltebilirsiniz "
            "(ör. Q değeri, yazar sırası).\n"
            "4. **▶ HESAPLA**'ya basın. Puanlarınız ve koşulların her biri ✓ / ✗ olarak görünür; "
            "**⬇ PDF İndir** ile raporu alın.\n"
            + ("5. Kanıt klasörü tanımlıysa sonuç ekranındaki **📦 Başvuru dosyası** bölümü, "
               "faaliyetleri belgeleriyle birlikte USB klasörü ve tek PDF olarak hazırlar.\n" if yerel else "")
            + "\n💡 **İpucu:** Herhangi bir düğmenin ya da alanın üzerine fareyle gelin (ya da ⓘ/? "
              "işaretine dokunun): ne işe yaradığı açıklanır.")


def bos_durum(baslik: str, metin: str, ikon: str = "🗒️") -> None:
    st.markdown(f'<div class="bos-durum"><div class="buyuk">{ikon}</div><b>{baslik}</b>'
                f"<div>{metin}</div></div>", unsafe_allow_html=True)


def sonraki_adim(metin: str) -> None:
    st.markdown(f'<div class="sonraki">👉 {metin}</div>', unsafe_allow_html=True)


def eksik_ozeti(kriterler: list[dict]) -> None:
    """Sonuç bandının altında: sağlanmayan koşulların kısa listesi."""
    satirlar = "".join(
        f"<li>{html.escape(k['kriter'])}"
        + (f" <span class='not'>— {html.escape(k['notlar'])}</span>" if k.get("notlar") else "")
        + "</li>" for k in kriterler)
    st.markdown(f"<div class='eksik-ozet'><b class='bas'>Başvuru için tamamlanması gereken "
                f"{len(kriterler)} koşul:</b><ul style='margin:0;padding-left:20px'>{satirlar}</ul>"
                "</div>", unsafe_allow_html=True)
