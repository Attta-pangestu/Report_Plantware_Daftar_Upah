# 🧪 Test Koneksi Remote SQL Server

Folder ini berisi script untuk testing koneksi ke remote SQL Server.

## 📋 Server Information
- **Server**: 10.0.0.110
- **Port**: 1433
- **Username**: sa
- **Password**: ptrj@123
- **Database**: db_ptrj

## 🚀 Cara Menggunakan

### Opsi 1: Quick Test (Rekomendasi)
```bash
# Double-click file batch
run_test.bat

# Atau jalankan manual
python quick_test.py
```

### Opsi 2: Comprehensive Test
```bash
# Test lengkap dengan troubleshooting
python test_remote_sql.py
```

## 📁 File yang Tersedia

### `quick_test.py`
- ✅ Test koneksi cepat
- ✅ Menampilkan status sukses/gagal
- ✅ Count jumlah tabel
- ⏱️ ~5 detik

### `test_remote_sql.py`
- ✅ Test network connection
- ✅ Test SQL Server connection
- ✅ Test multiple credentials
- ✅ Database information
- ✅ Generate connection script
- ⏱️ ~30 detik

### `run_test.bat`
- 🖱️ Double-click untuk jalankan
- 📦 Auto-install dependencies
- 💻 Windows friendly

## 🎯 Expected Output

### ✅ Success:
```
🚀 QUICK CONNECTION TEST
==============================
Server: 10.0.0.110,1433
Username: sa
Password: *********

✅ CONNECTION SUCCESSFUL!
📊 Total tables: 45

🎉 Remote database is accessible!
```

### ❌ Failed:
```
🚀 QUICK CONNECTION TEST
==============================
Server: 10.0.0.110,1433
Username: sa
Password: *********

❌ CONNECTION FAILED: Login failed for user 'sa'

💡 Check:
1. Server is running
2. Credentials are correct
3. Network connection
4. SQL Server authentication mode
```

## 🛠️ Troubleshooting

### Error: "Login failed for user 'sa' (18456)"
**Solusi:**
1. Enable SQL Server Authentication (Mixed Mode)
2. Enable 'sa' account
3. Reset password 'sa'
4. Check password: ptrj@123

### Error: "Cannot connect to server"
**Solusi:**
1. Check server 10.0.0.110 is running
2. Check port 1433 is open
3. Check firewall settings
4. Check network connection

### Error: "ODBC Driver not found"
**Solusi:**
```bash
pip install pyodbc
```

## 🔧 Manual Testing dengan Python

```python
import pyodbc

conn_str = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=10.0.0.110,1433;DATABASE=db_ptrj;UID=sa;PWD=ptrj@123;Encrypt=no;"

try:
    conn = pyodbc.connect(conn_str)
    print("✅ Connected!")
    conn.close()
except Exception as e:
    print(f"❌ Failed: {e}")
```

## 📞 Need Help?

Jika test gagal:
1. Coba run comprehensive test: `python test_remote_sql.py`
2. Periksa server status
3. Hubungi admin database
4. Cek dokumentasi utama di `../README.md`

---

**Version**: 1.0.0
**Created**: November 2025