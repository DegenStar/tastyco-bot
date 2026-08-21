# Tasty

Kumpulan berkas proyek **Tasty** yang berasal dari arsip `tasty.zip`.

## Isi repositori

| Berkas | Keterangan |
|---|---|
| `bot.py` | Skrip utama proyek. |
| `requirements.txt` | Daftar dependensi Python. |
| `accounts.txt` | Data akun yang disertakan dalam arsip sumber. |
| `captcha_key.txt` | Konfigurasi atau kunci CAPTCHA yang disertakan dalam arsip sumber. |
| `proxy.txt` | Daftar konfigurasi proxy yang disertakan dalam arsip sumber. |
| `sctg.txt` | Data teks pendukung proyek. |
| `useragent.txt` | Daftar user-agent yang disertakan dalam arsip sumber. |

## Instalasi dependensi

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Menjalankan proyek

```bash
python bot.py
```

> **Catatan keamanan:** Repositori ini dibuat privat sesuai permintaan. Beberapa berkas yang ikut diunggah dapat berisi kredensial, token, akun, proxy, atau data konfigurasi sensitif. Jangan mengubah visibilitas repositori menjadi publik, dan segera rotasi kredensial apabila akses repositori pernah terbuka atau dibagikan kepada pihak lain.

## Sumber

Berkas proyek ini diunggah dari arsip `tasty.zip` yang diberikan pengguna.
