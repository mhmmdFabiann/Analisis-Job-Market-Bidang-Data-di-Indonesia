-- =============================================================================
-- Indonesian Data Job Market Intelligence - Database Schema (PostgreSQL)
-- File: sql/schema.sql
-- Description: DDL untuk mendefinisikan tabel master lowongan (jobs_master)
--              dan tabel keterampilan teknis (skills_master).
-- =============================================================================

-- 1. Bersihkan tabel jika sudah ada (Urutan: Child table dulu, baru Parent table)
DROP TABLE IF EXISTS skills_master CASCADE;
DROP TABLE IF EXISTS jobs_master CASCADE;

-- 2. Tabel Master Lowongan Pekerjaan (jobs_master)
CREATE TABLE jobs_master (
    job_id                  VARCHAR(50)     PRIMARY KEY,
    source                  VARCHAR(20)     NOT NULL,
    source_job_id           VARCHAR(50),
    job_url                 TEXT            NOT NULL,
    title_raw               VARCHAR(255)    NOT NULL,
    role_group              VARCHAR(50)     NOT NULL,
    role_standard           VARCHAR(50)     NOT NULL,
    company_raw             VARCHAR(255),
    industry_category       VARCHAR(100),
    province                VARCHAR(100),
    city                    VARCHAR(100),
    work_mode               VARCHAR(50),
    employment_type         VARCHAR(50),
    education_requirement   VARCHAR(50),
    experience_level        VARCHAR(50),
    salary_min              NUMERIC(15, 2),
    salary_max              NUMERIC(15, 2),
    salary_median           NUMERIC(15, 2),
    collected_at            TIMESTAMP,
    regional_group          VARCHAR(50),
    salary_bracket          VARCHAR(50),
    is_salary_disclosed     BOOLEAN         NOT NULL DEFAULT FALSE,
    skills_count            INTEGER         NOT NULL DEFAULT 0,
    created_at              TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Tabel Master Keterampilan Teknis (skills_master)
CREATE TABLE skills_master (
    id                      SERIAL          PRIMARY KEY,
    job_id                  VARCHAR(50)     NOT NULL,
    source                  VARCHAR(20)     NOT NULL,
    role_group              VARCHAR(50)     NOT NULL,
    skill_name              VARCHAR(100)    NOT NULL,
    skill_category          VARCHAR(100)    NOT NULL,
    created_at              TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_skills_job FOREIGN KEY (job_id) 
        REFERENCES jobs_master(job_id) ON DELETE CASCADE,
    CONSTRAINT uq_job_skill UNIQUE (job_id, skill_name)
);

-- 4. Indeks Kinerja untuk Optimasi Query Analitik & Agregasi
CREATE INDEX idx_jobs_role_group ON jobs_master(role_group);
CREATE INDEX idx_jobs_industry_category ON jobs_master(industry_category);
CREATE INDEX idx_jobs_province ON jobs_master(province);
CREATE INDEX idx_jobs_city ON jobs_master(city);
CREATE INDEX idx_jobs_experience_level ON jobs_master(experience_level);
CREATE INDEX idx_jobs_education_requirement ON jobs_master(education_requirement);
CREATE INDEX idx_jobs_source ON jobs_master(source);
CREATE INDEX idx_jobs_salary_disclosed ON jobs_master(is_salary_disclosed);
CREATE INDEX idx_jobs_work_mode ON jobs_master(work_mode);

CREATE INDEX idx_skills_job_id ON skills_master(job_id);
CREATE INDEX idx_skills_name ON skills_master(skill_name);
CREATE INDEX idx_skills_category ON skills_master(skill_category);
CREATE INDEX idx_skills_role_group ON skills_master(role_group);

-- 5. Dokumentasi Kamus Data (PostgreSQL Column Comments)
COMMENT ON TABLE jobs_master IS 'Tabel master lowongan kerja bidang data hasil pembersihan dan integrasi multi-sumber (Glints & JobStreet)';
COMMENT ON COLUMN jobs_master.job_id IS 'Primary key unik gabungan prefix platform dan identifier lowongan';
COMMENT ON COLUMN jobs_master.source IS 'Platform asal sumber data (Glints / JobStreet)';
COMMENT ON COLUMN jobs_master.role_group IS 'Kelompok profesi data (Data Analytics & BI, Data Engineering, Data Science & AI, Machine Learning & AI)';
COMMENT ON COLUMN jobs_master.role_standard IS 'Standarisasi peran pekerjaan hasil normalisasi';
COMMENT ON COLUMN jobs_master.industry_category IS 'Kategori industri perusahaan hasil klasifikasi berbasis keyword & profil';
COMMENT ON COLUMN jobs_master.province IS 'Provinsi lokasi penempatan kerja di Indonesia';
COMMENT ON COLUMN jobs_master.city IS 'Kabupaten/Kota lokasi penempatan kerja';
COMMENT ON COLUMN jobs_master.salary_median IS 'Nilai tengah estimasi gaji bulanan yang dinormalisasi (Rupiah)';
COMMENT ON COLUMN jobs_master.is_salary_disclosed IS 'Penanda boolean apakah lowongan mempublikasikan informasi gaji atau tidak';

COMMENT ON TABLE skills_master IS 'Tabel master keterampilan teknis (skills & tools) yang diekstraksi dari deskripsi lowongan';
COMMENT ON COLUMN skills_master.id IS 'Surrogate auto-increment primary key untuk relasi granular';
COMMENT ON COLUMN skills_master.job_id IS 'Foreign key yang merujuk ke jobs_master.job_id';
COMMENT ON COLUMN skills_master.skill_name IS 'Nama keterampilan atau teknologi teknis yang dinormalisasi';
COMMENT ON COLUMN skills_master.skill_category IS 'Kategori keterampilan (Programming Languages, Databases, BI & Visualization, Big Data & Cloud, Data Science & ML)';
