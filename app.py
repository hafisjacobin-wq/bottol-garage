from flask import Flask, request, redirect, render_template_string
import os, sqlite3
from datetime import date, timedelta

app = Flask(__name__)
DB = "arapp.db"

def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

def init():
    con = db()
    con.execute("""CREATE TABLE IF NOT EXISTS motor (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer TEXT, phone TEXT, plat TEXT, jenis TEXT,
        masalah TEXT, harga REAL, status TEXT DEFAULT 'Masuk',
        pomen TEXT, bayar TEXT DEFAULT 'Belum'
    )""")
    con.execute("""CREATE TABLE IF NOT EXISTS kedai (
        id INTEGER PRIMARY KEY,
        nama_kedai TEXT, phone TEXT,
        tarikh_habis TEXT, status_bayar TEXT DEFAULT 'Trial'
    )""")
    # Auto buat 1 kedai trial 7 hari kalau belum ada
    c = con.execute("SELECT count(*) as c FROM kedai").fetchone()['c']
    if c == 0:
        habis = (date.today() + timedelta(days=7)).isoformat()
        con.execute("INSERT INTO kedai (nama_kedai, phone, tarikh_habis) VALUES (?,?,?)", ("ARAPP SYSTEM", "60123456789", habis))
    con.commit(); con.close()
init()

def check_subscribe():
    con = db()
    k = con.execute("SELECT * FROM kedai LIMIT 1").fetchone()
    con.close()
    if not k:
        return False
    # Kalau tarikh hari ni dah lepas tarikh habis = kena bayar
    if str(date.today()) > str(k['tarikh_habis']):
        return True # True = dah expired
    return False

# ================= PAGE SUBSCRIBE =================
SUBSCRIBE_HTML = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<title>ARAPP SYSTEM Garage - Subscribe</title>
<style>body{font-family:sans-serif;background:#111;padding:16px;margin:0;color:#111}
.box{background:white;padding:22px;border-radius:16px;text-align:center;max-width:400px;margin:20px auto}
.btn{display:block;background:#111;color:white;padding:16px;border-radius:10px;text-decoration:none;font-weight:bold;font-size:18px;margin-top:12px}
.btn2{display:block;background:#25D366;color:white;padding:14px;border-radius:10px;text-decoration:none;font-weight:bold;margin-top:10px}
</style></head><body>
<div class="box">
<h1>🏍️ ARAPP SYSTEM Garage</h1>
<h2 style="color:red">Trial Dah Habis </h2>
<p>Nak sambung guna untuk kedai lagi?</p>
<h1 style="font-size:42px">RM49 <span style="font-size:16px">/ Bulan</span></h1>
<p style="text-align:left">✅ Unlimited Motor Masuk<br>✅ Unlimited Pomen<br>✅ Approval Tokey<br>✅ WhatsApp Customer Auto<br>✅ Rekod Duit Harian</p>
<a class="btn" href="https://toyyibpay.com/Langanan-Bulanan">💳 BAYAR RM49 SEKARANG</a>
<a class="btn2" href="https://wa.me/60123456789?text=Salam%20saya%20nak%20subscribe%20Arapp%20Garage%20RM49">📱 WHATSAPP ADMIN - DAH BAYAR</a>
<p style="font-size:12px;color:#888;margin-top:15px">Lepas bayar, WhatsApp resit kat admin, admin akan aktifkan dalam 5 minit.</p>
</div></body></html>
"""

@app.route("/subscribe")
def subscribe():
    return SUBSCRIBE_HTML

# Link untuk KAU (owner app) aktifkan kedai orang lepas dia bayar
# Contoh kau buka: /aktifkan?hari=30
@app.route("/aktifkan")
def aktifkan():
    hari = int(request.args.get("hari", 30))
    baru = (date.today() + timedelta(days=hari)).isoformat()
    con = db()
    con.execute("UPDATE kedai SET tarikh_habis=?, status_bayar='Aktif' WHERE id=1", (baru,))
    con.commit(); con.close()
    return f"Siap! Kedai aktif sampai {baru}. <a href='/'>Balik ke App</a>"

# ================= PAGE UTAMA =================
HTML = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<title>ARAPPSYSTEM Garage</title>
<style>
body{font-family:sans-serif;background:#f4f4f4;padding:12px;margin:0}
h1{text-align:center}
.card{background:white;padding:14px;border-radius:12px;margin-bottom:10px;box-shadow:0 2px 5px #ddd}
input,select,textarea{width:100%;padding:10px;margin:5px 0;border:1px solid #ccc;border-radius:8px;box-sizing:border-box}
button{width:100%;padding:12px;border:none;border-radius:8px;font-weight:bold;font-size:16px;margin-top:5px}
.btn-add{background:#111;color:white}
.btn-kerja{background:#ff9800;color:white}
.btn-siap{background:#4caf50;color:white}
.btn-approve{background:#2196f3;color:white}
.btn-bayar{background:#111;color:white}
.badge{padding:4px 8px;border-radius:20px;font-size:12px;color:white}
.top{display:flex;gap:8px;text-align:center}
.top div{flex:1;background:white;padding:10px;border-radius:10px}
</style></head><body>
<h1>🏍️ ArappSystem Garage</h1>
<p style="text-align:center;font-size:12px">Aktif sampai: {{tarikh_habis}} | <a href="/subscribe">Subscribe</a></p>

<div class="top">
<div><b>{{total}}</b><br>Motor Hari Ni</div>
<div><b>{{siap}}</b><br>Dah Siap</div>
<div><b>RM{{duit}}</b><br>Duit \Masuk</div>
</div>

<div class="card" style="border:2px solid red">
<h3>🔴 PERLU APPROVAL BOSS</h3>
{% for r in need_approval %}
<p><b>{{r['jenis']}} {{r['plat']}}</b> - {{r['masalah']}}<br>Harga Pomen: <b>RM{{r['harga']}}</b> - {{r['pomen']}}</p>
<form method="post" action="/approve/{{r['id']}}">
<input name="harga_baru" type="number" placeholder="Tukar harga jika perlu">
<button class="btn-approve">✅ APPROVE & WHATSAPP CUSTOMER</button>
</form><hr>
{% else %}<p>Tiada approval. Semua clear ✅</p>{% endfor %}
</div>

<div class="card">
<h3>➕ Motor Baru Masuk</h3>
<form method="post" action="/add">
<input name="customer" placeholder="Nama Customer" required>
<input name="phone" placeholder="No WhatsApp cth 60123456789" required>
<input name="plat" placeholder="Plat cth WXY1234" required>
<input name="jenis" placeholder="Jenis Motor cth Y15" required>
<textarea name="masalah" placeholder="Apa rosak?"></textarea>
<button class="btn-add">MASUKKAN MOTOR</button>
</form></div>

{% for r in rows %}
<div class="card">
<a href="/edit/{{r['id']}}" style="background:#ff9800;color:white;padding:8px 10px;border-radius:8px;text-decoration:none;fonpx;border-radius:8px;text-decoration:none;font-size:13px;font-weight:bold;display:block;BETULKAN</a><a href="/edit/{{r['id']}}" style="display:block;text-align:left;margin-top:0;margin-left:0;padding:10px;"><✏️ EDIT - BETULKAN</a>
<b>{{r['jenis']}} - {{r['plat']}}</b><br>
👤 {{r['customer']}} - {{r['phone']}}<br>
🔧 {{r['masalah']}}<br>
💰 RM{{r['harga'] or 0}} | Pomen: {{r['pomen'] or '-'}} | Bayar: {{r['bayar']}}
<a href="https://wa.me/{{r['phone']}}?text=Salam%20{{r['customer']}}%2C%20motor%20{{r['jenis']}}%20{{r['plat']}}%20kau%20DAH%20SIAP!%20Total%20RM{{r['harga']}}%20-%20Arapp%20Garage" target="_blank" style="display:block;background:#25D366;color:white;text-align:center;padding:12px;border-radius:8px;text-decoration:none;font-weight:bold;margin-top:8px;">💬 WHATSAPP CUSTOMER</a>
{% if r['status']=='Masuk' %}
<form method="post" action="/kerja/{{r['id']}}"><input name="pomen" placeholder="Nama Pomen" required><button class="btn-kerja">🔧 MULA KERJA</button></form>
{% elif r['status']=='Tengah Buat' %}
<form method="post" action="/siap/{{r['id']}}"><input name="harga" type="number" placeholder="Harga Akhir RM" required><button class="btn-siap">🏁 DAH SIAP - MINTA APPROVAL</button></form>
{% elif r['status']=='Dah Siap' %}
<form method="post" action="/bayar/{{r['id']}}"><button class="btn-bayar">💵 CUSTOMER DAH BAYAR</button></form>
{% endif %}
</div>
{% endfor %}
</body></html>
"""

@app.route("/")
def index():
    if check_subscribe():
        return redirect("/subscribe")
    con=db(); rows=con.execute("SELECT * FROM motor ORDER BY id DESC").fetchall()
    need=con.execute("SELECT * FROM motor WHERE status='Tunggu Approval'").fetchall()
    kedai=con.execute("SELECT * FROM kedai LIMIT 1").fetchone()
    total=len(rows); siap=len([r for r in rows if r['status']=='Dah Siap'])
    duit=sum([r['harga'] or 0 for r in rows if r['bayar']=='Sudah'])
    con.close()
    return render_template_string(HTML, rows=rows, need_approval=need, total=total, siap=siap, duit=duit, tarikh_habis=kedai['tarikh_habis'] if kedai else '-')

@app.route("/add", methods=["POST"])
def add():
    con=db(); con.execute("INSERT INTO motor (customer,phone,plat,jenis,masalah) VALUES (?,?,?,?,?)",(request.form['customer'],request.form['phone'],request.form['plat'],request.form['jenis'],request.form['masalah'])); con.commit(); con.close(); return redirect("/")

@app.route("/kerja/<int:id>", methods=["POST"])
def kerja(id):
    con=db(); con.execute("UPDATE motor SET status='Tengah Buat', pomen=? WHERE id=?",(request.form['pomen'],id)); con.commit(); con.close(); return redirect("/")

@app.route("/siap/<int:id>", methods=["POST"])
def siap(id):
    con=db(); con.execute("UPDATE motor SET status='Tunggu Approval', harga=? WHERE id=?",(request.form['harga'],id)); con.commit(); con.close(); return redirect("/")

@app.route("/approve/<int:id>", methods=["POST"])
def approve(id):
    harga_baru=request.form.get('harga_baru')
    con=db(); r=con.execute("SELECT * FROM motor WHERE id=?",(id,)).fetchone()
    if harga_baru: con.execute("UPDATE motor SET harga=?, status='Dah Siap' WHERE id=?",(harga_baru,id))
    else: con.execute("UPDATE motor SET status='Dah Siap' WHERE id=?",(id,))
    con.commit(); con.close()
    harga_final = harga_baru if harga_baru else r['harga']
    print(f"WHATSAPP TO {r['phone']}: Bos, motor {r['jenis']} {r['plat']} DAH SIAP! Total RM{harga_final} - Arapp Garage")
    return redirect("/")

@app.route("/bayar/<int:id>", methods=["POST"])
def bayar(id):
    con=db(); con.execute("UPDATE motor SET bayar='Sudah' WHERE id=?",(id,)); con.commit(); con.close(); return redirect("/")
@app.route("/edit/<int:id>")
def edit(id):
    con=db(); r=con.execute("SELECT * FROM motor WHERE id=?",(id,)).fetchone(); con.close()
    return f"""
    <div style="font-family:sans-serif;max-width:500px;margin:20px auto;padding:20px">
    <h2>Edit Motor - {r['customer']}</h2>
    <form action="/update/{id}" method="POST" style="display:flex;flex-direction:column;gap:10px">
    Nama: <input name="customer" value="{r['customer']}" required>
    No Phone: <input name="phone" value="{r['phone']}" required>
    No Plat: <input name="plat" value="{r['plat']}" required>
    Motor: <input name="jenis" value="{r['jenis']}" required>
    Kerja: <input name="masalah" value="{r['masalah']}" required>
    Harga RM: <input name="harga" type="number" value="{r['harga'] or 0}" required>
    Pomen: <input name="pomen" value="{r['pomen'] or ''}">
    <button style="background:#ff9800;color:white;padding:12px;border:none;border-radius:8px;font-weight:bold">SIMPAN BETULKAN</button>
    <a href="/" style="text-align:center">Batal</a>
    </form></div>
    """

@app.route("/update/<int:id>", methods=["POST"])
def update(id):
    con=db(); con.execute("UPDATE motor SET customer=?, phone=?, plat=?, jenis=?, masalah=?, harga=?, pomen=? WHERE id=?",
    (request.form.get('customer'), request.form.get('phone'), request.form.get('plat'), request.form.get('jenis'), request.form.get('masalah'), request.form.get('harga'), request.form.get('pomen'), id))
    con.commit(); con.close()
    return redirect("/")
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)



