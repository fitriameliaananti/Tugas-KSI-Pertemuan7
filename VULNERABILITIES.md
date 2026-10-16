# Kerentanan yang Dibuat Secara Sengaja

Proyek ini adalah aplikasi latihan. Tiga kerentanan di bawah ini ditanam dengan sengaja.

| # | Kerentanan | Lokasi | Penyebab |
|---|-----------|--------|----------|
| 1 | **IDOR / kontrol akses lemah** | `GET /nilai/<id>` (`nilai_detail` di `app.py`) | Query hanya memakai `grade_id`, tanpa memeriksa apakah nilai itu milik pengguna yang login. |
| 2 | **SQL injection** | `GET /cari?q=` (`cari` di `app.py`) | Input pengguna digabung langsung ke string SQL dengan f-string. |
| 3 | **Stored XSS** | `/diskusi/<id>` (`templates/diskusi.html`) | Isi pesan dirender dengan filter `|safe`, sehingga HTML/JS tersimpan dan dieksekusi di browser pembaca. |

## Perbaikan (untuk laporan)
1. IDOR: tambahkan `AND g.student_id = ?` untuk mahasiswa (dosen: cek mata kuliah yang diampu).
2. SQLi: gunakan query berparameter `... LIKE ?` dengan `('%'+q+'%',)`.
3. XSS: hapus `|safe` supaya Jinja melakukan auto-escape; tambahkan header CSP.

## Catatan
Aplikasi ini tidak memiliki proteksi CSRF dan tidak membatasi percobaan login. Keduanya bukan bagian
dari kerentanan yang dipilih untuk dilaporkan.
