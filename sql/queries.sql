-- =============================================================================
-- Indonesian Data Job Market Intelligence - SQL Interview & Business Queries
-- File: sql/queries.sql
-- Description: Kumpulan query SQL analitik yang mengimplementasikan konsep-konsep
--              kunci pada panduan "Konsep SQL untuk Interview Data Analyst Junior".
-- =============================================================================

-- =============================================================================
-- BAGIAN 1: DASAR QUERY & OPERATOR FILTERING
-- Konsep: SELECT, WHERE, ORDER BY, LIMIT, DISTINCT, AND/OR/NOT, IN, BETWEEN, LIKE
-- =============================================================================

-- 1.1 Filter Lowongan Data Analyst di Jawa dengan Gaji 7-15 Juta & Judul Spesifik
SELECT 
    job_id,
    title_raw,
    company_raw,
    role_group,
    province,
    salary_median
FROM jobs_master
WHERE role_group = 'Data Analytics & BI'
  AND province IN ('DKI Jakarta', 'Jawa Barat', 'Jawa Tengah', 'Jawa Timur')
  AND salary_median BETWEEN 7000000 AND 15000000
  AND (title_raw ILIKE '%analyst%' OR title_raw ILIKE '%analis%')
ORDER BY salary_median DESC
LIMIT 10;

-- 1.2 Mendapatkan Daftar Unik (DISTINCT) Perusahaan yang Merekrut Talenta Data
SELECT DISTINCT 
    company_raw,
    industry_category,
    province
FROM jobs_master
WHERE company_raw IS NOT NULL
ORDER BY industry_category, company_raw
LIMIT 15;


-- =============================================================================
-- BAGIAN 2: AGREGASI, GROUP BY VS HAVING, DAN PERILAKU NULL
-- Konsep: COUNT(*), COUNT(kolom), AVG, WHERE vs HAVING
-- =============================================================================

-- 2.1 Pembuktian COUNT(*) vs COUNT(kolom): Mengapa COUNT(kolom) mengabaikan NULL
SELECT 
    role_group,
    COUNT(*) AS total_semua_lowongan,
    COUNT(salary_median) AS lowongan_dengan_gaji,
    COUNT(*) - COUNT(salary_median) AS lowongan_gaji_null,
    ROUND(AVG(salary_median), 0) AS rerata_gaji_valid,
    ROUND(AVG(COALESCE(salary_median, 0)), 0) AS rerata_jika_null_dianggap_nol
FROM jobs_master
GROUP BY role_group
ORDER BY total_semua_lowongan DESC;

-- 2.2 WHERE vs HAVING: Filter baris sebelum vs sesudah pengelompokan
-- WHERE memfilter lowongan Jabodetabek, HAVING memfilter industri dengan minimal 5 lowongan
SELECT 
    industry_category,
    COUNT(*) AS total_lowongan,
    ROUND(AVG(salary_median), 0) AS avg_salary
FROM jobs_master
WHERE province IN ('DKI Jakarta', 'Jawa Barat', 'Banten')
GROUP BY industry_category
HAVING COUNT(*) >= 5
ORDER BY total_lowongan DESC;


-- =============================================================================
-- BAGIAN 3: JENIS JOIN & KASUS ANTI-JOIN (INTERVIEW FAVORITE)
-- Konsep: INNER JOIN, LEFT JOIN, ANTI-JOIN (WHERE ... IS NULL)
-- =============================================================================

-- 3.1 INNER JOIN: Menghubungkan lowongan aktif dengan keahlian teknisnya
SELECT 
    j.role_group,
    s.skill_name,
    s.skill_category,
    COUNT(DISTINCT j.job_id) AS total_mentions
FROM jobs_master j
INNER JOIN skills_master s ON j.job_id = s.job_id
GROUP BY j.role_group, s.skill_name, s.skill_category
ORDER BY total_mentions DESC
LIMIT 10;

-- 3.2 ANTI-JOIN (LEFT JOIN + IS NULL): Mencari lowongan tanpa keahlian terdaftar
-- Khas interview: "Temukan data di tabel A yang tidak memiliki padanan di tabel B"
SELECT 
    j.job_id,
    j.title_raw,
    j.company_raw,
    j.role_group
FROM jobs_master j
LEFT JOIN skills_master s ON j.job_id = s.job_id
WHERE s.job_id IS NULL;


-- =============================================================================
-- BAGIAN 4: PENANGANAN NILAI NULL & LOGIKA KONDISIONAL
-- Konsep: IS NULL, COALESCE, NULLIF, CASE WHEN (Conditional Aggregation)
-- =============================================================================

-- 4.1 Penanganan NULL dengan COALESCE dan NULLIF
-- NULLIF mengembalikan NULL jika salary_min == salary_max (gaji flat)
SELECT 
    job_id,
    company_raw,
    COALESCE(TO_CHAR(salary_median, 'FM999,999,999'), 'Dirahasiakan') AS display_salary,
    NULLIF(salary_min, salary_max) AS variable_salary_min,
    CASE 
        WHEN salary_min = salary_max THEN 'Flat Salary'
        WHEN salary_min IS NOT NULL THEN 'Salary Range'
        ELSE 'Undisclosed'
    END AS salary_type
FROM jobs_master
LIMIT 10;

-- 4.2 Conditional Aggregation menggunakan CASE WHEN: Distribusi Mode Kerja per Sektor
SELECT 
    industry_category,
    COUNT(*) AS total_jobs,
    COUNT(CASE WHEN work_mode = 'On-site' THEN 1 END) AS on_site_jobs,
    COUNT(CASE WHEN work_mode = 'Hybrid' THEN 1 END) AS hybrid_jobs,
    COUNT(CASE WHEN work_mode = 'Remote' THEN 1 END) AS remote_jobs,
    ROUND(COUNT(CASE WHEN work_mode = 'Remote' THEN 1 END)::NUMERIC / COUNT(*) * 100, 1) AS remote_pct
FROM jobs_master
GROUP BY industry_category
ORDER BY total_jobs DESC;


-- =============================================================================
-- BAGIAN 5: WINDOW FUNCTIONS (PEMBEDA KANDIDAT JUARA)
-- Konsep: ROW_NUMBER(), RANK(), DENSE_RANK(), LAG(), LEAD(), SUM() OVER
-- =============================================================================

-- 5.1 Perbedaan ROW_NUMBER vs RANK vs DENSE_RANK (Pertanyaan Wajib Interview)
SELECT 
    job_id,
    company_raw,
    role_group,
    salary_median,
    ROW_NUMBER() OVER(PARTITION BY role_group ORDER BY salary_median DESC NULLS LAST) AS row_num,
    RANK() OVER(PARTITION BY role_group ORDER BY salary_median DESC NULLS LAST) AS rank_num,
    DENSE_RANK() OVER(PARTITION BY role_group ORDER BY salary_median DESC NULLS LAST) AS dense_rank_num
FROM jobs_master
WHERE is_salary_disclosed = TRUE AND role_group = 'Data Engineering'
LIMIT 10;

-- 5.2 LAG & LEAD: Menghitung Selisih Gaji terhadap Posisi Tepat di Atasnya
WITH ranked_bi AS (
    SELECT 
        company_raw,
        title_raw,
        salary_median,
        LAG(salary_median) OVER (ORDER BY salary_median DESC) AS higher_salary
    FROM jobs_master
    WHERE is_salary_disclosed = TRUE AND role_group = 'Data Analytics & BI'
    LIMIT 7
)
SELECT 
    company_raw,
    title_raw,
    salary_median,
    higher_salary,
    COALESCE(higher_salary - salary_median, 0) AS salary_gap_down
FROM ranked_bi;


-- =============================================================================
-- BAGIAN 6: SET OPERATIONS (UNION, UNION ALL, INTERSECT, EXCEPT)
-- Konsep: Membandingkan kumpulan skill antar profesi
-- =============================================================================

-- 6.1 INTERSECT: Keterampilan Teknis yang Beririsan antara Data Analyst dan Data Engineer
SELECT skill_name, 'Dibutuhkan Kedua Profesi' AS keterkaitan
FROM skills_master WHERE role_group = 'Data Analytics & BI'
INTERSECT
SELECT skill_name, 'Dibutuhkan Kedua Profesi' AS keterkaitan
FROM skills_master WHERE role_group = 'Data Engineering'
ORDER BY skill_name;

-- 6.2 EXCEPT: Keterampilan Khusus Data Engineering yang Tidak Dibutuhkan Data Analyst
SELECT skill_name AS skill_khusus_data_engineer
FROM skills_master WHERE role_group = 'Data Engineering'
EXCEPT
SELECT skill_name
FROM skills_master WHERE role_group = 'Data Analytics & BI'
ORDER BY skill_khusus_data_engineer;


-- =============================================================================
-- BAGIAN 7: BEDAH 5 SOAL PRAKTIK INTERVIEW TERPOPULER
-- =============================================================================

-- Soal 1: Cari Gaji Tertinggi Kedua Nasional (Second Highest Salary)
WITH salary_ranking AS (
    SELECT 
        company_raw,
        title_raw,
        role_group,
        salary_median,
        DENSE_RANK() OVER (ORDER BY salary_median DESC) AS rnk
    FROM jobs_master
    WHERE is_salary_disclosed = TRUE
)
SELECT *
FROM salary_ranking
WHERE rnk = 2;

-- Soal 2: Temukan Data Duplikat / Multiple Postings
SELECT 
    company_raw,
    title_raw,
    role_group,
    COUNT(*) AS total_postings
FROM jobs_master
GROUP BY company_raw, title_raw, role_group
HAVING COUNT(*) > 1
ORDER BY total_postings DESC;

-- Soal 3: Top 3 Keahlian Paling Dicari per Kelompok Profesi (Top N per Kategori)
WITH skill_ranks AS (
    SELECT 
        role_group,
        skill_name,
        skill_category,
        COUNT(DISTINCT job_id) AS demand_count,
        DENSE_RANK() OVER(PARTITION BY role_group ORDER BY COUNT(DISTINCT job_id) DESC) AS rank
    FROM skills_master
    GROUP BY role_group, skill_name, skill_category
)
SELECT role_group, rank, skill_name, skill_category, demand_count
FROM skill_ranks
WHERE rank <= 3
ORDER BY role_group, rank;

-- Soal 4: Running Total & Analisis Pareto Kebutuhan Keahlian
WITH ranked_skills AS (
    SELECT 
        skill_name,
        skill_category,
        COUNT(DISTINCT job_id) AS demand_count
    FROM skills_master
    GROUP BY skill_name, skill_category
    ORDER BY demand_count DESC
    LIMIT 10
)
SELECT 
    skill_name,
    skill_category,
    demand_count,
    SUM(demand_count) OVER (ORDER BY demand_count DESC, skill_name) AS running_total,
    ROUND(SUM(demand_count) OVER (ORDER BY demand_count DESC, skill_name)::NUMERIC / 
          (SELECT COUNT(*) FROM skills_master) * 100, 2) AS cumulative_pct
FROM ranked_skills;

-- Soal 5: Menghitung Selisih Gaji terhadap Rata-rata Profesi (Window Function vs Group Summary)
SELECT 
    job_id,
    company_raw,
    role_group,
    salary_median,
    ROUND(AVG(salary_median) OVER (PARTITION BY role_group), 0) AS avg_role_salary,
    ROUND(salary_median - AVG(salary_median) OVER (PARTITION BY role_group), 0) AS diff_from_role_avg
FROM jobs_master
WHERE is_salary_disclosed = TRUE
ORDER BY role_group, diff_from_role_avg DESC
LIMIT 10;
