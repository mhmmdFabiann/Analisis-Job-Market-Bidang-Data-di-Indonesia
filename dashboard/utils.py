import os
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv

# Direktori Proyek
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
ENV_PATH = PROJECT_ROOT / ".env"

load_dotenv(ENV_PATH)

def get_database_engine():
    """Membangun koneksi SQLAlchemy Engine ke PostgreSQL lokal jika tersedia."""
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD", "")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "loker_data")
    
    if not db_user or not db_name:
        return None

    try:
        from sqlalchemy import create_engine, text
        conn_str = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        engine = create_engine(conn_str, pool_pre_ping=True, connect_args={"connect_timeout": 2})
        with engine.connect() as conn:
            conn.execute(text("SELECT 1;"))
        return engine
    except Exception:
        return None

def load_data():
    """
    Memuat dataset master jobs dan skills.
    1. Mencoba dari database PostgreSQL lokal jika service menyala di laptop.
    2. Fallback otomatis membaca file data/processed/ (Parquet / CSV) untuk Streamlit Cloud.
    """
    engine = get_database_engine()
    df_jobs = None
    df_skills = None
    source_used = "Local PostgreSQL (loker_data)"
    
    if engine is not None:
        try:
            with engine.connect() as conn:
                df_jobs = pd.read_sql("SELECT * FROM jobs_master;", conn)
                df_skills = pd.read_sql("SELECT * FROM skills_master;", conn)
        except Exception:
            df_jobs = None
            df_skills = None
            
    # Fallback ke file data bersih terstandarisasi (digunakan oleh Streamlit Cloud)
    if df_jobs is None or df_skills is None:
        source_used = "Clean Processed Datasets (data/processed/)"
        jobs_p = DATA_PROCESSED_DIR / "jobs_master.parquet"
        skills_p = DATA_PROCESSED_DIR / "skills_master.parquet"
        
        if jobs_p.exists():
            df_jobs = pd.read_parquet(jobs_p)
        elif (DATA_PROCESSED_DIR / "jobs_master.csv").exists():
            df_jobs = pd.read_csv(DATA_PROCESSED_DIR / "jobs_master.csv")
            
        if skills_p.exists():
            df_skills = pd.read_parquet(skills_p)
        elif (DATA_PROCESSED_DIR / "skills_master.csv").exists():
            df_skills = pd.read_csv(DATA_PROCESSED_DIR / "skills_master.csv")

    if df_jobs is not None and "collected_at" in df_jobs.columns:
        df_jobs["collected_at"] = pd.to_datetime(df_jobs["collected_at"], errors="coerce")
        
    return df_jobs, df_skills, source_used

def format_rupiah(value):
    """Format angka ke format Rupiah standar, misal: Rp 12.500.000"""
    if pd.isna(value) or value is None or value <= 0:
        return "Dirahasiakan"
    return f"Rp {int(value):,}".replace(",", ".")

def format_rupiah_singkat(value):
    """Format angka ke format jutaan ringkas, misal: Rp 12,5 Jt"""
    if pd.isna(value) or value is None or value <= 0:
        return "N/A"
    jt = value / 1_000_000
    return f"Rp {jt:.1f} Jt".replace(".", ",")

def format_percent(value):
    """Format angka desimal ke persentase, misal: 46,8%"""
    if pd.isna(value) or value is None:
        return "0,0%"
    return f"{value:.1f}%".replace(".", ",")
