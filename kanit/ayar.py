"""Yerel ayar: kanıt kök klasörünün yolu (kullanıcının ev dizininde, repoda değil)."""

from __future__ import annotations

import json
import os
from pathlib import Path

AYAR_DOSYASI = Path.home() / ".tnku_atama.json"
VARSAYILAN_KOK = Path(r"E:\Kanit_Dosyalari")


def oku() -> dict:
    try:
        return json.loads(AYAR_DOSYASI.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def kanit_koku() -> str:
    """Ayarlanmış kök; yoksa varsayılan (varsa). Bulutta boş döner."""
    kok = os.environ.get("TNKU_KANIT_KOKU") or oku().get("kanit_koku", "")
    if not kok and VARSAYILAN_KOK.is_dir():
        kok = str(VARSAYILAN_KOK)
    return kok


def atif_haric() -> tuple[str, ...]:
    """Atıf sayımında hariç tutulan EK-2 kodları (örn. ("5.2",): ESCI atıfları sayılmaz)."""
    return tuple(oku().get("atif_haric_endeksler", ()))


def atif_haric_kaydet(kodlar) -> None:
    ayar = oku()
    ayar["atif_haric_endeksler"] = sorted(set(kodlar))
    try:
        AYAR_DOSYASI.write_text(json.dumps(ayar, ensure_ascii=False, indent=1), encoding="utf-8")
    except OSError:
        pass


def kanit_koku_kaydet(kok: str) -> None:
    ayar = oku()
    ayar["kanit_koku"] = kok
    try:
        AYAR_DOSYASI.write_text(json.dumps(ayar, ensure_ascii=False, indent=1), encoding="utf-8")
    except OSError:
        pass
