import os
from functools import wraps
from flask import Flask, render_template_string, request, redirect, url_for, session
from datetime import date, timedelta
import psycopg2
import psycopg2.extras

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "arapp-secret")

# --- SUPABASE CONFIG ---
# Project kau
SUPABASE_URL = "https://xiqgjuuphoveldhwbmhr.supabase.co"
SUPABASE_PUBLISHABLE_KEY = "sb_publishable_0FUvZd7_nHu87aI8J7wVOA_8Fl5IMps"

# Database URL dari Supabase > Project Settings > Database > Connection string
DATABASE_URL = os.environ.get("DATABASE_URL")
PASSWORD_KEDAI = os.environ.get("PASSWORD_KEDAI", "1234")  # Tukar password login kedai kat sini / Env

# --- Postgres wrapper ---
class CursorWrapper:
    def __init__(self, cur):
        self.cur = cur
    def fetchone(self):
        return self.cur.fetchone()
    def fetchall(self):
        return self.cur.fetchall()
    def __iter__(self):
        return iter(self.cur.fetchall())

class PGConn:
    def __init__(self):
        if not DATABASE_URL:
            raise Exception("DATABASE_URL tak set! Set kat Render / Railway / Env")
        self.conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
        self.conn.autocommit = False
    def execute(self, sql, params=()):
        sql2 = sql.replace("?", "%s")
        cur = self.conn.cursor()
        cur.execute(sql2, params)
        return CursorWrapper(cur)
    def commit(self):
        self.conn.commit()
    def close(self):
        try:
            self.conn.close()
        except:
            pass

def db():
    return PGConn()

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated

def login_required...
    ...
    return decorated

def init():
    con = db()
    con.execute("""CREATE TABLE IF NOT EXISTS motor (
        id SERIAL PRIMARY KEY,
        customer TEXT, phone TEXT, plat TEXT, jenis TEXT,
        masalah TEXT, harga REAL, status TEXT DEFAULT 'Masuk',
        pomen TEXT, bayar TEXT DEFAULT 'Belum'
    )""")
    con.execute("""CREATE TABLE IF NOT EXISTS sejarah (
        id SERIAL PRIMARY KEY,
        tarikh_tutup TEXT,
        customer TEXT, phone TEXT, plat TEXT, jenis TEXT,
        masalah TEXT, harga REAL, pomen TEXT, bayar TEXT
    )""")
    con.execute("""CREATE TABLE IF NOT EXISTS kedai (
        id SERIAL PRIMARY KEY,
        nama_kedai TEXT, phone TEXT,
        tarikh_habis TEXT, status_bayar TEXT DEFAULT 'Trial'
    )""")
    for tbl in ["motor", "sejarah", "kedai"]:
        con.execute(f"CREATE SEQUENCE IF NOT EXISTS {tbl}_id_seq")
        con.execute(f"ALTER TABLE {tbl} ALTER COLUMN id SET DEFAULT nextval('{tbl}_id_seq')")
        con.execute(f"SELECT setval('{tbl}_id_seq', COALESCE((SELECT MAX(id) FROM {tbl}), 1))")
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
    if str(date.today()) > str(k['tarikh_habis']):
        return True
    return False

# ================= LOGIN =================
LOGIN_HTML = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Login - ARAPP DEMO</title>
<style>body{font-family:sans-serif;background:#111;padding:16px;margin:0}
.box{background:white;padding:24px;border-radius:16px;text-align:center;max-width:380px;margin:40px auto}
input{width:100%;padding:14px;margin:8px 0;border:1px solid #ccc;border-radius:10px;box-sizing:border-box;font-size:16px}
button{width:100%;padding:14px;background:#111;color:white;border:none;border-radius:10px;font-weight:bold;font-size:16px}
.err{color:red;font-weight:bold}
</style></head><body>
<div class="box">
<h1>🏍️ ARAPP DEMO</h1>
<p>Staff sahaja. Sila login.</p>
{% if error %}<p class="err">{{error}}</p>{% endif %}
<form method="post">
<input type="password" name="password" placeholder="Masukkan Password Kedai" required>
<button>🔓 MASUK</button>
</form>
<p style="font-size:12px;color:#888">Lupa password? WhatsApp Admin.</p>
</div></body></html>
"""

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        if request.form.get("password") == PASSWORD_KEDAI:
            session["logged_in"] = True
            return redirect("/")
        else:
            error = "Password salah! Cuba lagi."
    return render_template_string(LOGIN_HTML, error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ================= SUBSCRIBE =================
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
<h2 style="color:red">Trial Dah Habis</h2>
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

@app.route("/aktifkan")
def aktifkan():
    hari = int(request.args.get("hari", 30))
    baru = (date.today() + timedelta(days=hari)).isoformat()
    con = db()
    con.execute("UPDATE kedai SET tarikh_habis=?, status_bayar='Aktif' WHERE id=1", (baru,))
    con.commit(); con.close()
    return f"Siap! Kedai aktif sampai {baru}. <a href='/'>Balik ke App</a>"

@app.route("/delete_all")
@login_required
def delete_all():
    con = db()
    try:
        con.execute("INSERT INTO sejarah (tarikh_tutup, customer, phone, plat, jenis, masalah, harga, pomen, bayar) SELECT date('now'), customer, phone, plat, jenis, masalah, harga, pomen, bayar FROM motor")
    except Exception as e:
        print("arkib gagal:", e)
    con.execute("DELETE FROM motor")
    con.commit(); con.close()
    return "Siap! Semua job dah pindah ke Arkib. <a href='/'>Balik ke App</a>"

@app.route("/delete_arkib/<int:id>")
@login_required
def delete_arkib(id):
    con = db()
    con.execute("DELETE FROM sejarah WHERE id=?", (id,))
    con.commit(); con.close()
    return redirect("/arkib")

@app.route("/delete_arkib_all")
@login_required
def delete_arkib_all():
    con = db()
    con.execute("DELETE FROM sejarah")
    con.commit(); con.close()
    return redirect("/arkib")

@app.route("/arkib")
@login_required
def arkib():
    con = db()
    rows = con.execute("SELECT * FROM sejarah ORDER BY id DESC").fetchall()
    total = len(rows)
    duit = sum([r['harga'] or 0 for r in rows if r['bayar'] == 'Sudah'])
    con.close()
    html = f"""
    <!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Arkib - ARAPP Garage</title>
    <style>body{{font-family:sans-serif;background:#f4f4f4;padding:12px;margin:0}}
    .card{{background:white;padding:14px;border-radius:12px;margin-bottom:10px;box-shadow:0 2px 5px #ddd}}
    a.btn{{display:block;background:#111;color:white;text-align:center;padding:12px;border-radius:8px;text-decoration:none;font-weight:bold;margin-bottom:10px}}
    a.btn-del{{display:block;background:#e53935;color:white;text-align:center;padding:10px;border-radius:8px;text-decoration:none;font-weight:bold;margin-top:10px}}
    a.btn-del-all{{display:block;background:#b71c1c;color:white;text-align:center;padding:12px;border-radius:8px;text-decoration:none;font-weight:bold;margin-bottom:10px}}
    </style></head><body>
    <h1 style="text-align:center">📦 ARKIB - Motor Lama</h1>
    <a class="btn" href="/">⬅️ BALIK KE PAGE UTAMA</a>
    <a class="btn-del-all" href="/delete_arkib_all" onclick="return confirm('Betul nak PADAM SEMUA Arkib? Tak boleh undo!')">🗑️ PADAM SEMUA ARKIB</a>
    <p style="text-align:center">Total Arkib: <b>{total}</b> | Duit Sudah Bayar: <b>RM{duit}</b></p>
    """
    if not rows:
        html += "<div class='card'><p>Arkib masih kosong. Belum ada motor yang di-delete.</p></div>"
    for r in rows:
        html += f"""
        <div class="card">
        <b>{r['jenis']} - {r['plat']}</b><br>
        👤 {r['customer']} - {r['phone']}<br>
        🔧 {r['masalah']}<br>
        💰 RM{r['harga'] or 0} | Pomen: {r['pomen'] or '-'} | Bayar: {r['bayar']}<br>
        📅 Tarikh Tutup: {r['tarikh_tutup'] or '-'}
        <a class="btn-del" href="/delete_arkib/{r['id']}" onclick="return confirm('Padam {r['plat']} dari Arkib?')">🗑️ PADAM</a>
        </div>
        """
    html += "</body></html>"
    return html

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
.top{display:flex;gap:8px;text-align:center}
.top div{flex:1;background:white;padding:10px;border-radius:10px}
</style></head><body>
<h1>🏍️ ArappSystem Garage</h1>
<p style="text-align:center;font-size:12px">Aktif sampai: {{tarikh_habis}} | <a href="/subscribe">Subscribe</a> | <a href="/logout">Logout</a></p>
<a href="/delete_all" onclick="return confirm('DELETE ALL? Semua job akan pindah ke Arkib!')" style="display:block;background:red;color:white;text-align:center;padding:12px;border-radius:8px;text-decoration:none;font-weight:bold;margin:10px 0;">🗑️ DELETE ALL - PINDAH KE ARKIB</a>
<a href="/arkib" style="display:block;background:#673ab7;color:white;text-align:center;padding:12px;border-radius:8px;text-decoration:none;font-weight:bold;margin:10px 0;">📦 TENGOK ARKIB - Motor Lama</a>
<div class="top">
<div><b>{{total}}</b><br>Motor Hari Ni</div>
<div><b>{{siap}}</b><br>Dah Siap</div>
<div><b>RM{{duit}}</b><br>Duit Masuk</div>
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
<textarea style="width:100%;height:160px;margin-top:10px;padding:10px;">REPORT ARAPP DEMO
Tarikh: {{today}}
Motor Hari Ni: {{total}}
Dah Siap: {{siap}}
Duit Masuk: RM{{duit}}
PERLU APPROVAL BOSS:
{% for r in need_approval %}- {{r['jenis']}} {{r['plat']}} - {{r['masalah']}} - RM{{r['harga']}}
{% else %}Tiada approval. Semua clear
{% endfor %}Dihantar dari ARAPP DEMO</textarea>
<p style="font-size:12px;">Tekan lama dalam kotak atas tu, SELECT ALL, COPY, pergi WhatsApp PASTE.</p>
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
<a href="/edit/{{r['id']}}" style="display:block;background:#ff9800;color:white;text-align:center;padding:10px;border-radius:8px;text-decoration:none;font-weight:bold;">✏️ EDIT - BETULKAN</a>
<br>
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
@login_required
def index():
    if check_subscribe():
        return redirect("/subscribe")
    con=db(); rows=con.execute("SELECT * FROM motor ORDER BY id DESC").fetchall()
    need=con.execute("SELECT * FROM motor WHERE status='Tunggu Approval'").fetchall()
    kedai=con.execute("SELECT * FROM kedai LIMIT 1").fetchone()
    total=len(rows); siap=len([r for r in rows if r['status']=='Dah Siap'])
    duit=sum([r['harga'] or 0 for r in rows if r['bayar']=='Sudah'])
    con.close()
    return render_template_string(HTML, rows=rows, need_approval=need, total=total, siap=siap, duit=duit, tarikh_habis=kedai['tarikh_habis'] if kedai else '-', today=date.today().isoformat())

@app.route("/add", methods=["POST"])
@login_required
def add():
    con=db(); con.execute("INSERT INTO motor (customer,phone,plat,jenis,masalah) VALUES (?,?,?,?,?)",(request.form['customer'],request.form['phone'],request.form['plat'],request.form['jenis'],request.form['masalah'])); con.commit(); con.close(); return redirect("/")

@app.route("/kerja/<int:id>", methods=["POST"])
@login_required
def kerja(id):
    con=db(); con.execute("UPDATE motor SET status='Tengah Buat', pomen=? WHERE id=?",(request.form['pomen'],id)); con.commit(); con.close(); return redirect("/")

@app.route("/siap/<int:id>", methods=["POST"])
@login_required
def siap(id):
    con=db(); con.execute("UPDATE motor SET status='Tunggu Approval', harga=? WHERE id=?",(request.form['harga'],id)); con.commit(); con.close(); return redirect("/")

@app.route("/approve/<int:id>", methods=["POST"])
@login_required
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
@login_required
def bayar(id):
    con=db(); con.execute("UPDATE motor SET bayar='Sudah' WHERE id=?",(id,)); con.commit(); con.close(); return redirect("/")

@app.route("/edit/<int:id>")
@login_required
def edit(id):
    con=db(); r=con.execute("SELECT * FROM motor WHERE id=?",(id,)).fetchone(); con.close()
    if not r:
        return redirect("/")
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
@login_required
def update(id):
    con=db(); con.execute("UPDATE motor SET customer=?, phone=?, plat=?, jenis=?, masalah=?, harga=?, pomen=? WHERE id=?",
    (request.form.get('customer'), request.form.get('phone'), request.form.get('plat'), request.form.get('jenis'), request.form.get('masalah'), request.form.get('harga'), request.form.get('pomen'), id))
    con.commit(); con.close()
    return redirect("/")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
