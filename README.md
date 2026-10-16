# Portal Kampus Fiktif (Latihan Keamanan Aplikasi Web)

Portal kampus fiktif. Seluruh akun dan data bersifat **sintetis**.
Aplikasi ini **sengaja rentan** (lihat [VULNERABILITIES.md](VULNERABILITIES.md)); jangan dipakai untuk data nyata.

## Fitur
- **Mahasiswa**: masuk, melihat nilai, mengunggah tugas (pdf/txt/docx/zip, maks 5 MB), berdiskusi per mata kuliah.
- **Dosen**: memberi/mengubah nilai, melihat tugas yang masuk, berdiskusi.
- **Admin**: membuat akun, reset sandi, aktif/nonaktifkan, hapus akun.

## Menjalankan lokal
```bash
pip install -r requirements.txt
python app.py        # http://127.0.0.1:5000
```
Database `campus.db` dibuat otomatis saat pertama jalan (hapus file untuk reset data).

## Deploy (Docker)
```bash
docker build -t portal-kampus . && docker run -p 8000:8000 portal-kampus
```
Bisa juga di Render / Railway / Fly.io memakai Dockerfile ini.

## Akun sintetis
| Peran | Username | Sandi |
|-------|----------|-------|
| Admin | admin.kampus | Adm1n#Fiktif26 |
| Dosen | laras.dosen | Dosen#Laras26 |
| Dosen | bayu.dosen | Dosen#Bayu26 |
| Mahasiswa | mhs.raka | Mhs#Raka26 |
| Mahasiswa | mhs.nadia | Mhs#Nadia26 |
| Mahasiswa | mhs.dimas | Mhs#Dimas26 |
| Mahasiswa | mhs.salsa | Mhs#Salsa26 |

> Ubah nama, NIM, username, dan sandi di fungsi `init_db()` pada `app.py` supaya datamu unik (tidak sama dengan peserta lain).
