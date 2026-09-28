"""
Komut satırı:

  python -m kanit durum        [KÖK]
  python -m kanit kimlik-yaz   [KÖK]                  eski klasörlere kayit.json yazar
  python -m kanit ozet         [KÖK]                  kunye.txt listeleri + Excel özeti
  python -m kanit arsivden-ekle [KÖK] --kaynak AD=YOL [--kaynak AD=YOL ...]
                               [--onceki YOL ...] [--kopyala]

KÖK verilmezse yerel ayardaki kanıt klasörü kullanılır.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

from . import ayar
from .kayit import KanitArsivi


def main(argv=None):
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    p = argparse.ArgumentParser(prog="python -m kanit", description="Kanıt arşivi araçları")
    alt = p.add_subparsers(dest="komut", required=True)
    for ad in ("durum", "kimlik-yaz", "ozet"):
        a = alt.add_parser(ad)
        a.add_argument("kok", nargs="?")
    a = alt.add_parser("arsivden-ekle")
    a.add_argument("kok", nargs="?")
    a.add_argument("--kaynak", action="append", default=[], metavar="AD=YOL")
    a.add_argument("--onceki", action="append", default=[], metavar="YOL")
    a.add_argument("--kopyala", action="store_true")
    ns = p.parse_args(argv)

    kok = ns.kok or ayar.kanit_koku()
    if not kok or not Path(kok).is_dir():
        p.error(f"kanıt klasörü bulunamadı: {kok!r}")
    arsiv = KanitArsivi(kok)

    if ns.komut == "durum":
        from .kontrol import durum
        eksik = Counter()
        for k in arsiv.kayitlar:
            for e in durum(k).eksik_aciklamalari():
                eksik[e] += 1
        print(f"{arsiv.kok}: {len(arsiv.kayitlar)} yayın klasörü, "
              f"{len(arsiv.diger_klasorler)} diğer klasör")
        print("Tam metni olmayan:", [k.aves_kod for k in arsiv.kayitlar if not k.tam_metin])
        for e, n in eksik.most_common():
            print(f"  {n:3} klasörde eksik: {e}")
    elif ns.komut == "kimlik-yaz":
        from .klasor import kimlikleri_yaz
        print("kayit.json yazılan klasör:", kimlikleri_yaz(arsiv))
    elif ns.komut == "ozet":
        from .ozet import ozet_yaz
        print("Özet yazıldı:", len(ozet_yaz(arsiv)), "yayın")
    elif ns.komut == "arsivden-ekle":
        from .arsivden import kurallari_oku, plan_olustur, uygula
        kaynaklar = dict(k.split("=", 1) for k in ns.kaynak)
        if not kaynaklar:
            p.error("en az bir --kaynak AD=YOL gerekli")
        # Daha önce işlenmiş kaynaklar: ayar dosyasından (--onceki ile genişletilebilir)
        onceki = [y for y in ns.onceki + kurallari_oku(arsiv.kok).get("islenmis_kaynaklar", [])
                  if Path(y).is_dir() and y not in kaynaklar.values()]
        plan = plan_olustur(arsiv, {a: Path(y) for a, y in kaynaklar.items()})
        sayac = uygula(arsiv, plan, onceki, kopyala=ns.kopyala,
                       kayit_csv=arsiv.kok / "_arsiv_eslestirme_son.csv")
        print(("Kopyalandı: " if ns.kopyala else "Plan (kopyalama yok): ") + str(dict(sayac)))
        print("Ayrıntı:", arsiv.kok / "_arsiv_eslestirme_son.csv")


if __name__ == "__main__":
    main()
