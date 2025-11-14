from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os
from datetime import datetime
from sqlalchemy import func, and_
import face_recognition 
import io
import numpy as np
import base64

load_dotenv()  # Memuat variabel dari file .env

app = Flask(__name__)
app.secret_key = "your_secret_key"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'photos')  # Folder untuk menyimpan foto

db = SQLAlchemy(app)

# Model Database
class Tamu(db.Model):

    __tablename__ = 'tamu'

    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(50), nullable=True)
    alamat = db.Column(db.Text, nullable=False)
    nomor_hp = db.Column(db.String(15), nullable=False)
    face_encoding = db.Column(db.Text, nullable=True) 

    def __repr__(self):
        return f"<Tamu {self.nama}>"

class FotoTamu(db.Model):

    __tablename__ = 'foto_tamu'

    id = db.Column(db.Integer, primary_key=True)
    visit_id = db.Column(db.Integer, db.ForeignKey('visit.id'), unique=True, nullable=False)
    foto_path = db.Column(db.String(255), nullable=False)

    visit = db.relationship('Visit',  backref=db.backref('foto_tamu', uselist=False))

class Visit(db.Model):
    __tablename__ = 'visit'

    id = db.Column(db.Integer, primary_key=True)
    tamu_id = db.Column(db.Integer, db.ForeignKey('tamu.id'), nullable=False)
    nama_instansi = db.Column(db.String(100), nullable=True)
    tanggal = db.Column(db.Date, nullable=False, default=datetime.today().date)
    jam = db.Column(db.Time, nullable=False, default=datetime.now().time)
    pesan = db.Column(db.Text, nullable=False)

    # Relasi ke model Tamu
    tamu = db.relationship('Tamu', backref='visits')

    def __repr__(self):
        return f"<Visit {self.tanggal} oleh Tamu ID {self.tamu_id}>"
 
# Perintah untuk membuat database jika belum ada
if not os.path.exists('database.db'):
    with app.app_context():
        db.create_all()
        print("Database berhasil dibuat.")

# Halaman Home
@app.route("/")
def home():
    return render_template("home.html", current_year=datetime.now().year)

# Fungsi deteksi wajah
@app.route('/detect_face', methods=['POST'])
def detect_face():
    image_data = request.json.get('image')
    if not image_data:
        return jsonify({"error": "Gambar tidak ditemukan!"}), 400

    try:
        image_binary = base64.b64decode(image_data.split(',')[1])
        image_stream = io.BytesIO(image_binary)
        image_array = face_recognition.load_image_file(image_stream)
        face_encodings = face_recognition.face_encodings(image_array)

        if not face_encodings:
            return jsonify({"error": "Wajah tidak ditemukan dalam gambar!"}), 400

        # Cek semua wajah dalam gambar
        tamu = Tamu.query.all()

        for face_encoding in face_encodings:  # Loop untuk semua wajah yang terdeteksi
            for person in tamu:
                stored_encoding = np.fromstring(person.face_encoding, sep=',')
                match = face_recognition.compare_faces([stored_encoding], face_encoding, tolerance=0.3)

                if match[0]:  # Jika cocok, tambahkan ke hasil
                    # Ambil kunjungan terakhir tamu (jika ada)
                    last_visit = Visit.query.filter_by(tamu_id=person.id).order_by(Visit.tanggal.desc()).first()

                    return jsonify({
                        "success": True,
                        "nama": person.nama,
                        "alamat": person.alamat,
                        "email": person.email,
                        "nomor_hp": person.nomor_hp,
                        "nama_instansi": last_visit.nama_instansi if last_visit else "Tidak ada data"
                    })

        return jsonify({"success": False, "message": "Wajah tidak dikenali"}), 404

    except Exception as e:
        return jsonify({"error": f"Terjadi kesalahan: {e}"}), 400

# Form Pengisian Tamu
@app.route('/form_tamu', methods=['GET','POST'])
def form_tamu():
    if request.method == 'POST':
        # Ambil data dari form
        nama = request.form.get('nama')
        email = request.form.get('email')
        nama_instansi = request.form.get('nama_instansi')
        alamat = request.form.get('alamat')
        nomor_hp = request.form.get('nomor_hp')
        pesan = request.form.get('pesan')
        image_data = request.form.get('image')  # Base64 image dari frontend
        
        # Validasi data wajib
        if not all([nama, alamat, nomor_hp, pesan, image_data]):
            flash('Semua data wajib diisi!', 'form_tamu_danger')
            return redirect(url_for('form_tamu'))

        try:
             # Simpan gambar ke folder
            image_filename = f"{nama.replace(' ', '_')}_photo_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)

            # Decode Base64 menjadi byte stream
            image_binary = base64.b64decode(image_data.split(',')[1])

             # Pastikan gambar berhasil disimpan
            with open(image_path, 'wb') as f:
                f.write(image_binary)

            # Proses encoding wajah
            image_array = face_recognition.load_image_file(image_path)
            face_encodings = face_recognition.face_encodings(image_array)

            if not face_encodings:
                flash('Gagal mengenali wajah pada gambar!', 'form_tamu_danger')
                face_encoding_str = None

            else:
                face_encoding_str = ','.join(map(str, face_encodings[0]))  # Ubah encoding ke string

        except Exception as e:
            flash(f"Gambar tidak valid: {e}", 'form_tamu_danger')
            return redirect(url_for('form_tamu'))

        # Simpan data tamu ke database
        try:
            tamu = Tamu(
                nama=nama,
                email=email,
                alamat=alamat,
                nomor_hp=nomor_hp,
                face_encoding=face_encoding_str,
            )
            db.session.add(tamu)
            db.session.commit()

            # Simpan data kunjungan
            kunjungan = Visit(
                tamu_id=tamu.id,
                nama_instansi=nama_instansi,
                tanggal=datetime.today().date(),
                jam=datetime.now().time(),
                pesan=pesan
            )
            db.session.add(kunjungan)
            db.session.commit()

            # Simpan data foto ke tabel FotoTamu
            foto_tamu = FotoTamu(
                visit_id=kunjungan.id,
                foto_path=image_filename
            )
            db.session.add(foto_tamu)
            db.session.commit()

            flash('Data tamu dan kunjungan berhasil disimpan!', 'form_tamu_success')
        except Exception as e:
            db.session.rollback()
            flash(f"Terjadi kesalahan saat menyimpan data: {e}", 'form_tamu_danger')
        return redirect(url_for('form_tamu'))

    return render_template('form_tamu.html')

# Daftar Tamu (Admin Only)
@app.route("/daftar_tamu")
def daftar_tamu():
    if not session.get("admin_logged_in"):
        return redirect(url_for("login"))
    
     # Ambil parameter filter berdasarkan tanggal
    full_date = request.args.get('full_date')  # Format YYYY-MM-DD
    year_month = request.args.get('year_month')  # Format YYYY-MM
    year = request.args.get('year') # Tanggal dalam format YYYY-MM-DD

    # Query dasar untuk semua data tamu
    query = db.session.query(Tamu, Visit).join(Visit, Tamu.id == Visit.tamu_id)

    # Filter berdasarkan tanggal
    if full_date:  # Jika tanggal lengkap tersedia
        try:
            query = query.filter(Visit.tanggal == full_date)
        except ValueError:
            return "Format tanggal lengkap tidak valid", 400
    elif year_month:  # Jika hanya tahun dan bulan tersedia
        try:
            year, month = map(int, year_month.split('-'))
            query = query.filter(and_(
                func.extract('year', Visit.tanggal) == year,
                func.extract('month', Visit.tanggal) == month
            ))
        except ValueError:
            return "Format tahun-bulan tidak valid", 400
    elif year:  # Jika hanya tahun tersedia
        try:
            year = int(year)
            query = query.filter(func.extract('year', Visit.tanggal) == int(year))
        except ValueError:
            return "Format tahun tidak valid", 400
    
    kunjungan = query.order_by(Visit.tanggal.desc(), Visit.jam.desc()).all()

    # Hitung kunjungan per hari
    kunjungan_harian = db.session.query(func.count(Visit.id)).filter(
        func.date(Visit.tanggal) == func.current_date()
    ).scalar()

    # Hitung kunjungan per bulan
    kunjungan_bulanan = db.session.query(func.count(Visit.id)).filter(
        func.extract('month', Visit.tanggal) == datetime.today().month,
        func.extract('year', Visit.tanggal) == datetime.today().year
    ).scalar()

    # Hitung kunjungan per tahun
    kunjungan_tahunan = db.session.query(func.count(Visit.id)).filter(
        func.extract('year', Visit.tanggal) == datetime.today().year
    ).scalar()

    filter_title = " "  # Default jika tidak ada filter
    if full_date:
        filter_title = f"Tanggal: {full_date}"
    elif year_month:
        filter_title = f"Bulan: {year_month}"
    elif year:
        filter_title = f"Tahun: {year}"

    return render_template(
        'daftar_tamu.html',
        kunjungan=kunjungan,
        date=full_date,
        filter_title=filter_title,
        request=request,
        kunjungan_harian=kunjungan_harian,
        kunjungan_bulanan=kunjungan_bulanan,
        kunjungan_tahunan=kunjungan_tahunan
    )

# Edit Tamu
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_tamu(id):
    tamu = Tamu.query.get_or_404(id)

      # Ambil kunjungan terakhir yang terkait dengan tamu ini
    kunjungan = Visit.query.filter_by(tamu_id=id).order_by(Visit.tanggal.desc(), Visit.jam.desc()).first()
    if request.method == "POST":
        tamu.nama = request.form['nama']
        tamu.email = request.form['email']
        kunjungan.nama_instansi = request.form['nama_instansi']
        tamu.alamat = request.form['alamat']
        tamu.nomor_hp = request.form['nomor_hp']
        kunjungan.pesan = request.form['pesan']

        db.session.commit()  # Simpan perubahan
        flash("Data tamu berhasil diperbarui!", "daftar_tamu_success")
        return redirect(url_for("daftar_tamu"))

    return render_template("edit_tamu.html", tamu=tamu, kunjungan=kunjungan)

# Delete tamu
@app.route("/delete/<int:id>", methods=["POST"])
def delete_tamu(id):
    try:
        # Ambil data tamu berdasarkan ID
        tamu = Tamu.query.get_or_404(id)

        # Hapus semua kunjungan terkait
        for visit in tamu.visits:
            # Hapus foto terkait kunjungan (jika ada)
            if visit.foto_tamu:
                foto_path = os.path.join(app.config['UPLOAD_FOLDER'], visit.foto_tamu.foto_path)
                if os.path.exists(foto_path):
                    try:
                        os.remove(foto_path)  # Hapus file foto dari folder
                        flash(f"File foto {foto_path} berhasil dihapus.")
                    except Exception as e:
                        flash(f"Terjadi kesalahan: {e}", "danger")
                else:
                    print(f"File foto {foto_path} tidak ditemukan.")
                db.session.delete(visit.foto_tamu)  # Hapus entri dari database

            db.session.delete(visit)  # Hapus entri kunjungan dari database

        # Hapus tamu
        db.session.delete(tamu)

        # Commit perubahan
        db.session.commit()
        flash("Data tamu dan semua data terkait berhasil dihapus!", "daftar_tamu_success")
    except Exception as e:
        db.session.rollback()  # Batalkan perubahan jika ada kesalahan
        flash(f"Kesalahan saat menghapus data: {e}", "daftar_tamu_danger")
    return redirect(url_for("daftar_tamu"))

# Detail Tamu
@app.route("/detail/<int:id>")
def detail_tamu(id):
    # Ambil data tamu berdasarkan ID
    tamu = Tamu.query.get_or_404(id)
    # Ambil data kunjungan terkait
    kunjungan = Visit.query.filter_by(tamu_id=id).all()
    return render_template("detail_tamu.html", tamu=tamu, kunjungan=kunjungan)

# Login Admin
# Mengambil username dan password dari .env
admin_username = os.getenv('ADMIN_USERNAME')
admin_password = os.getenv('ADMIN_PASSWORD')

@app.route("/login", methods=["GET", "POST"])
def login():
    global admin_username, admin_password

    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']

        if username == admin_username and password == admin_password:
            session["admin_logged_in"] = True
            return redirect(url_for("daftar_tamu"))
        else:
            flash("Login gagal. Periksa username dan password.", "danger")

    return render_template("login.html")

# Ganti akun
@app.route("/ganti_akun", methods=["GET", "POST"])
def ganti_akun():
    global admin_username, admin_password

    if request.method == "POST":
        new_username = request.form['new_username']
        new_password = request.form['new_password']
        
        # Perbarui nilai username dan password
        admin_username = new_username
        admin_password = new_password
        
        # Perbarui nilai di file .env
        with open(".env", "w") as f:
            f.write(f"ADMIN_USERNAME={admin_username}\n")
            f.write(f"ADMIN_PASSWORD={admin_password}\n")
        
        flash("Username dan password berhasil diubah!", "success")
        return redirect(url_for("login"))

    return render_template("ganti_akun.html")

# Logout Admin
@app.route("/logout")
def logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("home"))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
