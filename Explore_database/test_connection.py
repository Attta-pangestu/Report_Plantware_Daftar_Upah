import json
import pyodbc

def test_database_connection():
    # Membaca konfigurasi dari file config.json
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    db_config = config['database']
    
    # Membangun connection string
    server = db_config['server']
    port = db_config['port']
    username = db_config['username']
    password = db_config['password']
    database = db_config['database_name']
    
    # Connection string untuk MSSQL
    connection_string = f"DRIVER={{{db_config['driver']}}};SERVER={server},{port};DATABASE={database};UID={username};PWD={password}"
    
    try:
        # Membuat koneksi
        conn = pyodbc.connect(connection_string)
        print("✅ Koneksi ke database berhasil!")
        print(f"Database: {database}")
        print(f"Server: {server}:{port}")
        
        # Menguji dengan menjalankan query sederhana
        cursor = conn.cursor()
        cursor.execute("SELECT 1 as test")
        result = cursor.fetchone()
        print(f"Query test berhasil: {result[0]}")
        
        # Menutup koneksi
        conn.close()
        print("✅ Koneksi ditutup.")
        
    except pyodbc.Error as e:
        print(f"❌ Koneksi ke database gagal: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    test_database_connection()