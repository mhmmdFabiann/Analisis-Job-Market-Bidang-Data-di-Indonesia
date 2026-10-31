-- =============================================================================
-- Indonesian Data Job Market Intelligence - Analytical Views (PostgreSQL)
-- File: sql/views.sql
-- Description: View analitik untuk agregasi pasar kerja, distribusi gaji,
--              kebutuhan keterampilan teknis, dan penetrasi industri.
-- =============================================================================

-- 1. Ringkasan Gaji & Penyerapan Kerja per Kelompok Profesi Data
CREATE OR REPLACE VIEW v_role_salary_summary AS
SELECT 
    role_group,
    COUNT(*) AS total_jobs,
    COUNT(CASE WHEN is_salary_disclosed THEN 1 END) AS jobs_with_salary,
    ROUND(COUNT(CASE WHEN is_salary_disclosed THEN 1 END)::NUMERIC / COUNT(*) * 100, 2) AS salary_disclosure_pct,
    ROUND(MIN(salary_min), 0) AS min_salary_lowest,
    ROUND(AVG(salary_median), 0) AS avg_salary_median,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY salary_median)::NUMERIC, 0) AS median_salary_overall,
    ROUND(MAX(salary_max), 0) AS max_salary_highest
FROM jobs_master
GROUP BY role_group
ORDER BY total_jobs DESC;

-- 2. Top Keterampilan Teknis Nasional (Persentase Kebutuhan dari Seluruh Lowongan)
CREATE OR REPLACE VIEW v_top_skills_overall AS
SELECT 
    s.skill_name,
    s.skill_category,
    COUNT(DISTINCT s.job_id) AS job_count,
    ROUND(COUNT(DISTINCT s.job_id)::NUMERIC / (SELECT COUNT(*) FROM jobs_master) * 100, 2) AS demand_percentage
FROM skills_master s
GROUP BY s.skill_name, s.skill_category
ORDER BY job_count DESC;

-- 3. Top Keterampilan Teknis Berdasarkan Peran Profesi (Skill Demands by Role Group)
CREATE OR REPLACE VIEW v_skills_by_role AS
SELECT 
    s.role_group,
    s.skill_name,
    s.skill_category,
    COUNT(DISTINCT s.job_id) AS demand_count,
    ROUND(COUNT(DISTINCT s.job_id)::NUMERIC / j.total_role_jobs * 100, 2) AS demand_percentage_in_role
FROM skills_master s
JOIN (
    SELECT role_group, COUNT(*) AS total_role_jobs 
    FROM jobs_master 
    GROUP BY role_group
) j ON s.role_group = j.role_group
GROUP BY s.role_group, s.skill_name, s.skill_category, j.total_role_jobs
ORDER BY s.role_group, demand_count DESC;

-- 4. Distribusi Sektor Industri Terhadap Kebutuhan Talenta Data & Rerata Gaji
CREATE OR REPLACE VIEW v_industry_role_summary AS
SELECT 
    industry_category,
    COUNT(*) AS total_jobs,
    COUNT(CASE WHEN role_group = 'Data Analytics & BI' THEN 1 END) AS data_analyst_jobs,
    COUNT(CASE WHEN role_group = 'Data Engineering' THEN 1 END) AS data_engineer_jobs,
    COUNT(CASE WHEN role_group = 'Data Science' THEN 1 END) AS data_science_jobs,
    COUNT(CASE WHEN role_group = 'Machine Learning & AI' THEN 1 END) AS ml_ai_jobs,
    ROUND(AVG(salary_median), 0) AS avg_disclosed_salary
FROM jobs_master
GROUP BY industry_category
ORDER BY total_jobs DESC;
