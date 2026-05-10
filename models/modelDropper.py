from sqlalchemy import MetaData, text
from sqlalchemy.schema import DropTable

from databases.connection import engine

def drop_all_tables_from_db():
    metadata = MetaData()

    try:
        print("Menghubungkan ke database melalui databases.connection...")
        metadata.reflect(bind=engine)
        
        if not metadata.tables:
            print("Database sudah kosong, tidak ada tabel untuk didrop.")
            return

        print(f"Ditemukan {len(metadata.tables)} tabel. Memulai proses drop...")

        with engine.connect() as conn:
            conn.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
            
            for table in metadata.sorted_tables:
                print(f"Menghapus tabel: {table.name}")
                conn.execute(DropTable(table))
            conn.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
            conn.commit()

        print("\nSelesai! Semua tabel di database telah dihapus.")

    except Exception as e:
        print(f"Terjadi kesalahan saat menghapus tabel: {e}")

if __name__ == "__main__":
    confirm = input("Apakah Anda yakin ingin menghapus SELURUH tabel di database? (y/n): ")
    if confirm.lower() == 'y':
        drop_all_tables_from_db()
    else:
        print("Aksi dibatalkan.")