from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from models import db, Menu, Pesanan, DetailPesanan
from datetime import datetime
from sqlalchemy import func

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///kasir.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'
db.init_app(app)

# CRUD Menu
@app.route('/menu', methods=['GET', 'POST'])
def menu():
    # Tambah Menu
    if request.method == 'POST':
        nama = request.form['nama']
        harga = float(request.form['harga'])
        
        # Validasi input
        if not nama or harga <= 0:
            flash('Nama menu harus diisi dan harga harus lebih dari 0', 'error')
            return redirect(url_for('menu'))
        
        new_menu = Menu(nama=nama, harga=harga)
        db.session.add(new_menu)
        db.session.commit()
        flash('Menu berhasil ditambahkan', 'success')
        return redirect(url_for('menu'))
    
    # Lihat Daftar Menu
    menus = Menu.query.all()
    return render_template('menu.html', menus=menus)

# Edit Menu
@app.route('/menu/edit/<int:menu_id>', methods=['GET', 'POST'])
def edit_menu(menu_id):
    menu = Menu.query.get_or_404(menu_id)
    
    if request.method == 'POST':
        menu.nama = request.form['nama']
        menu.harga = float(request.form['harga'])
        
        # Validasi input
        if not menu.nama or menu.harga <= 0:
            flash('Nama menu harus diisi dan harga harus lebih dari 0', 'error')
            return redirect(url_for('edit_menu', menu_id=menu_id))
        
        db.session.commit()
        flash('Menu berhasil diubah', 'success')
        return redirect(url_for('menu'))
    
    return render_template('edit_menu.html', menu=menu)

# Hapus Menu
@app.route('/menu/hapus/<int:menu_id>')
def hapus_menu(menu_id):
    menu = Menu.query.get_or_404(menu_id)
    
    # Cek apakah menu pernah digunakan dalam pesanan
    pesanan_exist = DetailPesanan.query.filter_by(menu_id=menu_id).first()
    if pesanan_exist:
        flash('Tidak dapat menghapus menu yang sudah pernah dipesan', 'error')
        return redirect(url_for('menu'))
    
    db.session.delete(menu)
    db.session.commit()
    flash('Menu berhasil dihapus', 'success')
    return redirect(url_for('menu'))

@app.route('/pesanan', methods=['GET', 'POST'])
def pesanan():
    if request.method == 'POST':
        # Ambil data dari form
        menu_ids = request.form.getlist('menu_id[]')
        jumlahs = request.form.getlist('jumlah[]')
        
        # Validasi input
        if not menu_ids or not jumlahs:
            flash('Pilih setidaknya satu menu', 'error')
            return redirect(url_for('pesanan'))
        
        # Hitung total harga
        total_harga = 0
        detail_pesanan = []
        
        for menu_id, jumlah in zip(menu_ids, jumlahs):
            jumlah = int(jumlah)
            if jumlah <= 0:
                continue
            
            menu = Menu.query.get(menu_id)
            subtotal = menu.harga * jumlah
            total_harga += subtotal
            
            detail_pesanan.append({
                'menu_id': menu_id,
                'jumlah': jumlah,
                'subtotal': subtotal
            })
        
        # Buat pesanan
        pesanan_baru = Pesanan(total_harga=total_harga)
        db.session.add(pesanan_baru)
        db.session.flush()  # Untuk mendapatkan ID pesanan
        
        # Buat detail pesanan
        for detail in detail_pesanan:
            detail_pesanan_baru = DetailPesanan(
                pesanan_id=pesanan_baru.id,
                menu_id=detail['menu_id'],
                jumlah=detail['jumlah'],
                subtotal=detail['subtotal']
            )
            db.session.add(detail_pesanan_baru)
        
        db.session.commit()
        flash('Pesanan berhasil ditambahkan', 'success')
        return redirect(url_for('pesanan'))
    
    # Ambil semua menu dan pesanan
    menus = Menu.query.all()
    pesanans = Pesanan.query.order_by(Pesanan.waktu.desc()).all()
    
    # Gabungkan detail pesanan untuk setiap pesanan
    pesanan_details = []
    for pesanan in pesanans:
        details = DetailPesanan.query.filter_by(pesanan_id=pesanan.id).all()
        pesanan_details.append({
            'pesanan': pesanan,
            'details': details
        })
    
    return render_template('pesanan.html', menus=menus, pesanan_details=pesanan_details)

# Hapus Pesanan
@app.route('/pesanan/hapus/<int:pesanan_id>')
def hapus_pesanan(pesanan_id):
    pesanan = Pesanan.query.get_or_404(pesanan_id)
    
    # Hapus detail pesanan terlebih dahulu
    DetailPesanan.query.filter_by(pesanan_id=pesanan_id).delete()
    
    db.session.delete(pesanan)
    db.session.commit()
    flash('Pesanan berhasil dihapus', 'success')
    return redirect(url_for('pesanan'))

# Laporan Penjualan
@app.route('/laporan')
def laporan():
    # Laporan Harian
    harian = db.session.query(
        func.date(Pesanan.waktu).label('tanggal'),
        func.sum(Pesanan.total_harga).label('total_penjualan'),
        func.sum(DetailPesanan.jumlah).label('total_item')
    ).join(DetailPesanan, Pesanan.id == DetailPesanan.pesanan_id) \
     .group_by(func.date(Pesanan.waktu)) \
     .order_by(func.date(Pesanan.waktu).desc()) \
     .all()

    # Laporan Bulanan
    bulanan = db.session.query(
        func.strftime('%Y-%m', Pesanan.waktu).label('bulan'),
        func.sum(Pesanan.total_harga).label('total_penjualan'),
        func.sum(DetailPesanan.jumlah).label('total_item')
    ).join(DetailPesanan, Pesanan.id == DetailPesanan.pesanan_id) \
     .group_by(func.strftime('%Y-%m', Pesanan.waktu)) \
     .order_by(func.strftime('%Y-%m', Pesanan.waktu).desc()) \
     .all()

    # Laporan Tahunan
    tahunan = db.session.query(
        func.strftime('%Y', Pesanan.waktu).label('tahun'),
        func.sum(Pesanan.total_harga).label('total_penjualan'),
        func.sum(DetailPesanan.jumlah).label('total_item')
    ).join(DetailPesanan, Pesanan.id == DetailPesanan.pesanan_id) \
     .group_by(func.strftime('%Y', Pesanan.waktu)) \
     .order_by(func.strftime('%Y', Pesanan.waktu).desc()) \
     .all()

    return render_template('laporan.html', 
                           harian=harian, 
                           bulanan=bulanan, 
                           tahunan=tahunan)

@app.route('/')
def index():
    # Hitung total menu
    total_menu = Menu.query.count()
    
    # Hitung total pesanan hari ini
    today = datetime.now().date()
    total_pesanan_hari_ini = Pesanan.query.filter(
        func.date(Pesanan.waktu) == today
    ).count()
    
    # Hitung total penjualan hari ini
    total_penjualan_hari_ini = db.session.query(
        func.sum(Pesanan.total_harga)
    ).filter(
        func.date(Pesanan.waktu) == today
    ).scalar() or 0
    
    return render_template('index.html', 
                           total_menu=total_menu,
                           total_pesanan_hari_ini=total_pesanan_hari_ini,
                           total_penjualan_hari_ini=total_penjualan_hari_ini)
@app.template_filter('rupiah')
def rupiah_filter(value):
    try:
        return "{:,}".format(int(value)).replace(',', '.')
    except (ValueError, TypeError):
        return value
def index():
    return render_template('index.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)