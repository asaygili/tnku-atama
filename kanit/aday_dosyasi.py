"""Aday bilgilerinin ve faaliyet listesinin kalıcı kaydı (aday.json)."""

from __future__ import annotations

import dataclasses
import json
from datetime import date, datetime
from pathlib import Path

import tnku_atama as t

ADAY_DOSYASI = "aday.json"
SURUM = 1


def _yaziya(v):
    if isinstance(v, date):
        return {"__tarih__": v.isoformat()}
    return v


def _tarihe(v):
    if isinstance(v, dict) and "__tarih__" in v:
        return date.fromisoformat(v["__tarih__"])
    return v


def _faaliyet_sozluk(f: t.Faaliyet) -> dict:
    d = {k: _yaziya(v) for k, v in dataclasses.asdict(f).items()}
    if kunye := getattr(f, "_kunye", ""):
        d["_kunye"] = kunye
    return d


def _faaliyet_olustur(d: dict) -> t.Faaliyet:
    alanlar = {f.name for f in dataclasses.fields(t.Faaliyet)}
    f = t.Faaliyet(**{k: _tarihe(v) for k, v in d.items() if k in alanlar})
    if d.get("_kunye"):
        f._kunye = d["_kunye"]
    return f


def kaydet(yol: Path, aday: t.AdayBilgi, ek: dict | None = None) -> Path:
    """Aday bilgilerini ve faaliyetleri JSON olarak kaydeder.
    Var olan dosya önce aday.json.bak olarak saklanır."""
    yol = Path(yol)
    if yol.is_dir():
        yol = yol / ADAY_DOSYASI
    aday_d = {k: _yaziya(v) for k, v in dataclasses.asdict(aday).items() if k != "faaliyetler"}
    veri = {"surum": SURUM, "kaydedilme": datetime.now().isoformat(timespec="seconds"),
            "aday": aday_d, "faaliyetler": [_faaliyet_sozluk(f) for f in aday.faaliyetler],
            "ek": ek or {}}
    if yol.exists():
        yol.replace(yol.with_suffix(".json.bak"))
    yol.write_text(json.dumps(veri, ensure_ascii=False, indent=1), encoding="utf-8")
    return yol


def yukle(yol: Path) -> tuple[t.AdayBilgi, dict]:
    """(AdayBilgi, ek) döndürür. Bilinmeyen alanlar yok sayılır (ileri/geri uyum)."""
    yol = Path(yol)
    if yol.is_dir():
        yol = yol / ADAY_DOSYASI
    veri = json.loads(yol.read_text(encoding="utf-8"))
    alanlar = {f.name for f in dataclasses.fields(t.AdayBilgi)} - {"faaliyetler"}
    aday = t.AdayBilgi(**{k: _tarihe(v) for k, v in veri.get("aday", {}).items() if k in alanlar})
    aday.faaliyetler = [_faaliyet_olustur(d) for d in veri.get("faaliyetler", [])]
    return aday, veri.get("ek", {})
