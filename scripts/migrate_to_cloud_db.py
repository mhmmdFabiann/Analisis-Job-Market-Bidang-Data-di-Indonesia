import os
import sys
import argparse
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text

# Direktori Proyek
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_PROCESSED_DIR = ROOT_DIR / "data" / "processed"
SQL_DIR = ROOT_DIR / "sql"

def migrate_to_cloud(connection_url: str):
    """
    Membuat tabel relasional, views, dan memuat 250 lowongan serta 
    1.061 keahlian teknis ke Cloud PostgreSQL (Neon / Supabase / dll).
    """
    # Standarisasi URI untuk SQLAlchemy
    clean_url = connection_url.strip()
    if clean_url.startswith("postgres://"):
        clean_url = clean_url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif clean_url.startswith("postgresql://") and not clean_url.startswith("postgresql+psycopg2://"):
        clean_url = clean_url.replace("postgresql://", "postgresql+psycopg2://", 1)

    print("=" * 70)
    print("MIGRASI DATA KE CLOUD POSTGRESQL (NEON / SUPABASE)")
    print("=" * 70)
    print(f"Menghubungkan ke database cloud...")

    try:
        engine = create_engine(clean_url, pool_pre_ping=True)
        with engine.connect() as conn:
            ver = conn.execute(text("SELECT version();")).scalar()
            curr_db = conn.execute(text("SELECT current_database();")).scalar()
            print(f"✅ Berhasil terkoneksi ke database '{curr_db}'!")
            print(f"   Server: {ver.split(',')[0]}")
    except Exception as e:
        print(f"❌ Gagal terkoneksi: {e}")
        sys.exit(1)

    # 1. Eksekusi Schema DDL
    print("\n1. Mengeksekusi DDL schema.sql...")
    with open(SQL_DIR / "schema.sql", "r", encoding="utf-8") as f:
        schema_sql = f.read()
    
    with engine.begin() as conn:
        for stmt in schema_sql.split(";"):
            stmt = stmt.strip()
            if stmt:
                conn.execute(text(stmt))
    print("   ✅ Tabel 'jobs_master' dan 'skills_master' berhasil dibuat!")

    # 2. Eksekusi Views
    print("\n2. Mengeksekusi Analytical Views (views.sql)...")
    with open(SQL_DIR / "views.sql", "r", encoding="utf-8") as f:
        views_sql = f.read()

    with engine.begin() as conn:
        for stmt in views_sql.split(";"):
            stmt = stmt.strip()
            if stmt:
                conn.execute(text(stmt))
    print("   ✅ Seluruh SQL views analitik berhasil dibuat!")

    # 3. Ingest Data Master
    print("\n3. Memuat data master ke database cloud...")
    jobs_file = DATA_PROCESSED_DIR / "jobs_master.parquet"
    skills_file = DATA_PROCESSED_DIR / "skills_master.parquet"

    df_jobs = pd.read_parquet(jobs_file) if jobs_file.exists() else pd.read_csv(DATA_PROCESSED_DIR / "jobs_master.csv")
    df_skills = pd.read_parquet(skills_file) if skills_file.exists() else pd.read_csv(DATA_PROCESSED_DIR / "skills_master.csv")

    df_jobs["collected_at"] = pd.to_datetime(df_jobs["collected_at"], errors="coerce")

    # Ingest ke jobs_master
    df_jobs.to_sql("jobs_master", engine, if_exists="append", index=False, method="multi", chunksize=500)
    print(f"   ✅ jobs_master: {len(df_jobs)} baris data berhasil dimuat.")

    # Ingest ke skills_master
    df_skills.to_sql("skills_master", engine, if_exists="append", index=False, method="multi", chunksize=500)
    print(f"   ✅ skills_master: {len(df_skills)} baris data berhasil dimuat.")

    # 4. Verifikasi Akhir
    with engine.connect() as conn:
        cnt_jobs = conn.execute(text("SELECT COUNT(*) FROM jobs_master;")).scalar()
        cnt_skills = conn.execute(text("SELECT COUNT(*) FROM skills_master;")).scalar()
        print("\n" + "=" * 70)
        print("HASIL VERIFIKASI CLOUD DATABASE:")
        print(f"- Total jobs_master   : {cnt_jobs} baris (Ekspektasi: 250) -> {'PASS ✅' if cnt_jobs == 250 else 'FAIL ❌'}")
        print(f"- Total skills_master : {cnt_skills} baris (Ekspektasi: 1.061) -> {'PASS ✅' if cnt_skills == 1061 else 'FAIL ❌'}")
        print("=" * 70)

    print("\n🎉 MIGRASI SELESAI! Langkah berikutnya:")
    print("Salin connection string di bawah ini dan masukkan ke menu 'Secrets' di Streamlit Cloud:\n")
    print("----------------------------------------------------------------------")
    print(f'DATABASE_URL = "{clean_url}"')
    print("----------------------------------------------------------------------")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrasikan dataset master ke Cloud PostgreSQL.")
    parser.add_argument("--uri", type=str, help="Connection string PostgreSQL Cloud (misal dari Neon atau Supabase)")
    args = parser.parse_args()

    if args.uri:
        url = args.uri
    else:
        url = input("Masukkan Connection String PostgreSQL Cloud Anda:\n> ").strip()

    if not url:
        print("Error: Connection String tidak boleh kosong!")
        sys.exit(1)

    migrate_to_cloud(url)
