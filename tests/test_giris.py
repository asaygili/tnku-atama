"""Giriş şifresi: Secrets'ta şifre varsa uygulama şifresiz açılmaz."""

import hashlib
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from streamlit.testing.v1 import AppTest  # noqa: E402

KOK = os.path.join(os.path.dirname(__file__), "..")


def uygulama(**secrets) -> AppTest:
    at = AppTest.from_file(os.path.join(KOK, "tnku_streamlit.py"), default_timeout=120)
    for k, v in secrets.items():
        at.secrets[k] = v
    return at.run()


class Giris(unittest.TestCase):
    def test_sifre_yoksa_dogrudan_acilir(self):
        at = uygulama()
        self.assertFalse(at.exception)
        self.assertTrue(any(b.label.startswith("⚡") for b in at.button))

    def test_sifre_sorulur_ve_dogrusu_acar(self):
        at = uygulama(giris_sifresi="gizli123")
        self.assertEqual([t.label for t in at.text_input], ["Giriş şifresi"])
        at.text_input[0].set_value("yanlis")
        at.button[0].click().run()
        self.assertTrue(any("hatalı" in e.value for e in at.error))
        self.assertEqual(len(at.text_input), 1)               # hâlâ giriş ekranında
        at.text_input[0].set_value("gizli123")
        at.button[0].click().run()
        self.assertFalse(at.exception)
        self.assertTrue(any(b.label.startswith("⚡") for b in at.button))

    def test_sha256_ozeti(self):
        at = uygulama(giris_sifresi_sha256=hashlib.sha256(b"abc").hexdigest())
        at.text_input[0].set_value("abc")
        at.button[0].click().run()
        self.assertTrue(any(b.label.startswith("⚡") for b in at.button))


if __name__ == "__main__":
    unittest.main()
