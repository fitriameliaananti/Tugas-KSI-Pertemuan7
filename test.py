import os, io
os.environ["SECRET_KEY"]="t"
import app as A
c=A.app.test_client()
def login(u,p):
    c.get("/logout"); return c.post("/login",data={"username":u,"password":p},follow_redirects=True)
assert b"Halo" in login("mhs.raka","Mhs#Raka26").data
print("nilai:", b"Detail" in c.get("/nilai").data)
print("IDOR  :", c.get("/nilai/1").status_code, "(nilai milik user lain)")
print("SQLi  :", c.get("/cari?q=zzz' UNION SELECT id,username,role FROM users--").data.count(b"mhs.")>0)
c.post("/diskusi/2",data={"body":"<script>alert(1)</script>"})
print("XSS   :", b"<script>alert(1)</script>" in c.get("/diskusi/2").data)
r=c.post("/tugas",data={"assignment_id":"2","berkas":(io.BytesIO(b"x"),"a.pdf")},content_type="multipart/form-data",follow_redirects=True)
print("upload:", b"a.pdf" in r.data)
r=c.post("/tugas",data={"assignment_id":"2","berkas":(io.BytesIO(b"x"),"a.py")},content_type="multipart/form-data",follow_redirects=True)
print("tolak .py:", b"tidak diizinkan" in r.data)
login("laras.dosen","Dosen#Laras26"); print("dosen:", c.get("/dosen/nilai/1").status_code, c.post("/dosen/nilai/1",data={"score_4":"88"}).status_code)
login("admin.kampus","Adm1n#Fiktif26"); print("admin:", c.get("/admin").status_code)
login("mhs.raka","Mhs#Raka26"); print("mhs->admin:", c.get("/admin").status_code)
