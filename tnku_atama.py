"""
TNKÜ Öğretim Üyeliği Kadrosuna Başvuru Puanlama Programı
Tekirdağ Namık Kemal Üniversitesi - EYS-YNG-129 (28.03.2025)

Desteklenen kadro türleri:
  - Dr. Öğretim Üyesi (İlk Atanma ve Yeniden Atama)
  - Doçent
  - Profesör
"""

from __future__ import annotations
import sys
import io
from dataclasses import dataclass, field
from typing import Optional

# Windows terminalinde UTF-8 çıktı için
if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Yazar sırası çarpanları (Madde 8)
# Sorumlu Yazar / Senyör Yazar → 1. isimle aynı değer
# ---------------------------------------------------------------------------
YAZAR_CARPANI = {
    1: [1.00],
    2: [1.00, 0.90],
    3: [0.90, 0.80, 0.70],
    4: [0.85, 0.75, 0.65, 0.55],
    5: [0.80, 0.70, 0.60, 0.50, 0.40],
}
# 6 ve üzeri
YAZAR_CARPANI_6PLUS = [0.75, 0.65, 0.55, 0.45, 0.35, 0.25]


def yazar_carpani_hesapla(toplam_yazar: int, yazar_sirasi: int,
                          sorumlu_veya_senyör: bool = False) -> float:
    """Yazar sırasına göre puan çarpanını döndürür."""
    if sorumlu_veya_senyör:
        yazar_sirasi = 1  # 1. isimle aynı değerlendirme
    if toplam_yazar == 1:
        return 1.00
    if toplam_yazar <= 5:
        carpanlar = YAZAR_CARPANI[toplam_yazar]
        return carpanlar[min(yazar_sirasi, len(carpanlar)) - 1]
    # 6 ve üzeri
    idx = min(yazar_sirasi - 1, len(YAZAR_CARPANI_6PLUS) - 1)
    return YAZAR_CARPANI_6PLUS[idx]


# ---------------------------------------------------------------------------
# EK-2 Faaliyet Puanları
# ---------------------------------------------------------------------------
EK2_PUANLAR: dict[str, dict] = {

    # -------- 1. MAKALE --------
    "1.1":  {"ad": "SCI/SCI-E/SSCI/AHCI araştırma makalesi",
             "taban": 25, "q_carpan": True, "grup": 1},
    "1.2":  {"ad": "SCI/SCI-E/SSCI/AHCI teknik not/editöre mektup vb.",
             "taban": 10, "q_carpan": False, "grup": 1},
    "1.3":  {"ad": "SCI/SCI-E/SSCI/AHCI derleme makale",
             "taban": 15, "q_carpan": True, "grup": 1},
    "1.4":  {"ad": "ESCI/Scopus/ÜAK uluslararası endeksli araştırma makalesi",
             "taban": 15, "q_carpan": False, "grup": 1},
    "1.5":  {"ad": "Diğer uluslararası endeksli hakemli araştırma makalesi",
             "taban": 9,  "q_carpan": False, "grup": 1},
    "1.6":  {"ad": "TR Dizin ulusal hakemli araştırma makalesi",
             "taban": 13, "q_carpan": False, "grup": 1},
    "1.7":  {"ad": "Diğer uluslararası hakemli araştırma makalesi",
             "taban": 3,  "q_carpan": False, "grup": 1},
    "1.8":  {"ad": "TR Dizin dışı ulusal hakemli araştırma makalesi",
             "taban": 2,  "q_carpan": False, "grup": 1},
    "1.9":  {"ad": "ESCI/uluslararası/TR Dizin derleme-teknik not vb.",
             "taban": 3,  "q_carpan": False, "grup": 1},
    "1.10": {"ad": "Ulusal hakemli araştırma makalesi",
             "taban": 1,  "q_carpan": False, "grup": 1},
    "1.11": {"ad": "TR Dizin dışı derleme/teknik not vb.",
             "taban": 1,  "q_carpan": False, "grup": 1},

    # -------- 2. KİTAP --------
    "2.1":  {"ad": "BKCI kitap yazarlığı",
             "taban": 45, "q_carpan": False, "grup": 2},
    "2.2":  {"ad": "Tanınmış uluslararası yayınevi/yabancı üniversite özgün kitap",
             "taban": 40, "q_carpan": False, "grup": 2},
    "2.3":  {"ad": "Tanınmış ulusal yayınevi/üniversite özgün kitap",
             "taban": 15, "q_carpan": False, "grup": 2},
    "2.4":  {"ad": "BKCI kitap bölümü",
             "taban": 25, "q_carpan": False, "grup": 2},
    "2.5":  {"ad": "Tanınmış uluslararası yayınevi/yabancı üniversite kitap bölümü",
             "taban": 20, "q_carpan": False, "grup": 2},
    "2.6":  {"ad": "Tanınmış ulusal yayınevi/üniversite kitap bölümü",
             "taban": 10, "q_carpan": False, "grup": 2},
    "2.7":  {"ad": "Yabancı üniversite ders kitabı",
             "taban": 30, "q_carpan": False, "grup": 2},
    "2.8":  {"ad": "Ulusal üniversite ders kitabı",
             "taban": 20, "q_carpan": False, "grup": 2},
    "2.9":  {"ad": "Uluslararası kitap çevirisi",
             "taban": 20, "q_carpan": False, "grup": 2},
    "2.10": {"ad": "Uluslararası kitap bölümü çevirisi",
             "taban": 10, "q_carpan": False, "grup": 2},
    "2.11": {"ad": "Ulusal kitap çevirisi",
             "taban": 8,  "q_carpan": False, "grup": 2},
    "2.12": {"ad": "Ulusal kitap bölümü çevirisi",
             "taban": 5,  "q_carpan": False, "grup": 2},
    "2.13": {"ad": "Ulusal/uluslararası tahkik/neşir/transkripsiyon",
             "taban": 15, "q_carpan": False, "grup": 2},

    # -------- 3. BİLDİRİ --------
    "3.1":  {"ad": "CPCI uluslararası davetli konuşmacı (tam metin)",
             "taban": 15, "q_carpan": False, "grup": 3},
    "3.2":  {"ad": "Hakemli uluslararası konferans sözlü tam metin",
             "taban": 12, "q_carpan": False, "grup": 3},
    "3.3":  {"ad": "Hakemli uluslararası konferans sözlü özet",
             "taban": 6,  "q_carpan": False, "grup": 3},
    "3.4":  {"ad": "Hakemli uluslararası konferans poster",
             "taban": 5,  "q_carpan": False, "grup": 3},
    "3.5":  {"ad": "Hakemli ulusal konferans davetli konuşmacı",
             "taban": 8,  "q_carpan": False, "grup": 3},
    "3.6":  {"ad": "Hakemli ulusal konferans sözlü tam metin",
             "taban": 6,  "q_carpan": False, "grup": 3},
    "3.7":  {"ad": "Hakemli ulusal konferans sözlü özet",
             "taban": 3,  "q_carpan": False, "grup": 3},
    "3.8":  {"ad": "Hakemli ulusal konferans poster",
             "taban": 3,  "q_carpan": False, "grup": 3},
    "3.9":  {"ad": "Uluslararası ansiklopedi maddesi (her madde için)",
             "taban": 5,  "q_carpan": False, "grup": 3},
    "3.10": {"ad": "Ulusal ansiklopedi maddesi (her madde için)",
             "taban": 3,  "q_carpan": False, "grup": 3},
    "3.11": {"ad": "Güzel Sanatlar/Tasarım uluslararası bilimsel rapor/katalog vb.",
             "taban": 5,  "q_carpan": False, "grup": 3},
    "3.12": {"ad": "Güzel Sanatlar/Tasarım ulusal bilimsel rapor/katalog vb.",
             "taban": 3,  "q_carpan": False, "grup": 3},
    "3.13": {"ad": "Türk İslam Sanatları uluslararası bilimsel rapor vb.",
             "taban": 5,  "q_carpan": False, "grup": 3},
    "3.14": {"ad": "Türk İslam Sanatları ulusal bilimsel rapor vb.",
             "taban": 3,  "q_carpan": False, "grup": 3},

    # -------- 4. EDİTÖRLÜK (max 40 puan) --------
    "4.1":  {"ad": "SCI/SCI-E/SSCI/AHCI dergide editörlük (yıllık)",
             "taban": 15, "q_carpan": True, "grup": 4, "max_grup": 40},
    "4.2":  {"ad": "ESCI/Scopus dergide editörlük (yıllık)",
             "taban": 10, "q_carpan": False, "grup": 4, "max_grup": 40},
    "4.3":  {"ad": "Diğer uluslararası endeksli hakemli editörlük (yıllık)",
             "taban": 8,  "q_carpan": False, "grup": 4, "max_grup": 40},
    "4.4":  {"ad": "Diğer uluslararası hakemli editörlük (yıllık)",
             "taban": 5,  "q_carpan": False, "grup": 4, "max_grup": 40},
    "4.5":  {"ad": "Ulusal dergide editörlük (yıllık)",
             "taban": 2,  "q_carpan": False, "grup": 4, "max_grup": 40},
    "4.6":  {"ad": "TR Dizin ulusal hakemli editörlük (yıllık)",
             "taban": 5,  "q_carpan": False, "grup": 4, "max_grup": 40},
    "4.7":  {"ad": "Uluslararası dergide editörlük (yıllık)",
             "taban": 3,  "q_carpan": False, "grup": 4, "max_grup": 40},
    "4.8":  {"ad": "BKCI kitap editörlüğü",
             "taban": 25, "q_carpan": False, "grup": 4, "max_grup": 40},
    "4.9":  {"ad": "Tanınmış uluslararası yayınevi bilimsel kitap editörlüğü",
             "taban": 20, "q_carpan": False, "grup": 4, "max_grup": 40},
    "4.10": {"ad": "Tanınmış ulusal yayınevi bilimsel kitap editörlüğü",
             "taban": 10, "q_carpan": False, "grup": 4, "max_grup": 40},
    "4.11": {"ad": "SCI/SCI-E/SSCI/AHCI/ESCI/Scopus yayın kurulu üyeliği",
             "taban": 5,  "q_carpan": False, "grup": 4, "max_grup": 40},
    "4.12": {"ad": "Diğer uluslararası/ulusal yayın kurulu üyeliği",
             "taban": 3,  "q_carpan": False, "grup": 4, "max_grup": 40},

    # -------- 5. ATIF (max 50 puan) --------
    "5.1":  {"ad": "SCI/SCI-E/SSCI/AHCI atıf (adet)",
             "taban": 5,  "q_carpan": False, "grup": 5, "max_grup": 50},
    "5.2":  {"ad": "ESCI/Scopus/ÜAK atıf (adet)",
             "taban": 3,  "q_carpan": False, "grup": 5, "max_grup": 50},
    "5.3":  {"ad": "Diğer uluslararası endeksli atıf (adet)",
             "taban": 2,  "q_carpan": False, "grup": 5, "max_grup": 50},
    "5.4":  {"ad": "Diğer uluslararası hakemli atıf (adet)",
             "taban": 1,  "q_carpan": False, "grup": 5, "max_grup": 50},
    "5.5":  {"ad": "TR Dizin atıf (adet)",
             "taban": 2,  "q_carpan": False, "grup": 5, "max_grup": 50},
    "5.6":  {"ad": "Diğer ulusal hakemli atıf (adet)",
             "taban": 1,  "q_carpan": False, "grup": 5, "max_grup": 50},
    "5.7":  {"ad": "Uluslararası bilimsel kitapta atıf (adet)",
             "taban": 5,  "q_carpan": False, "grup": 5, "max_grup": 50},
    "5.8":  {"ad": "Ulusal bilimsel kitapta atıf (adet)",
             "taban": 3,  "q_carpan": False, "grup": 5, "max_grup": 50},
    "5.9":  {"ad": "H-endeks puanı (WoS) - her puan için",
             "taban": 5,  "q_carpan": False, "grup": 5, "max_grup": 50},
    "5.10": {"ad": "Uluslararası kitapta adla anılan formül/şema/tablo (adet)",
             "taban": 5,  "q_carpan": False, "grup": 5, "max_grup": 50},
    "5.11": {"ad": "Ulusal kitapta adla anılan formül/şema/tablo (adet)",
             "taban": 3,  "q_carpan": False, "grup": 5, "max_grup": 50},
    "5.12": {"ad": "Güzel Sanatlar patent/eser uluslararası yayın/gösterim",
             "taban": 5,  "q_carpan": False, "grup": 5, "max_grup": 50},
    "5.13": {"ad": "Güzel Sanatlar patent/eser ulusal yayın/gösterim",
             "taban": 3,  "q_carpan": False, "grup": 5, "max_grup": 50},

    # -------- 6. HAKEMLİK (max 20 puan) --------
    "6.1":  {"ad": "BKCI/uluslararası kitap hakemliği",
             "taban": 5, "q_carpan": False, "grup": 6, "max_grup": 20},
    "6.2":  {"ad": "Ulusal kitap hakemliği",
             "taban": 4, "q_carpan": False, "grup": 6, "max_grup": 20},
    "6.3":  {"ad": "SCI/SCI-E/SSCI/AHCI makale hakemliği",
             "taban": 5, "q_carpan": False, "grup": 6, "max_grup": 20},
    "6.4":  {"ad": "ESCI/Scopus makale hakemliği",
             "taban": 4, "q_carpan": False, "grup": 6, "max_grup": 20},
    "6.5":  {"ad": "Diğer uluslararası endeksli makale hakemliği",
             "taban": 3, "q_carpan": False, "grup": 6, "max_grup": 20},
    "6.6":  {"ad": "Diğer uluslararası hakemli makale hakemliği",
             "taban": 3, "q_carpan": False, "grup": 6, "max_grup": 20},
    "6.7":  {"ad": "Uluslararası konferans/sanat etkinliği hakemliği",
             "taban": 2, "q_carpan": False, "grup": 6, "max_grup": 20},
    "6.8":  {"ad": "TR Dizin ulusal hakemli makale hakemliği",
             "taban": 2, "q_carpan": False, "grup": 6, "max_grup": 20},
    "6.9":  {"ad": "Ulusal hakemli makale hakemliği",
             "taban": 2, "q_carpan": False, "grup": 6, "max_grup": 20},
    "6.10": {"ad": "Ulusal konferans hakemliği",
             "taban": 1, "q_carpan": False, "grup": 6, "max_grup": 20},
    "6.11": {"ad": "YÖK bilimsel araştırma projesi hakemliği",
             "taban": 3, "q_carpan": False, "grup": 6, "max_grup": 20},
    "6.12": {"ad": "TÜBİTAK projesi hakemliği",
             "taban": 5, "q_carpan": False, "grup": 6, "max_grup": 20},

    # -------- 7. PANELİST/JÜRİ (max 20 puan) --------
    "7.1":  {"ad": "Yurt dışı uluslararası panel yöneticisi/panelist",
             "taban": 15, "q_carpan": False, "grup": 7, "max_grup": 20},
    "7.2":  {"ad": "Yurt içi uluslararası panel yöneticisi/panelist",
             "taban": 5,  "q_carpan": False, "grup": 7, "max_grup": 20},
    "7.3":  {"ad": "Ulusal bilimsel toplantıda panel yöneticisi/panelist",
             "taban": 3,  "q_carpan": False, "grup": 7, "max_grup": 20},
    "7.4":  {"ad": "TÜBİTAK toplantı/proje panel yöneticisi/panelist",
             "taban": 10, "q_carpan": False, "grup": 7, "max_grup": 20},
    "7.5":  {"ad": "TÜBİTAK destekli projede dış panelist",
             "taban": 8,  "q_carpan": False, "grup": 7, "max_grup": 20},
    "7.6":  {"ad": "Yurt dışı uluslararası mimari/tasarım yarışması jürisi",
             "taban": 15, "q_carpan": False, "grup": 7, "max_grup": 20},
    "7.7":  {"ad": "Yurt dışı diğer uluslararası yarışma jürisi",
             "taban": 8,  "q_carpan": False, "grup": 7, "max_grup": 20},
    "7.8":  {"ad": "Yurt içi uluslararası mimari/tasarım yarışması jürisi",
             "taban": 10, "q_carpan": False, "grup": 7, "max_grup": 20},
    "7.9":  {"ad": "Yurt içi ulusal yarışma jürisi",
             "taban": 5,  "q_carpan": False, "grup": 7, "max_grup": 20},

    # -------- 8. TV-SİNEMA-TASARIM --------
    "8.1":  {"ad": "Uluslararası (yurt dışı) güzel sanatlar etkinliği plan/tasarım",
             "taban": 8,  "q_carpan": False, "grup": 8},
    "8.2":  {"ad": "Yurt içi uluslararası güzel sanatlar etkinliği plan/tasarım",
             "taban": 6,  "q_carpan": False, "grup": 8},
    "8.3":  {"ad": "Ulusal güzel sanatlar etkinliği plan/tasarım",
             "taban": 5,  "q_carpan": False, "grup": 8},
    "8.4":  {"ad": "Yurt dışı kamu tarafından uygulanan mimari plan/tasarım",
             "taban": 20, "q_carpan": False, "grup": 8},
    "8.5":  {"ad": "Yurt içi kamu tarafından uygulanan mimari plan/tasarım",
             "taban": 10, "q_carpan": False, "grup": 8},
    "8.6":  {"ad": "Yurt dışı özel sektör mimari plan/tasarım",
             "taban": 8,  "q_carpan": False, "grup": 8},
    "8.7":  {"ad": "Yurt içi özel sektör mimari plan/tasarım",
             "taban": 5,  "q_carpan": False, "grup": 8},
    "8.8":  {"ad": "Grafik/web/görsel kimlik tasarımı yurt dışı kamu/özel uygulama",
             "taban": 7,  "q_carpan": False, "grup": 8},
    "8.9":  {"ad": "Uzun metrajlı film yönetmenliği",
             "taban": 20, "q_carpan": False, "grup": 8},
    "8.10": {"ad": "Uzun metrajlı film görüntü yönetmenliği",
             "taban": 15, "q_carpan": False, "grup": 8},
    "8.11": {"ad": "Uzun metrajlı film senaryo yazarlığı",
             "taban": 10, "q_carpan": False, "grup": 8},
    "8.12": {"ad": "Kısa film/belgesel yönetmenliği",
             "taban": 10, "q_carpan": False, "grup": 8},
    "8.13": {"ad": "Kısa film/belgesel görüntü yönetmenliği",
             "taban": 7,  "q_carpan": False, "grup": 8},
    "8.14": {"ad": "Kısa film/belgesel senaryo yazarlığı",
             "taban": 8,  "q_carpan": False, "grup": 8},
    "8.15": {"ad": "Ulusal TV film/dizi yönetmenliği",
             "taban": 20, "q_carpan": False, "grup": 8},
    "8.16": {"ad": "TV film/dizi görüntü yönetmenliği",
             "taban": 10, "q_carpan": False, "grup": 8},
    "8.17": {"ad": "Ulusal TV film/dizi senaryo yazarlığı",
             "taban": 10, "q_carpan": False, "grup": 8},
    "8.18": {"ad": "Ulusal TV programı yönetmenliği",
             "taban": 10, "q_carpan": False, "grup": 8},
    "8.19": {"ad": "Ulusal TV programı kameramanlığı",
             "taban": 5,  "q_carpan": False, "grup": 8},
    "8.20": {"ad": "Ulusal TV programı metin yazarlığı",
             "taban": 8,  "q_carpan": False, "grup": 8},
    "8.21": {"ad": "Ulusal TV reklam yönetmenliği",
             "taban": 10, "q_carpan": False, "grup": 8},
    "8.22": {"ad": "Ulusal TV reklam kameramanlığı",
             "taban": 5,  "q_carpan": False, "grup": 8},
    "8.23": {"ad": "Ulusal TV reklam metin yazarlığı",
             "taban": 5,  "q_carpan": False, "grup": 8},
    "8.24": {"ad": "Uluslararası film festivali katılımı",
             "taban": 30, "q_carpan": False, "grup": 8},
    "8.25": {"ad": "Ulusal film festivali katılımı",
             "taban": 20, "q_carpan": False, "grup": 8},

    # -------- 9. SANAT VE TASARIM --------
    "9.1":  {"ad": "Yurt dışı bireysel sergi (müze/galeri/üniversite)",
             "taban": 20, "q_carpan": False, "grup": 9},
    "9.2":  {"ad": "Yurt içi bireysel sergi",
             "taban": 10, "q_carpan": False, "grup": 9},
    "9.3":  {"ad": "Uluslararası karma sergi kataloğu/dergi/kitapta eser",
             "taban": 8,  "q_carpan": False, "grup": 9},
    "9.4":  {"ad": "Yurt içi uluslararası karma sergi kataloğunda eser",
             "taban": 6,  "q_carpan": False, "grup": 9},
    "9.5":  {"ad": "Ulusal karma sergi kataloğunda eser",
             "taban": 5,  "q_carpan": False, "grup": 9},
    "9.6":  {"ad": "Yurt dışı müze/koleksiyona eser kabulü",
             "taban": 30, "q_carpan": False, "grup": 9},
    "9.7":  {"ad": "Yurt içi müze/koleksiyona eser kabulü",
             "taban": 15, "q_carpan": False, "grup": 9},
    "9.8":  {"ad": "Yurt içi müze/özel koleksiyonda eser",
             "taban": 10, "q_carpan": False, "grup": 9},
    "9.9":  {"ad": "Uluslararası tasarım üretime girmiş çalışma/koleksiyon",
             "taban": 10, "q_carpan": False, "grup": 9},
    "9.10": {"ad": "Ulusal tasarım üretime girmiş çalışma/koleksiyon",
             "taban": 10, "q_carpan": False, "grup": 9},
    "9.11": {"ad": "Yurt dışı uluslararası gösteri/defile",
             "taban": 20, "q_carpan": False, "grup": 9},
    "9.12": {"ad": "Yurt içi uluslararası gösteri/defile",
             "taban": 15, "q_carpan": False, "grup": 9},
    "9.13": {"ad": "Ulusal gösteri/defile",
             "taban": 10, "q_carpan": False, "grup": 9},
    "9.14": {"ad": "Yurt dışı uluslararası sahne tasarımı etkinliği",
             "taban": 30, "q_carpan": False, "grup": 9},
    "9.15": {"ad": "Yurt içi uluslararası sahne tasarımı etkinliği",
             "taban": 20, "q_carpan": False, "grup": 9},
    "9.16": {"ad": "Ulusal sahne tasarımı etkinliği",
             "taban": 15, "q_carpan": False, "grup": 9},
    "9.17a": {"ad": "Yurt dışı uluslararası gösteri/koreografi",
              "taban": 20, "q_carpan": False, "grup": 9},
    "9.17b": {"ad": "Yurt dışı uluslararası gösteride solo dans",
              "taban": 15, "q_carpan": False, "grup": 9},
    "9.17c": {"ad": "Yurt dışı uluslararası gösteride grup dansı",
              "taban": 10, "q_carpan": False, "grup": 9},
    "9.18a": {"ad": "Yurt içi uluslararası gösteri/koreografi",
              "taban": 15, "q_carpan": False, "grup": 9},
    "9.18b": {"ad": "Yurt içi uluslararası gösteride solo dans",
              "taban": 10, "q_carpan": False, "grup": 9},
    "9.18c": {"ad": "Yurt içi uluslararası gösteride grup dansı",
              "taban": 5,  "q_carpan": False, "grup": 9},
    "9.19a": {"ad": "Ulusal gösteri/koreografi",
              "taban": 15, "q_carpan": False, "grup": 9},
    "9.19b": {"ad": "Ulusal gösteride solo dans",
              "taban": 10, "q_carpan": False, "grup": 9},
    "9.19c": {"ad": "Ulusal gösteride grup dansı",
              "taban": 5,  "q_carpan": False, "grup": 9},
    "9.20": {"ad": "Uluslararası seçkin tiyatroda önemli rol",
             "taban": 20, "q_carpan": False, "grup": 9},
    "9.21": {"ad": "Ulusal seçkin tiyatroda önemli rol",
             "taban": 10, "q_carpan": False, "grup": 9},
    "9.22": {"ad": "Tam uzunlukta oyun sahneleme",
             "taban": 20, "q_carpan": False, "grup": 9},
    "9.23": {"ad": "Kısa oyun sahneleme",
             "taban": 10, "q_carpan": False, "grup": 9},
    "9.24": {"ad": "Sahne oyunu yazma",
             "taban": 20, "q_carpan": False, "grup": 9},
    "9.25": {"ad": "Kısa sahne oyunu yazma",
             "taban": 10, "q_carpan": False, "grup": 9},
    "9.26": {"ad": "Metin çevirisi/düzenlemesi/uyarlaması",
             "taban": 10, "q_carpan": False, "grup": 9},
    "9.27": {"ad": "Yurt dışı bireysel dinleti",
             "taban": 15, "q_carpan": False, "grup": 9},
    "9.28": {"ad": "Yurt içi karma dinleti",
             "taban": 10, "q_carpan": False, "grup": 9},
    "9.29": {"ad": "Uluslararası etkinlikte çalgı/ses icracısı",
             "taban": 7,  "q_carpan": False, "grup": 9},
    "9.30": {"ad": "Ulusal etkinlikte çalgı/ses icracısı",
             "taban": 7,  "q_carpan": False, "grup": 9},
    "9.31": {"ad": "Koro/orkestra şefliği",
             "taban": 15, "q_carpan": False, "grup": 9},
    "9.32": {"ad": "CD stüdyo kaydı",
             "taban": 7,  "q_carpan": False, "grup": 9},
    "9.33": {"ad": "Konser/dinleti sanat yönetmenliği",
             "taban": 7,  "q_carpan": False, "grup": 9},
    "9.34": {"ad": "Yurt içi uluslararası ses/çalgı yarışması jürisi",
             "taban": 10, "q_carpan": False, "grup": 9},
    "9.35": {"ad": "Yurt içi ulusal ses/çalgı yarışması jürisi",
             "taban": 5,  "q_carpan": False, "grup": 9},
    "9.36": {"ad": "Yurt içi radyo/TV yayınına icracı/konuk katılım",
             "taban": 2,  "q_carpan": False, "grup": 9},

    # -------- 10. SPORTİF ETKİNLİKLER --------
    "10.1":  {"ad": "Olimpiyat/Dünya/Avrupa şampiyonası hakem/idareci",
              "taban": 25, "q_carpan": False, "grup": 10},
    "10.2":  {"ad": "Uluslararası antrenör/hakem eğitim kursu eğiticisi",
              "taban": 20, "q_carpan": False, "grup": 10},
    "10.3":  {"ad": "Sahne sanatları grubu yurt dışı sunum",
              "taban": 10, "q_carpan": False, "grup": 10},
    "10.4":  {"ad": "Milli takımda görev (idareci/antrenör vb.)",
              "taban": 20, "q_carpan": False, "grup": 10},
    "10.5":  {"ad": "Uluslararası müsabakada hakemlik",
              "taban": 15, "q_carpan": False, "grup": 10},
    "10.6":  {"ad": "Uluslararası organizasyonda idareci/yönetici",
              "taban": 10, "q_carpan": False, "grup": 10},
    "10.7":  {"ad": "Uluslararası federasyon yönetim/teknik/hakem kurulu",
              "taban": 15, "q_carpan": False, "grup": 10},
    "10.8":  {"ad": "Ulusal antrenör/hakem eğitim kursu eğiticisi",
              "taban": 7,  "q_carpan": False, "grup": 10},
    "10.9":  {"ad": "Sahne sanatları grubu yurt içi sunum",
              "taban": 5,  "q_carpan": False, "grup": 10},
    "10.10": {"ad": "Amatör takımda görev",
              "taban": 4,  "q_carpan": False, "grup": 10},
    "10.11": {"ad": "Profesyonel takımda görev",
              "taban": 7,  "q_carpan": False, "grup": 10},
    "10.12": {"ad": "Ulusal federasyon yönetim/teknik/hakem kurulu",
              "taban": 5,  "q_carpan": False, "grup": 10},
    "10.13": {"ad": "Ulusal organizasyonda hakem/idareci/yönetici",
              "taban": 4,  "q_carpan": False, "grup": 10},
    "10.14": {"ad": "TÜSF organizasyonunda görev",
              "taban": 7,  "q_carpan": False, "grup": 10},
    "10.15": {"ad": "Ulusal federasyondan 1. kademe antrenörlük belgesi",
              "taban": 5,  "q_carpan": False, "grup": 10},
    "10.16": {"ad": "Ulusal federasyondan 2-5. kademe antrenörlük belgesi",
              "taban": 10, "q_carpan": False, "grup": 10},
    "10.17": {"ad": "Sağlık Kültür Spor Daire Başkanlığı organizasyonu",
              "taban": 3,  "q_carpan": False, "grup": 10},

    # -------- 11. PATENTLER --------
    "11.1":  {"ad": "Uluslararası patent (tescilli=50, araştırma raporu=25, başvuru=12.5)",
              "taban": 50, "q_carpan": False, "grup": 11},
    "11.2":  {"ad": "Türk patenti (tescilli)",
              "taban": 35, "q_carpan": False, "grup": 11},
    "11.3":  {"ad": "Uluslararası faydalı model/çeşit tescili",
              "taban": 30, "q_carpan": False, "grup": 11},
    "11.4":  {"ad": "Ulusal faydalı model/çeşit tescili",
              "taban": 15, "q_carpan": False, "grup": 11},
    "11.5":  {"ad": "Uluslararası tasarım tescili",
              "taban": 20, "q_carpan": False, "grup": 11},
    "11.6":  {"ad": "Ulusal tasarım tescili",
              "taban": 10, "q_carpan": False, "grup": 11},
    "11.7":  {"ad": "Ulusal incelemesiz patent (tescilli=15, araştırma=7.5, başvuru=3.75)",
              "taban": 15, "q_carpan": False, "grup": 11},
    "11.8":  {"ad": "TGB'de firma sahibi/ortağı",
              "taban": 15, "q_carpan": False, "grup": 11},
    "11.9":  {"ad": "TGB/sanayi AR-GE danışmanlığı",
              "taban": 3,  "q_carpan": False, "grup": 11},
    "11.10": {"ad": "Diğer bilimsel/sanatsal danışmanlık (uluslararası=4)",
              "taban": 2,  "q_carpan": False, "grup": 11},

    # -------- 12. PROJELER --------
    "12.1":  {"ad": "AB destekli proje yürütücülüğü",
              "taban": 50, "q_carpan": False, "grup": 12},
    "12.2":  {"ad": "AB destekli projede görev",
              "taban": 35, "q_carpan": False, "grup": 12},
    "12.3":  {"ad": "TÜBİTAK büyük ARGE projesinde yürütücülük (≥5×1002)",
              "taban": 30, "q_carpan": False, "grup": 12},
    "12.4":  {"ad": "TÜBİTAK büyük ARGE projesinde görev (≥5×1002)",
              "taban": 25, "q_carpan": False, "grup": 12},
    "12.5":  {"ad": "Diğer TÜBİTAK projesinde yürütücülük",
              "taban": 20, "q_carpan": False, "grup": 12},
    "12.6":  {"ad": "Diğer TÜBİTAK projesinde görev",
              "taban": 10, "q_carpan": False, "grup": 12},
    "12.7":  {"ad": "TGB projesinde yürütücülük",
              "taban": 10, "q_carpan": False, "grup": 12},
    "12.8":  {"ad": "TGB projesinde görev",
              "taban": 5,  "q_carpan": False, "grup": 12},
    "12.9":  {"ad": "Uluslararası üniversite/kamu destekli projede yürütücülük",
              "taban": 20, "q_carpan": False, "grup": 12},
    "12.10": {"ad": "Uluslararası üniversite/kamu destekli projede görev",
              "taban": 10, "q_carpan": False, "grup": 12},
    "12.11": {"ad": "Yükseköğretim BAP yürütücülüğü",
              "taban": 10, "q_carpan": False, "grup": 12},
    "12.12": {"ad": "Yükseköğretim BAP'ta görev",
              "taban": 5,  "q_carpan": False, "grup": 12},
    "12.13": {"ad": "Kamu kurumu destekli bilimsel projede yürütücülük",
              "taban": 20, "q_carpan": False, "grup": 12},
    "12.14": {"ad": "Kamu kurumu destekli bilimsel projede görev",
              "taban": 10, "q_carpan": False, "grup": 12},

    # -------- 13. ÇALIŞTAY/KONGRE (max 20 puan) --------
    "13.1":  {"ad": "Uluslararası kongre/konferans yöneticisi",
              "taban": 10, "q_carpan": False, "grup": 13, "max_grup": 20},
    "13.2":  {"ad": "Uluslararası kongre/konferans görevlisi (sekretarya vb.)",
              "taban": 5,  "q_carpan": False, "grup": 13, "max_grup": 20},
    "13.3":  {"ad": "Uluslararası kongre/konferans katılımcısı",
              "taban": 3,  "q_carpan": False, "grup": 13, "max_grup": 20},
    "13.4":  {"ad": "Ulusal kongre/konferans yöneticisi",
              "taban": 5,  "q_carpan": False, "grup": 13, "max_grup": 20},
    "13.5":  {"ad": "Ulusal kongre/konferans görevlisi",
              "taban": 3,  "q_carpan": False, "grup": 13, "max_grup": 20},
    "13.6":  {"ad": "Ulusal kongre/konferans katılımcısı",
              "taban": 1,  "q_carpan": False, "grup": 13, "max_grup": 20},
    "13.7":  {"ad": "Uluslararası sanatsal etkinlik yürütücüsü/küratörü",
              "taban": 10, "q_carpan": False, "grup": 13, "max_grup": 20},
    "13.8":  {"ad": "Yurt içi uluslararası sanatsal etkinlik yürütücüsü/küratörü",
              "taban": 7,  "q_carpan": False, "grup": 13, "max_grup": 20},
    "13.9":  {"ad": "Uluslararası sanatsal etkinlikte görev",
              "taban": 5,  "q_carpan": False, "grup": 13, "max_grup": 20},
    "13.10": {"ad": "Yurt içi uluslararası sanatsal etkinlikte görev",
              "taban": 3,  "q_carpan": False, "grup": 13, "max_grup": 20},
    "13.11": {"ad": "Ulusal sanatsal etkinlikte görev",
              "taban": 2,  "q_carpan": False, "grup": 13, "max_grup": 20},
    "13.12": {"ad": "Ulusal sanatsal etkinlik yürütücüsü/küratörü",
              "taban": 5,  "q_carpan": False, "grup": 13, "max_grup": 20},

    # -------- 14. ÖDÜLLER --------
    "14.1":  {"ad": "Yurt dışı uluslararası yarışmada derece (güzel sanatlar/mimari)",
              "taban": 50, "q_carpan": False, "grup": 14},
    "14.2":  {"ad": "Yurt dışı uluslararası yarışmada mansiyon/özel ödül",
              "taban": 40, "q_carpan": False, "grup": 14},
    "14.3":  {"ad": "Yurt içi uluslararası yarışmada derece",
              "taban": 40, "q_carpan": False, "grup": 14},
    "14.4":  {"ad": "Yurt içi uluslararası yarışmada mansiyon",
              "taban": 25, "q_carpan": False, "grup": 14},
    "14.5":  {"ad": "Ulusal yarışmada derece",
              "taban": 40, "q_carpan": False, "grup": 14},
    "14.6":  {"ad": "Ulusal yarışmada mansiyon/jüri özel ödülü",
              "taban": 20, "q_carpan": False, "grup": 14},
    "14.7":  {"ad": "Uluslararası yarışmaya katılım",
              "taban": 5,  "q_carpan": False, "grup": 14},
    "14.8":  {"ad": "Ulusal yarışmaya katılım",
              "taban": 3,  "q_carpan": False, "grup": 14},
    "14.9":  {"ad": "Yurt dışı kurum/kuruluş bilim/sanat ödülü",
              "taban": 40, "q_carpan": False, "grup": 14},
    "14.10": {"ad": "Yurt dışı jürili diğer ödül",
              "taban": 20, "q_carpan": False, "grup": 14},
    "14.11": {"ad": "Yurt içi kurum/kuruluş bilim/sanat ödülü",
              "taban": 20, "q_carpan": False, "grup": 14},
    "14.12": {"ad": "Yurt içi jürili diğer ödül",
              "taban": 10, "q_carpan": False, "grup": 14},

    # -------- 15. KAZI ÇALIŞMALARI --------
    "15.1":  {"ad": "Bakanlık onaylı arkeolojik kazı yönetimi",
              "taban": 15, "q_carpan": False, "grup": 15},
    "15.2":  {"ad": "Bakanlık onaylı arkeolojik kazıya katılım",
              "taban": 5,  "q_carpan": False, "grup": 15},
    "15.3":  {"ad": "Bakanlık onaylı yüzey araştırması yönetimi",
              "taban": 10, "q_carpan": False, "grup": 15},
    "15.4":  {"ad": "Bakanlık onaylı yüzey araştırmasına katılım",
              "taban": 3,  "q_carpan": False, "grup": 15},
    "15.5":  {"ad": "Arkeolojik araştırma sergisi açmak",
              "taban": 3,  "q_carpan": False, "grup": 15},
    "15.6":  {"ad": "Örgün eğitimde arkeolojik etkinlik düzenlemek",
              "taban": 3,  "q_carpan": False, "grup": 15},
    "15.7":  {"ad": "Arkeoloji müzesinde etkinlik yapmak",
              "taban": 2,  "q_carpan": False, "grup": 15},

    # -------- 16. YURT DIŞI DENEYİMİ --------
    "16.1":  {"ad": "Yurt dışı deneyimi (kesintisiz 3 ay+)",
              "taban": 5,  "q_carpan": False, "grup": 16},
    "16.2":  {"ad": "Uluslararası bilimsel/sanatsal burs (her burs için)",
              "taban": 5,  "q_carpan": False, "grup": 16},
    "16.3":  {"ad": "Ulusal bilimsel/sanatsal burs (her burs için)",
              "taban": 3,  "q_carpan": False, "grup": 16},

    # -------- 17. EĞİTİM-ÖĞRETİM --------
    "17.1":  {"ad": "Doktora/uzmanlık tez yönetimi (2. danışman = yarı puan)",
              "taban": 12, "q_carpan": False, "grup": 17},
    "17.2":  {"ad": "Yüksek lisans tez yönetimi (2. danışman = yarı puan)",
              "taban": 8,  "q_carpan": False, "grup": 17},
    "17.3":  {"ad": "Tez jürisi/komitesi (doktorada tam, yüksek lisansta yarı puan)",
              "taban": 2,  "q_carpan": False, "grup": 17},
    "17.4":  {"ad": "Ön lisans/lisans/lisansüstü ders (son 3 yılda her dönem için)",
              "taban": 5,  "q_carpan": False, "grup": 17},

    # -------- 18. İDARİ GÖREVLER --------
    "18.1":  {"ad": "Rektör / Rektör Yardımcısı (yıllık)",
              "taban": 15, "q_carpan": False, "grup": 18},
    "18.2":  {"ad": "Dekan/Başhekim/Enstitü-Yüksekokul Müdürü (yıllık)",
              "taban": 10, "q_carpan": False, "grup": 18},
    "18.3":  {"ad": "Senato Üyesi/Dekan Yrd./Enstitü Müdür Yrd./Merkez Müdürü (yıllık)",
              "taban": 5,  "q_carpan": False, "grup": 18},
    "18.4":  {"ad": "Bölüm başkanlığı (yıllık)",
              "taban": 4,  "q_carpan": False, "grup": 18},
    "18.5":  {"ad": "Bölüm başkan yrd./ABD başkanlığı/koordinatörlük (yıllık)",
              "taban": 3,  "q_carpan": False, "grup": 18},
    "18.6":  {"ad": "Dergi/gazete faaliyetinde görev (yıllık)",
              "taban": 3,  "q_carpan": False, "grup": 18},
    "18.7":  {"ad": "Öğrenci sınıf/kulüp danışmanlığı (yıllık)",
              "taban": 2,  "q_carpan": False, "grup": 18},
    "18.8":  {"ad": "Kongre/sempozyum düzenleme görevi (en fazla 10 puan)",
              "taban": 2,  "q_carpan": False, "grup": 18},
    "18.9":  {"ad": "Üniversite dışı kurul/komisyon üyeliği (yıllık)",
              "taban": 2,  "q_carpan": False, "grup": 18},
    "18.10": {"ad": "Üniversite bünyesi koordinatörlük/komisyon üyeliği (yıllık)",
              "taban": 2,  "q_carpan": False, "grup": 18},

    # -------- 19. DİĞER --------
    "19.1":  {"ad": "YÖK kabul sınavında ≥85 puan (yabancı dil bölümü farklı)",
              "taban": 10, "q_carpan": False, "grup": 19},
}

# ── PUAN-1 kapsam kodları (kadro türüne göre, EK-1 tablosundan) ─────────────
# Her kadro türünde PUAN-1'e giren EK-2 kodlarıdır.
# PUAN-2 ise EK-2'nin tamamından oluşabilir (PUAN-1 fazlası dahil — madde a).
PUAN1_KODLAR: dict[str, frozenset] = {
    # Dr. Öğr. Üyesi ilk atanma
    "dr_ilk": frozenset([
        "1.1", "1.2", "1.3", "1.4", "1.5", "1.6",
    ]),
    # Dr. Öğr. Üyesi yeniden atanma (1, 2, 3 yıl)
    "dr_yeniden": frozenset([
        "1.1", "1.2", "1.3", "1.4", "1.5", "1.6",
        "2.1", "2.2", "2.4", "2.5",
    ]),
    # Doçent
    "docent": frozenset([
        "1.1", "1.2", "1.3", "1.4", "1.5", "1.6",
    ]),
    # Profesör
    "profesor": frozenset([
        "1.1", "1.2", "1.3", "1.4", "1.5", "1.6",
    ]),
}


def is_puan1(kod: str, kadro_turu: str) -> bool:
    """Belirli kadro türünde bu EK-2 kodunun PUAN-1'e girip girmediğini döndürür."""
    return kod in PUAN1_KODLAR.get(kadro_turu, frozenset())


@dataclass
class Faaliyet:
    """Bir akademik faaliyeti temsil eder."""
    kod: str                  # EK-2 kodu (örn. "1.1")
    adet: int = 1             # kaç adet yapıldı
    toplam_yazar: int = 1     # yayın için toplam yazar sayısı
    yazar_sirasi: int = 1     # kişinin yazar sırası
    sorumlu_veya_senyör: bool = False  # Sorumlu/Senyör yazar mı?
    q_degeri: Optional[str] = None    # "Q1", "Q2", "Q3", "Q4" (1.1/1.3/4.1 için)
    # Patent durumu için (11.1, 11.7)
    patent_durum: Optional[str] = None  # "tescilli", "arastirma_raporu", "basvuru"
    # İkinci danışman mı? (17.1, 17.2)
    ikinci_danisман: bool = False
    # Doçentlik sonrası mı?
    docent_sonrasi: bool = False


def q_carpan_al(q: Optional[str]) -> float:
    carpanlar = {"Q1": 2.0, "Q2": 1.5, "Q3": 1.25, "Q4": 1.0}
    return carpanlar.get(q or "Q4", 1.0)


def faaliyet_puan_hesapla(f: Faaliyet) -> tuple[float, bool]:
    """
    Faaliyetin toplam puanını hesaplar.
    Döndürür: (puan, puan1_mi)
    puan1_mi → bu faaliyet PUAN-1 kapsamında mı?
    """
    if f.kod not in EK2_PUANLAR:
        return 0.0, False

    bilgi = EK2_PUANLAR[f.kod]
    taban = bilgi["taban"]
    grup = bilgi["grup"]

    # Q çarpanı
    if bilgi["q_carpan"] and f.q_degeri:
        taban = taban * q_carpan_al(f.q_degeri)

    # Patent durumu çarpanı (11.1 ve 11.7)
    if f.kod in ("11.1", "11.7") and f.patent_durum:
        if f.patent_durum == "arastirma_raporu":
            taban = taban * 0.5
        elif f.patent_durum == "basvuru":
            taban = taban * 0.25

    # İkinci danışman çarpanı (17.1, 17.2)
    if f.kod in ("17.1", "17.2") and f.ikinci_danisман:
        taban = taban * 0.5

    # Tez jürisi: Yüksek lisansta yarı puan (17.3)
    # (kullanıcı adet ile girebilir; burada otomatik yarı yapmıyoruz,
    #  kullanıcı bilinçli girmeli)

    # Yazar çarpanı (yayınlar için)
    if f.toplam_yazar > 0 and grup in {1, 2, 3}:
        yc = yazar_carpani_hesapla(f.toplam_yazar, f.yazar_sirasi,
                                   f.sorumlu_veya_senyör)
        taban = taban * yc

    puan = taban * f.adet

    # Genel "P1 adayı mı?" işareti: en geniş P1 kümesine (dr_yeniden) göre
    # Gerçek kadro bazlı ayrım için is_puan1() / puan_hesapla() kullanın.
    puan1_mi_genel = f.kod in PUAN1_KODLAR["dr_yeniden"]

    return round(puan, 2), puan1_mi_genel


# ---------------------------------------------------------------------------
# Atama Kriteri Kontrolü
# ---------------------------------------------------------------------------

@dataclass
class AdayBilgi:
    ad_soyad: str = ""
    alan: str = "ALAN-1"           # "ALAN-1" veya "ALAN-2"
    guzel_sanat: bool = False      # Güzel Sanatlar temel alanı mı?
    kadro_turu: str = "dr"         # "dr_ilk", "dr_yeniden", "docent", "profesör"
    yeniden_sure: int = 3          # Yeniden atama: 1, 2 veya 3 yıl
    faaliyetler: list[Faaliyet] = field(default_factory=list)

    # Genel kriterler
    doktora_var: bool = False
    yabanci_dil_puani: float = 0.0
    calisma_alani_yabanci_dil_bolumu: bool = False
    ornek_ders_basarili: bool = False
    uak_docent: bool = False
    sifahi_sinav_basarili: bool = False
    doktora_sonrasi_ders_yari_yil: int = 0  # Doçent/Prof. için ≥4 dönem
    docent_sonrasi_sure_yil: float = 0.0   # Prof. için ≥2.5 yıl
    baslica_arastirma_eseri_var: bool = False  # Prof. için


def puan_hesapla(aday: AdayBilgi) -> dict:
    """
    Tüm faaliyetlerden PUAN-1 ve PUAN-2 toplamlarını hesaplar.

    PUAN-1 kapsamı kadro türüne göre PUAN1_KODLAR ile belirlenir.
    PUAN-2 = EK-2'nin tamamı (PUAN-1 fazlası da dahil — madde a).
    """
    p1_kodlar = PUAN1_KODLAR.get(aday.kadro_turu, PUAN1_KODLAR["dr_ilk"])
    # (d): dr_yeniden'de bu kodlar P1'de %25 sınırına tabidir
    KITAP_KODLAR_D = frozenset(["2.1", "2.2", "2.4", "2.5"])

    puan1_toplam        = 0.0
    puan2_toplam        = 0.0
    puan1_kitap_yeniden = 0.0   # (d): 2.1/2.2/2.4/2.5 → P1'e giren miktar
    puan1_alan1_11_var  = False  # (e): PUAN-1'de en az 1 adet 1.1 kodu
    puan1_b_kural_var   = False  # (b): Q1/Q2/Q3'te 1.1, 1./sor./senyör → P1 otomatik

    grup_toplamlar: dict[int, float] = {}
    detaylar = []

    for f in aday.faaliyetler:
        p, _ = faaliyet_puan_hesapla(f)
        if f.kod not in EK2_PUANLAR:
            continue
        bilgi    = EK2_PUANLAR[f.kod]
        grup     = bilgi["grup"]
        max_grup = bilgi.get("max_grup")

        # Grup bazlı maksimum puan sınırı
        if max_grup is not None:
            mevcut = grup_toplamlar.get(grup, 0.0)
            kalan  = max(0.0, max_grup - mevcut)
            p      = min(p, kalan)
            grup_toplamlar[grup] = mevcut + p
        else:
            grup_toplamlar[grup] = grup_toplamlar.get(grup, 0.0) + p

        # Kod bazlı PUAN-1 / PUAN-2 ayrımı
        puan1_mi = f.kod in p1_kodlar
        if puan1_mi:
            puan1_toplam += p
            if f.kod in KITAP_KODLAR_D:
                puan1_kitap_yeniden += p   # (d) izleme
        else:
            puan2_toplam += p

        # (e): ALAN-1 koşulu – PUAN-1'deki herhangi bir 1.1 yayını yeter
        if f.kod == "1.1" and puan1_mi:
            puan1_alan1_11_var = True

        # (b): Q1/Q2/Q3'te 1.1, 1. isim / sorumlu / senyör yazar
        if (f.kod == "1.1" and puan1_mi
                and (f.sorumlu_veya_senyör or f.yazar_sirasi == 1)
                and f.q_degeri in ("Q1", "Q2", "Q3")):
            puan1_b_kural_var = True

        detaylar.append({
            "kod": f.kod, "ad": bilgi["ad"], "adet": f.adet,
            "puan": p, "puan1_mi": puan1_mi,
        })

    return {
        "puan1":               round(puan1_toplam, 2),
        "puan2":               round(puan2_toplam, 2),
        "toplam":              round(puan1_toplam + puan2_toplam, 2),
        "puan1_alan1_11_var":  puan1_alan1_11_var,
        "puan1_b_kural_var":   puan1_b_kural_var,
        "puan1_kitap_yeniden": round(puan1_kitap_yeniden, 2),
        "detaylar":            detaylar,
    }


def kriter_kontrol(aday: AdayBilgi) -> dict:
    """
    Adayın ilgili kadroya atanma/yükseltilme kriterlerini karşılayıp
    karşılamadığını kontrol eder.
    """
    sonuclar = []
    puanlar = puan_hesapla(aday)

    p1 = puanlar["puan1"]
    p2 = puanlar["puan2"]
    toplam = puanlar["toplam"]

    def ekle(kriter, durum, notlar=""):
        sonuclar.append({"kriter": kriter,
                         "durum": "✓ SAĞLANIYOR" if durum else "✗ SAĞLANMIYOR",
                         "notlar": notlar})
        return durum

    if aday.kadro_turu == "dr_ilk":
        # --- Dr. Öğretim Üyesi İlk Atanma ---
        ekle("Doktora/Uzmanlık/Yeterlilik",
             aday.doktora_var)

        # Yabancı dil
        if aday.calisma_alani_yabanci_dil_bolumu:
            ekle("Yabancı dil ≥85",
                 aday.yabanci_dil_puani >= 85,
                 f"Girilen puan: {aday.yabanci_dil_puani}")
        else:
            ekle("Yabancı dil (YÖKDİL/YDS) ≥60",
                 aday.yabanci_dil_puani >= 60,
                 f"Girilen puan: {aday.yabanci_dil_puani}")

        ekle("Örnek ders başarısı",
             aday.ornek_ders_basarili)

        # Puan koşulları
        puan1_asgarisi = 30
        puan2_asgarisi = 50
        toplam_asgari = 80

        # PUAN-1 = kodlar 1.1–1.6 (puan_hesapla tarafından hesaplandı)
        # (a) PUAN-1 fazlası → PUAN-2
        puan1_asgarisi = 30
        puan2_asgarisi = 50
        toplam_asgari  = 80

        p1_fazla   = max(0.0, p1 - puan1_asgarisi)
        p2_efektif = p2 + p1_fazla

        # (b): Q1/Q2/Q3, 1./sor./senyör yazar → PUAN-1 otomatik sağlanır
        if puanlar["puan1_b_kural_var"]:
            ekle("(b) PUAN-1 otomatik sağlandı (Q1/Q2/Q3, 1./sor./senyör yazar)",
                 True,
                 "Bir adet Q1/Q2/Q3 yayınıyla PUAN-1 koşulu karşılandı")
        else:
            ekle(f"PUAN-1 ≥{puan1_asgarisi} (EK-2: 1.1–1.6)",
                 p1 >= puan1_asgarisi,
                 f"PUAN-1: {p1}")
        ekle(f"PUAN-2 ≥{puan2_asgarisi} (EK-2 tamamı, P1 fazlası dahil)",
             p2_efektif >= puan2_asgarisi,
             f"PUAN-2 + P1 fazlası: {round(p2_efektif, 2)}")
        ekle(f"Toplam ≥{toplam_asgari}",
             toplam >= toplam_asgari,
             f"Toplam: {toplam}")

        if aday.alan == "ALAN-1":
            ekle("(e) ALAN-1: PUAN-1'de en az 1 EK-2(1.1) olmalıdır",
                 puanlar["puan1_alan1_11_var"])

    elif aday.kadro_turu == "dr_yeniden":
        sure = aday.yeniden_sure
        if sure == 3:
            puan1_asgarisi, puan2_asgarisi, toplam_asgari = 40, 40, 80
        elif sure == 2:
            puan1_asgarisi, puan2_asgarisi, toplam_asgari = 30, 30, 60
        else:  # 1 yıl
            puan1_asgarisi, puan2_asgarisi, toplam_asgari = 20, 20, 40

        # PUAN-1 = kodlar 1.1–1.6 + 2.1, 2.2, 2.4, 2.5 (puan_hesapla hesapladı)
        # (d): 2.1/2.2/2.4/2.5'ten gelen PUAN-1 payı, P1 asgari'nin %25'iyle sınırlı
        p1_kitap_max   = puan1_asgarisi * 0.25
        p1_kitap_asiri = max(0.0, puanlar["puan1_kitap_yeniden"] - p1_kitap_max)
        p1_efektif     = p1 - p1_kitap_asiri  # (d) fazlası P1'den düşülür
        # (a) PUAN-1 fazlası → PUAN-2
        p1_fazla   = max(0.0, p1_efektif - puan1_asgarisi)
        p2_efektif = p2 + p1_fazla + p1_kitap_asiri  # (d) + (a) fazlası P2'ye

        # (b): Q1/Q2/Q3, 1./sor./senyör yazar → PUAN-1 otomatik sağlanır
        if puanlar["puan1_b_kural_var"]:
            ekle("(b) PUAN-1 otomatik sağlandı (Q1/Q2/Q3, 1./sor./senyör yazar)",
                 True,
                 "Bir adet Q1/Q2/Q3 yayınıyla PUAN-1 koşulu karşılandı")
        else:
            p1_not = f"PUAN-1: {p1}"
            if p1_kitap_asiri > 0:
                p1_not += (f"  [(d) 2.1/2.2/2.4/2.5 fazlası "
                           f"{round(p1_kitap_asiri, 2)} puan P2'ye aktarıldı]")
            ekle(f"PUAN-1 ≥{puan1_asgarisi} (EK-2: 1.1–1.6, 2.1/2.2/2.4/2.5; (d) %25 üst sınır)",
                 p1_efektif >= puan1_asgarisi,
                 p1_not)
        ekle(f"PUAN-2 ≥{puan2_asgarisi} (EK-2 tamamı, P1 fazlası dahil)",
             p2_efektif >= puan2_asgarisi,
             f"PUAN-2 + P1 fazlası: {round(p2_efektif, 2)}")
        ekle(f"Toplam ≥{toplam_asgari}",
             toplam >= toplam_asgari,
             f"Toplam: {toplam}")

        if sure == 1:
            ekle("(f) Bilgi: 1 yıllık süre – bu dönem puanları sonraki süre "
                 "belirlemesinde önceki puanlarla birleştirilir",
                 True,
                 "Mevzuat gereği bilgilendirme; ayrı bir sınama kriteri değildir")
        elif aday.alan == "ALAN-1":
            ekle("(e) ALAN-1: PUAN-1'de en az 1 EK-2(1.1) olmalıdır",
                 puanlar["puan1_alan1_11_var"])

    elif aday.kadro_turu == "docent":
        ekle("ÜAK Doçent unvanı",
             aday.uak_docent)

        # Doçent için ÜAK sözlü sınavı artık zorunlu (istisnasız)
        ekle("ÜAK sözlü sınavı geçildi (zorunlu)",
             aday.sifahi_sinav_basarili)

        if aday.calisma_alani_yabanci_dil_bolumu:
            ekle("Yabancı dil ≥85",
                 aday.yabanci_dil_puani >= 85,
                 f"Girilen puan: {aday.yabanci_dil_puani}")
        else:
            ekle("Yabancı dil ≥65",
                 aday.yabanci_dil_puani >= 65,
                 f"Girilen puan: {aday.yabanci_dil_puani}")

        ekle("Doktora sonrası ≥4 farklı yarıyıl ders",
             aday.doktora_sonrasi_ders_yari_yil >= 4,
             f"Girilen: {aday.doktora_sonrasi_ders_yari_yil} yarıyıl")

        puan1_asgarisi = 25
        puan2_asgarisi = 300
        toplam_asgari = 325

        if aday.guzel_sanat:
            puan1_asgarisi = int(25 * 0.5)  # %50'si yeterli

        # PUAN-1 = kodlar 1.1–1.6 (puan_hesapla hesapladı)
        # (a) PUAN-1 fazlası → PUAN-2
        p1_fazla   = max(0.0, p1 - puan1_asgarisi)
        p2_efektif = p2 + p1_fazla

        ekle(f"PUAN-1 ≥{puan1_asgarisi} (EK-2: 1.1–1.6)",
             p1 >= puan1_asgarisi,
             f"PUAN-1: {p1}")
        ekle(f"PUAN-2 ≥{puan2_asgarisi} (EK-2 tamamı, P1 fazlası dahil)",
             p2_efektif >= puan2_asgarisi,
             f"PUAN-2 + P1 fazlası: {round(p2_efektif, 2)}")
        ekle(f"Toplam ≥{toplam_asgari}",
             toplam >= toplam_asgari,
             f"Toplam: {toplam}")

    elif aday.kadro_turu == "profesor":
        ekle("ÜAK Doçent unvanı",
             aday.uak_docent)

        sinav_carpan = 1.0
        if aday.sifahi_sinav_basarili:
            ekle("ÜAK sözlü sınavı geçildi (sınavlı başvuru yolu)",
                 True)
        else:
            ekle("Örnek ders 'Başarılı' (sözlü sınavsız başvuru – zorunlu)",
                 aday.ornek_ders_basarili)
            sinav_carpan = 1.20

        if aday.calisma_alani_yabanci_dil_bolumu:
            ekle("Yabancı dil ≥85",
                 aday.yabanci_dil_puani >= 85,
                 f"Girilen puan: {aday.yabanci_dil_puani}")
        else:
            ekle("Yabancı dil ≥65",
                 aday.yabanci_dil_puani >= 65,
                 f"Girilen puan: {aday.yabanci_dil_puani}")

        ekle("Doçent sonrası ≥4 farklı yarıyıl ders",
             aday.doktora_sonrasi_ders_yari_yil >= 4,
             f"Girilen: {aday.doktora_sonrasi_ders_yari_yil} yarıyıl")

        ekle("Doçent sonrası en az 2.5 yıl yükseköğretim kurumunda",
             aday.docent_sonrasi_sure_yil >= 2.5,
             f"Girilen: {aday.docent_sonrasi_sure_yil} yıl")

        ekle("Başlıca Araştırma Eseri sunulmuş (başlıca yazar olarak)",
             aday.baslica_arastirma_eseri_var)

        puan1_asgarisi = 50
        puan2_asgarisi = 500
        toplam_asgari = 550

        if aday.guzel_sanat:
            puan1_asgarisi = 25  # %50

        # Sınavsız başvuruda her puan türünde %20 fazla (Madde 11/3)
        p1_min  = round(puan1_asgarisi * sinav_carpan, 1)
        p2_min  = round(puan2_asgarisi * sinav_carpan, 1)
        top_min = round(toplam_asgari  * sinav_carpan, 1)
        sinav_not = "  (+%20 – sınavsız başvuru)" if sinav_carpan > 1 else ""

        # PUAN-1 = kodlar 1.1–1.6 (puan_hesapla hesapladı)
        # (a) PUAN-1 fazlası → PUAN-2
        p1_fazla   = max(0.0, p1 - p1_min)
        p2_efektif = p2 + p1_fazla

        # (g) Puanların ≥yarısı doçent sonrası olmalı
        docent_sonrasi = sum(
            faaliyet_puan_hesapla(f)[0]
            for f in aday.faaliyetler if f.docent_sonrasi
        )
        ekle(f"(g) Puanların en az yarısı (≥{int(top_min//2)}) doçent sonrası",
             docent_sonrasi >= top_min / 2,
             f"Doçent sonrası puan: {round(docent_sonrasi, 2)}")

        ekle(f"PUAN-1 ≥{p1_min} (EK-2: 1.1–1.6){sinav_not}",
             p1 >= p1_min,
             f"PUAN-1: {p1}")
        ekle(f"PUAN-2 ≥{p2_min} (EK-2 tamamı, P1 fazlası dahil){sinav_not}",
             p2_efektif >= p2_min,
             f"PUAN-2 + P1 fazlası: {round(p2_efektif, 2)}")
        ekle(f"Toplam ≥{top_min}{sinav_not}",
             toplam >= top_min,
             f"Toplam: {toplam}")

    genel_basari = all(
        "✓" in s["durum"] for s in sonuclar
    )
    return {
        "puanlar": puanlar,
        "kriterler": sonuclar,
        "genel_sonuc": genel_basari
    }


# ---------------------------------------------------------------------------
# Etkileşimli CLI
# ---------------------------------------------------------------------------

def temizle():
    print("\n" + "=" * 70)


def sec(prompt: str, secenekler: dict) -> str:
    while True:
        print(f"\n{prompt}")
        for k, v in secenekler.items():
            print(f"  {k}) {v}")
        tercih = input("Seçiminiz: ").strip()
        if tercih in secenekler:
            return tercih
        print("Geçersiz seçim, tekrar deneyin.")


def evet_hayir(prompt: str) -> bool:
    while True:
        cevap = input(f"{prompt} (e/h): ").strip().lower()
        if cevap in ("e", "evet", "y", "yes"):
            return True
        if cevap in ("h", "hayır", "hayir", "n", "no"):
            return False


def sayi_al(prompt: str, tam: bool = False,
            min_val: float = 0, max_val: float = 1e9) -> float:
    while True:
        try:
            v = input(f"{prompt}: ").strip()
            val = int(v) if tam else float(v)
            if min_val <= val <= max_val:
                return val
            print(f"  {min_val} ile {max_val} arasında bir değer girin.")
        except ValueError:
            print("  Geçersiz sayı.")


def faaliyet_ekle_interaktif() -> list[Faaliyet]:
    """Kullanıcıdan faaliyet listesi alır."""
    faaliyetler: list[Faaliyet] = []

    # Kısa grup açıklamaları
    gruplar = {
        "1": "Makale",
        "2": "Kitap / Kitap Bölümü",
        "3": "Bildiri / Ansiklopedi",
        "4": "Editörlük (max 40 puan)",
        "5": "Atıf (max 50 puan)",
        "6": "Hakemlik (max 20 puan)",
        "7": "Panelist / Jüri Üyeliği (max 20 puan)",
        "8": "TV-Sinema-Tasarım",
        "9": "Sanat ve Tasarım",
        "10": "Sportif Etkinlikler",
        "11": "Patentler ve Girişimler",
        "12": "Projeler",
        "13": "Çalıştay-Kongre-Workshop (max 20 puan)",
        "14": "Ödüller",
        "15": "Kazı Çalışmaları",
        "16": "Yurt Dışı Deneyimi ve Burslar",
        "17": "Eğitim-Öğretim Faaliyetleri",
        "18": "İdari Görevler",
        "19": "Diğer Faaliyetler",
    }

    while True:
        temizle()
        print("FAAALİYET EKLEME")
        print("─" * 40)
        print("Mevcut faaliyetler:", len(faaliyetler))
        if faaliyetler:
            for i, f in enumerate(faaliyetler, 1):
                p, _ = faaliyet_puan_hesapla(f)
                print(f"  {i}. [{f.kod}] {EK2_PUANLAR.get(f.kod, {}).get('ad', '')[:50]}"
                      f"  ×{f.adet}  → {p:.2f} puan")

        print("\n0) Faaliyet eklemeyi bitir")
        for k, v in gruplar.items():
            print(f"  {k:>2}) {v}")

        secim = input("\nGrup numarası (veya 0): ").strip()
        if secim == "0":
            break

        if secim not in gruplar:
            print("Geçersiz seçim.")
            input("Devam etmek için Enter...")
            continue

        # O gruba ait kodları göster
        grup_no = int(secim)
        ilgili = {k: v for k, v in EK2_PUANLAR.items()
                  if v["grup"] == grup_no}

        temizle()
        print(f"[{gruplar[secim]}] – Faaliyet Seçimi")
        print("─" * 40)
        kodlar = sorted(ilgili.keys(),
                        key=lambda x: [int(p) if p.isdigit() else p
                                        for p in x.replace(".", " ").split()])
        for k in kodlar:
            v = ilgili[k]
            print(f"  {k:>6}  {v['taban']:>4} puan  {v['ad']}")

        kod = input("\nFaaliyet kodu (örn. 1.1): ").strip()
        if kod not in EK2_PUANLAR:
            print("Geçersiz kod.")
            input("Devam etmek için Enter...")
            continue

        bilgi = EK2_PUANLAR[kod]
        adet = int(sayi_al("  Kaç adet", tam=True, min_val=1, max_val=500))

        # Yazar bilgisi (yayınlar için)
        toplam_yazar = 1
        yazar_sirasi = 1
        sorumlu = False
        q_val = None
        patent_durum = None
        ikinci_d = False
        docent_s = False

        if bilgi["grup"] in {1, 2, 3}:
            if evet_hayir("  Sorumlu yazar veya Senyör yazar mısınız?"):
                sorumlu = True
            else:
                toplam_yazar = int(sayi_al("  Toplam yazar sayısı", tam=True, min_val=1, max_val=50))
                if toplam_yazar > 1:
                    yazar_sirasi = int(sayi_al(f"  Kişinin yazar sırası (1-{toplam_yazar})",
                                               tam=True, min_val=1, max_val=toplam_yazar))

        if bilgi.get("q_carpan"):
            q_val = sec("  Q değeri",
                        {"1": "Q1", "2": "Q2", "3": "Q3", "4": "Q4"})
            q_val = "Q" + q_val

        if kod in ("11.1", "11.7"):
            ps = sec("  Patent durumu",
                     {"1": "Tescilli", "2": "Araştırma raporu almış başvuru",
                      "3": "Başvuru aşaması"})
            patent_durum = {"1": "tescilli", "2": "arastirma_raporu", "3": "basvuru"}[ps]

        if kod in ("17.1", "17.2"):
            ikinci_d = evet_hayir("  İkinci danışman mısınız? (yarı puan)")

        docent_s = evet_hayir("  Bu faaliyet doçentlik sonrası mı?")

        f = Faaliyet(
            kod=kod, adet=adet,
            toplam_yazar=toplam_yazar, yazar_sirasi=yazar_sirasi,
            sorumlu_veya_senyör=sorumlu,
            q_degeri=q_val, patent_durum=patent_durum,
            ikinci_danisман=ikinci_d,
            docent_sonrasi=docent_s
        )
        faaliyetler.append(f)
        p_son, _ = faaliyet_puan_hesapla(f)
        print(f"\n  ✓ Eklendi: {p_son:.2f} puan")
        input("  Devam etmek için Enter...")

    return faaliyetler


def rapor_yazdir(aday: AdayBilgi):
    temizle()
    sonuc = kriter_kontrol(aday)
    puanlar = sonuc["puanlar"]
    kriterler = sonuc["kriterler"]

    kadro_adi = {
        "dr_ilk": "Dr. Öğretim Üyesi (İlk Atanma)",
        "dr_yeniden": f"Dr. Öğretim Üyesi (Yeniden Atanma – {aday.yeniden_sure} Yıl)",
        "docent": "Doçent",
        "profesor": "Profesör",
    }.get(aday.kadro_turu, aday.kadro_turu)

    print("=" * 70)
    print("TNKÜ ÖĞRETİM ÜYELİĞİ ATAMA PUANLAMA RAPORU")
    print("EYS-YNG-129 | 28.03.2025")
    print("=" * 70)
    print(f"Aday         : {aday.ad_soyad}")
    print(f"Alan         : {aday.alan}" + (" (Güzel Sanatlar)" if aday.guzel_sanat else ""))
    print(f"Kadro Türü   : {kadro_adi}")
    print("─" * 70)
    print("PUANLAR")
    print(f"  PUAN-1 (EK-2 grp 1-6 kapsamı)  : {puanlar['puan1']:>8.2f}")
    print(f"  PUAN-2 (EK-2 tümü)              : {puanlar['puan2']:>8.2f}")
    print(f"  TOPLAM                          : {puanlar['toplam']:>8.2f}")
    print("─" * 70)
    print("KRİTER KONTROL SONUÇLARI")
    for k in kriterler:
        isaretler = "  " + k["durum"]
        print(f"{isaretler}  →  {k['kriter']}")
        if k["notlar"]:
            print(f"              ({k['notlar']})")
    print("─" * 70)
    if sonuc["genel_sonuc"]:
        print("  *** GENEL SONUÇ: TÜM KRİTERLER SAĞLANIYOR – BAŞVURU YAPILABİLİR ***")
    else:
        print("  *** GENEL SONUÇ: BAZI KRİTERLER SAĞLANMIYOR – BAŞVURU YAPILAMAZ ***")
    print("=" * 70)
    print("\nFAALİYET DETAYI")
    print(f"{'Kod':>8}  {'Adet':>5}  {'Puan':>8}  {'P1?':>4}  Açıklama")
    print("─" * 70)
    for d in puanlar["detaylar"]:
        p1str = "PUAN-1" if d["puan1_mi"] else "PUAN-2"
        print(f"{d['kod']:>8}  {d['adet']:>5}  {d['puan']:>8.2f}  {p1str}  "
              f"{d['ad'][:40]}")
    print("=" * 70)


def ana_menu():
    print("=" * 70)
    print("TNKÜ ÖĞRETİM ÜYELİĞİ ATAMA PUANLAMA PROGRAMI")
    print("Tekirdağ Namık Kemal Üniversitesi – EYS-YNG-129 (28.03.2025)")
    print("=" * 70)

    aday = AdayBilgi()

    # Temel bilgiler
    aday.ad_soyad = input("\nAday adı soyadı: ").strip() or "Bilinmiyor"

    alan_sec = sec("Akademik alan",
                   {"1": "ALAN-1 (Fen/Sağlık/Mühendislik/Matematik vb.)",
                    "2": "ALAN-2 (Sosyal/İdari/Eğitim/Güzel Sanatlar vb.)"})
    aday.alan = "ALAN-" + alan_sec

    if alan_sec == "2":
        aday.guzel_sanat = evet_hayir("Güzel Sanatlar temel alanı mı?")

    kadro = sec("Kadro türü",
                {"1": "Dr. Öğretim Üyesi – İlk Atanma",
                 "2": "Dr. Öğretim Üyesi – Yeniden Atanma",
                 "3": "Doçent",
                 "4": "Profesör"})

    aday.kadro_turu = {
        "1": "dr_ilk", "2": "dr_yeniden",
        "3": "docent", "4": "profesor"
    }[kadro]

    if aday.kadro_turu == "dr_yeniden":
        sure = sec("Yeniden atama süresi",
                   {"3": "3 yıl", "2": "2 yıl", "1": "1 yıl"})
        aday.yeniden_sure = int(sure)

    # Genel kriterler
    if aday.kadro_turu in ("dr_ilk", "dr_yeniden"):
        aday.doktora_var = evet_hayir("Doktora/Uzmanlık/Yeterlilik unvanı var mı?")
        aday.calisma_alani_yabanci_dil_bolumu = evet_hayir("Çalışma alanı yabancı dil bölümü mü?")
        aday.yabanci_dil_puani = sayi_al("YÖKDİL/YDS puanı", min_val=0, max_val=100)
        if aday.kadro_turu == "dr_ilk":
            aday.ornek_ders_basarili = evet_hayir("Örnek ders jüriden 'Başarılı' aldı mı?")

    elif aday.kadro_turu == "docent":
        aday.uak_docent = evet_hayir("ÜAK Doçent unvanı var mı?")
        aday.sifahi_sinav_basarili = evet_hayir(
            "Sözlü sınav başarılı mı (veya muafiyetli)?")
        aday.calisma_alani_yabanci_dil_bolumu = evet_hayir("Çalışma alanı yabancı dil bölümü mü?")
        aday.yabanci_dil_puani = sayi_al("YÖKDİL/YDS puanı", min_val=0, max_val=100)
        aday.doktora_sonrasi_ders_yari_yil = int(
            sayi_al("Doktora sonrası farklı yarıyıl ders sayısı (≥4 gerekli)",
                    tam=True, min_val=0, max_val=100))

    elif aday.kadro_turu == "profesor":
        aday.uak_docent = evet_hayir("ÜAK Doçent unvanı var mı?")
        aday.sifahi_sinav_basarili = evet_hayir(
            "Sözlü sınav başarılı mı / örnek ders +%20 puan şartı sağlanıyor mu?")
        aday.calisma_alani_yabanci_dil_bolumu = evet_hayir("Çalışma alanı yabancı dil bölümü mü?")
        aday.yabanci_dil_puani = sayi_al("YÖKDİL/YDS puanı", min_val=0, max_val=100)
        aday.doktora_sonrasi_ders_yari_yil = int(
            sayi_al("Doçent sonrası farklı yarıyıl ders sayısı (≥4 gerekli)",
                    tam=True, min_val=0, max_val=100))
        aday.docent_sonrasi_sure_yil = sayi_al(
            "Doçent unvanı sonrası yükseköğretim kurumunda kaç yıl? (≥2.5 gerekli)",
            min_val=0, max_val=50)
        aday.baslica_arastirma_eseri_var = evet_hayir(
            "Başlıca Araştırma Eseri başvuruya eklendi mi (başlıca yazar)?")

    # Faaliyetler
    aday.faaliyetler = faaliyet_ekle_interaktif()

    # Rapor
    rapor_yazdir(aday)

    if evet_hayir("\nRaporu metin dosyasına kaydet?"):
        dosya = f"tnku_rapor_{aday.ad_soyad.replace(' ', '_')}.txt"
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rapor_yazdir(aday)
        with open(dosya, "w", encoding="utf-8") as fp:
            fp.write(buf.getvalue())
        print(f"Rapor kaydedildi: {dosya}")


if __name__ == "__main__":
    try:
        ana_menu()
    except KeyboardInterrupt:
        print("\n\nProgram sonlandırıldı.")
        sys.exit(0)
