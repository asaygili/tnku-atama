"""
Kanıt arşivi: faaliyetlerin kanıt klasörleriyle bütünleştirilmesi (yalnızca yerelde).

Modüller:
  kayit        klasörlerin okunması, faaliyet ↔ klasör eşleştirmesi
  aday_dosyasi aday bilgileri ve faaliyetlerin aday.json'a kaydı
  klasor       yeni klasör açma, AVES numaraları kayınca yeniden adlandırma
  kontrol      yönergenin istediği kanıtların bulunup bulunmadığı
  ozet         kunye.txt kontrol listeleri ve Excel özeti
  arsivden     eski arşiv klasörlerinden eşleyip kopyalama
  bildiri      bildiri kitabından bildiri sayfalarını kesme
  indir        açık erişimli tam metinleri indirme
  ayar         kanıt kök klasörünün yerel ayarı

Komut satırı: python -m kanit --help
"""

from .kayit import KanitArsivi, KanitKaydi  # noqa: F401
