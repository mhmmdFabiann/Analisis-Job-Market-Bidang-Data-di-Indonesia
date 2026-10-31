import os
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Direktori Proyek
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
ENV_PATH = PROJECT_ROOT / ".env"

load_dotenv(ENV_PATH)

def get_database_engine():
    """
    Membangun koneksi SQLAlchemy Engine ke PostgreSQL.
    Mendukung st.secrets (Streamlit Cloud) dan .env (Lokal).
    """
    conn_str = None
    
    # 1. Cek apakah berjalan di Streamlit Cloud dengan st.secrets
    try:
        import streamlit as st
        if hasattr(st, "secrets"):
            if "postgres" in st.secrets:
                pg = st.secrets["postgres"]
                user = pg.get("user")
                password = pg.get("password")
                host = pg.get("host")
                port = pg.get("port", 5432)
                dbname = pg.get("dbname")
                sslmode = pg.get("sslmode", "require")
                conn_str = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}?sslmode={sslmode}"
            elif "DATABASE_URL" in st.secrets:
                raw_url = str(st.secrets["DATABASE_URL"]).strip()
                if raw_url.startswith("postgres://"):
                    raw_url = raw_url.replace("postgres://", "postgresql+psycopg2://", 1)
                elif raw_url.startswith("postgresql://") and not raw_url.startswith("postgresql+psycopg2://"):
                    raw_url = raw_url.replace("postgresql://", "postgresql+psycopg2://", 1)
                conn_str = raw_url
    except Exception:
        conn_str = None

    # 2. Cek variabel lokal (.env) jika tidak ada st.secrets
    if not conn_str:
        db_user = os.getenv("DB_USER", "postgres")
        db_password = os.getenv("DB_PASSWORD", "")
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "5432")
        db_name = os.getenv("DB_NAME", "loker_data")
        db_sslmode = os.getenv("DB_SSLMODE", "")
        ssl_suffix = f"?sslmode={db_sslmode}" if db_sslmode else ""
        if db_name:
            conn_str = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}{ssl_suffix}"
    
    if not conn_str:
        return None

    try:
        engine = create_engine(conn_str, pool_pre_ping=True, connect_args={"connect_timeout": 5})
        with engine.connect() as conn:
            conn.execute(text("SELECT 1;"))
        return engine
    except Exception:
        return None

def load_data():
    """
    Memuat dataset master jobs dan skills.
    Mencoba dari database PostgreSQL (Cloud / Lokal) terlebih dahulu,
    jika offline otomatis fallback ke file processed lokal.
    """
    engine = get_database_engine()
    df_jobs = None
    df_skills = None
    source_used = "PostgreSQL Database"
    
    if engine is not None:
        try:
            with engine.connect() as conn:
                df_jobs = pd.read_sql("SELECT * FROM jobs_master;", conn)
                df_skills = pd.read_sql("SELECT * FROM skills_master;", conn)
                current_db = conn.execute(text("SELECT current_database();")).scalar()
                current_host = conn.execute(text("SELECT inet_server_addr();")).scalar()
                source_used = f"Cloud/Remote DB ({current_db})" if current_host != "127.0.0.1" else f"Local PostgreSQL ({current_db})"
        except Exception:
            df_jobs = None
            df_skills = None
            
    if df_jobs is None or df_skills is None:
        source_used = "Local Files (data/processed/)"
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
