"""
"⚡ Yükle ve Ekle" sonrası tek adımda otomatik doldurma.

AVES'ten gelen liste mevcut listeyle birleştirilir (kullanıcının düzelttiği alanlar korunur,
aynı eser iki kez eklenmez); kanıt klasörü varsa ardından sırasıyla:
  1. yayın tarihleri (Crossref / AVES künyesi)
  2. atıflar: yayın klasörlerindeki atiflar\\ alt klasörlerinden kanıtlı sayım (EK-2 5.x)
  3. dersler: son üç yılda ders verilen dönemler (EK-2 17.4)
  4. proje / hakemlik / idari görevlerin kanıt klasörlerine bağlanması
  5. profesörlükte Başlıca Araştırma Eseri önerisi (işaretli eser yoksa)
"""

from __future__ import annotations

from datetime import date

from .kayit import KanitArsivi

# Kullanıcının elle düzelttiği, yeniden yüklemede kaybolmaması gereken alanlar
KORUNAN = ("q_degeri", "baslica_eser", "tezden_uretilmis", "uak_baslica_yazar",
           "sorumlu_veya_senyör", "uak_kalem", "yuksek_lisans", "uluslararasi")


def _korunan_alanlar(f) -> tuple:
    import dataclasses
    ikinci = tuple(a.name for a in dataclasses.fields(f) if a.name.startswith("ikinci_"))
    return KORUNAN + ikinci             # 2. danışman alanının adı motorda tanımlıdır


def _kalici_kimlik(f) -> str:
    k = getattr(f, "kimlik", "") or ""
    return "" if k.startswith(("klasor:", "atif:")) else k


def birlestir(eski: list, yeni: list) -> list:
    """AVES'ten yeniden yüklenen listeyi mevcut listeyle birleştirir.

    - Aynı eser (DOI / başlık kimliği, yoksa AVES kodu + EK-2 kodu) bir kez yer alır.
    - Eski kayıttaki elle düzeltilmiş alanlar (Q değeri, Başlıca Araştırma Eseri …),
      bağlı kanıt klasörü ve yayın tarihi korunur.
    - AVES'ten gelmeyen (elle eklenmiş) faaliyetler olduğu gibi kalır."""
    kimlikle = {k: f for f in eski if (k := _kalici_kimlik(f))}
    kodla = {(f.aves_kod, f.kod): f for f in eski if getattr(f, "aves_kod", "")}
    for f in yeni:
        o = kimlikle.get(_kalici_kimlik(f)) or kodla.get((f.aves_kod, f.kod))
        if o is None:
            continue
        for alan in _korunan_alanlar(o):
            if getattr(o, alan, None) not in (None, False, ""):
                setattr(f, alan, getattr(o, alan))
        if (o.kimlik or "").startswith("klasor:") and not f.kimlik:
            f.kimlik = o.kimlik
        f.yayin_tarihi = f.yayin_tarihi or o.yayin_tarihi
    elle = [f for f in eski if not getattr(f, "aves_kod", "")]
    return list(yeni) + elle


def doldur(faaliyetler: list, arsiv: KanitArsivi, soyad: str, basvuru: date | None,
           unvan: date | None, kadro: str, faaliyet_sinifi, internet: bool = True):
    """Kanıt klasöründen otomatik doldurma. (yeni liste, rapor satırları) döndürür."""
    from . import atif, bagla, oneri, tarih
    import tnku_atama as t
    rapor = []

    bos = [f for f in faaliyetler if getattr(f, "aves_kod", "") and not f.yayin_tarihi]
    if bos:
        try:
            ol = tarih.oneriler(bos, internet=internet)
        except Exception:  # noqa: BLE001 – internet yoksa AVES künyesinden
            ol = tarih.oneriler(bos, internet=False)
        for f, o in ol:
            f.yayin_tarihi = o.tarih
        if ol:
            rapor.append(f"📅 {len(ol)} yayının tarihi dolduruldu")

    atiflar = atif.atiflari_topla(arsiv, soyad)
    if atiflar:
        yeni_atif = atif.faaliyetler(atiflar, basvuru, None, faaliyet_sinifi)
        faaliyetler = [f for f in faaliyetler if not (f.kimlik or "").startswith("atif:")
                       and not (f.kod in ("5.1", "5.9") and not f.kimlik and not f.aves_kod)]
        faaliyetler += yeni_atif
        sayim = sum(f.adet for f in yeni_atif)
        rapor.append(f"🔗 {sayim} kanıtlı atıf {len(yeni_atif)} satır olarak eklendi "
                     f"(öz atıflar ve endeksi belirsizler hariç)")

    ders = oneri.ders_onerisi(arsiv, None, unvan)
    if ders.son_uc_yil:
        faaliyetler = [f for f in faaliyetler if not (f.kod == "17.4" and not f.aves_kod)]
        klasor = next((d for d in arsiv.diger_klasorler if d.name.upper().startswith("DERS")), None)
        faaliyetler.append(faaliyet_sinifi("17.4", adet=len(ders.son_uc_yil), docent_sonrasi=True,
                                           kimlik=arsiv.klasor_kimligi(klasor) if klasor else ""))
        rapor.append(f"🎓 Son üç yılda {len(ders.son_uc_yil)} ders dönemi (EK-2 17.4)")

    if (n := bagla.uygula(arsiv, bagla.oneriler(arsiv, faaliyetler))):
        rapor.append(f"📁 {n} proje / hakemlik / idari görev kanıt klasörüne bağlandı")

    if kadro == "profesor" and unvan and not any(f.baslica_eser for f in faaliyetler):
        aday = [f for f in faaliyetler if f.kod == "1.1" and f.yayin_tarihi
                and f.yayin_tarihi > unvan and (f.toplam_yazar <= 1 or f.yazar_sirasi == 1)]
        if aday:
            en = max(aday, key=lambda f: t.faaliyet_puan_hesapla(f)[0])
            en.baslica_eser = True
            rapor.append(f"★ Başlıca Araştırma Eseri önerildi: {en.aves_kod} (değiştirmek için "
                         "faaliyet satırını açın)")
    return faaliyetler, rapor
