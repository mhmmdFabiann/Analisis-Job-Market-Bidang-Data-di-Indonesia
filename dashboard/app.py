import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

from utils import (
    load_data,
    format_rupiah,
    format_rupiah_singkat,
    format_percent,
    PROJECT_ROOT
)

# ==============================================================================
# 1. KONFIGURASI HALAMAN & TEMA VISUAL (STREAMLIT SET_PAGE_CONFIG)
# ==============================================================================
st.set_page_config(
    page_title="Indonesian Data Job Market Intelligence",
    page_icon="🇮🇩",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Skema Palet Warna Korporat & Konsisten
PRIMARY_COLOR = "#1E3A8A"     # Deep Blue
SECONDARY_COLOR = "#0D9488"   # Teal
ACCENT_BLUE = "#3B82F6"       # Electric Blue
ACCENT_ORANGE = "#F59E0B"     # Amber
ACCENT_PURPLE = "#8B5CF6"     # Purple
ACCENT_GREEN = "#10B981"      # Emerald
BG_CARD = "#F8FAFC"           # Light Slate Surface

ROLE_COLORS = {
    "Data Analytics & BI": "#3B82F6",
    "Data Engineering": "#10B981",
    "Data Science": "#8B5CF6",
    "Machine Learning & AI": "#F59E0B"
}

# Custom CSS untuk Kartu KPI, Spasi, dan Aksesibilitas
st.markdown("""
<style>
    /* Styling Container Metrik */
    .metric-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 20px 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-bottom: 12px;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08);
    }
    .metric-label {
        font-size: 0.85rem;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 6px;
    }
    .metric-value {
        font-size: 1.85rem;
        font-weight: 800;
        color: #0f172a;
        line-height: 1.2;
    }
    .metric-subtext {
        font-size: 0.8rem;
        color: #94a3b8;
        margin-top: 6px;
    }
    .metric-badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .badge-blue { background-color: #dbeafe; color: #1e40af; }
    .badge-green { background-color: #dcfce7; color: #166534; }
    .badge-orange { background-color: #fef3c7; color: #92400e; }
    
    /* Header & Tagline */
    .dashboard-title {
        font-size: 2.1rem;
        font-weight: 800;
        color: #0f172a;
        margin-bottom: 2px;
    }
    .dashboard-subtitle {
        font-size: 1rem;
        color: #475569;
        margin-bottom: 20px;
    }
    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 18px;
        border-radius: 8px 8px 0px 0px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# 2. MEMUAT DATASET DENGAN CACHING
# ==============================================================================
@st.cache_data(ttl=3600)
def get_cached_data():
    df_j, df_s, src = load_data()
    if df_j is None or df_j.empty:
        raise ValueError("Dataset lowongan pekerjaan (jobs_master) tidak berhasil dimuat.")
    return df_j, df_s, src

try:
    df_jobs_raw, df_skills_raw, data_source_name = get_cached_data()
except Exception as e:
    st.error(f"❌ **Gagal Memuat Dataset:** {e}")
    st.info("Pastikan file data tersedia di repositori. Silakan refresh halaman.")
    st.stop()

if df_jobs_raw is None or df_jobs_raw.empty:
    st.warning("⚠️ Dataset pekerjaan kosong.")
    st.stop()


# ==============================================================================
# 3. SIDEBAR: KONTROL FILTER & DATA FRESHNESS
# ==============================================================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2920/2920349.png", width=64)
    st.title("Filter Analisis")
    st.caption("Sesuaikan parameter eksplorasi data:")

    # 1. Filter Platform Sumber
    sources_available = ["Semua Platform"] + sorted([str(s) for s in df_jobs_raw["source"].dropna().unique()])
    selected_source = st.selectbox("🌐 Platform Sumber", sources_available)

    # 2. Filter Kelompok Profesi (Role Group)
    roles_available = sorted([str(r) for r in df_jobs_raw["role_group"].dropna().unique()])
    selected_roles = st.multiselect("💼 Kelompok Profesi", roles_available, default=roles_available)

    # 3. Filter Sektor Industri
    industries_available = sorted([str(i) for i in df_jobs_raw["industry_category"].dropna().unique()])
    selected_industries = st.multiselect("🏢 Sektor Industri", industries_available, default=industries_available)

    # 4. Filter Mode Kerja
    work_modes_available = sorted([str(w) for w in df_jobs_raw["work_mode"].dropna().unique()])
    selected_work_modes = st.multiselect("💻 Mode Kerja", work_modes_available, default=work_modes_available)

    # 5. Filter Jenjang Pengalaman
    exp_available = sorted([str(e) for e in df_jobs_raw["experience_level"].dropna().unique()])
    selected_exp = st.multiselect("🎓 Jenjang Pengalaman", exp_available, default=exp_available)

    # 6. Filter Rentang Gaji (Hanya lowongan dengan gaji terbuka)
    salary_series = df_jobs_raw[df_jobs_raw["is_salary_disclosed"]]["salary_median"]
    min_sal = int(salary_series.min() / 1_000_000) if not salary_series.empty else 1
    max_sal = int(salary_series.max() / 1_000_000) if not salary_series.empty else 40
    
    selected_salary_range = st.slider(
        "💵 Rentang Gaji (Juta Rupiah)",
        min_value=min_sal,
        max_value=max_sal,
        value=(min_sal, max_sal),
        step=1,
        help="Memfilter lowongan dengan informasi gaji terbuka sesuai rentang nilai median."
    )

    st.divider()
    
    # Metadata & Data Freshness
    st.caption("ℹ️ **Informasi Sumber Data:**")
    st.markdown(f"- **Koneksi:** `{data_source_name}`")
    st.markdown(f"- **Total Koleksi:** `{len(df_jobs_raw)} lowongan`")
    if "collected_at" in df_jobs_raw.columns and not df_jobs_raw["collected_at"].dropna().empty:
        latest_date = df_jobs_raw["collected_at"].max().strftime("%d %b %Y, %H:%M WIB")
        st.markdown(f"- **Pembaruan:** `{latest_date}`")
        
    st.caption("Dirancang berdasarkan prinsip *Visual Hierarchy*, *Grid Alignment*, dan *Cognitive Load Reduction*.")


# ==============================================================================
# 4. FILTERING DATASET DINAMIS
# ==============================================================================
df_jobs = df_jobs_raw.copy()

if selected_source != "Semua Platform":
    df_jobs = df_jobs[df_jobs["source"] == selected_source]

if selected_roles:
    df_jobs = df_jobs[df_jobs["role_group"].isin(selected_roles)]
else:
    df_jobs = df_jobs.iloc[0:0]

if selected_industries:
    df_jobs = df_jobs[df_jobs["industry_category"].isin(selected_industries)]
else:
    df_jobs = df_jobs.iloc[0:0]

if selected_work_modes:
    df_jobs = df_jobs[df_jobs["work_mode"].isin(selected_work_modes)]
else:
    df_jobs = df_jobs.iloc[0:0]

if selected_exp:
    df_jobs = df_jobs[df_jobs["experience_level"].isin(selected_exp)]
else:
    df_jobs = df_jobs.iloc[0:0]

# Filter gaji (hanya mengecualikan yang di luar batas jika gajinya tertera)
sal_min_val = selected_salary_range[0] * 1_000_000
sal_max_val = selected_salary_range[1] * 1_000_000
df_jobs = df_jobs[
    (~df_jobs["is_salary_disclosed"]) | 
    ((df_jobs["salary_median"] >= sal_min_val) & (df_jobs["salary_median"] <= sal_max_val))
]

# Sinkronkan dataset skills_master dengan jobs yang lolos filter
df_skills = df_skills_raw[df_skills_raw["job_id"].isin(df_jobs["job_id"])].copy()


# ==============================================================================
# 5. HEADER UTAMA DASHBOARD
# ==============================================================================
col_head1, col_head2 = st.columns([4, 1])
with col_head1:
    st.markdown('<div class="dashboard-title">🇮🇩 Indonesian Data Job Market Intelligence</div>', unsafe_allow_html=True)
    st.markdown('<div class="dashboard-subtitle">Dashboard Interaktif Analisis Pasar Kerja Talenta Data Indonesia (Glints & JobStreet)</div>', unsafe_allow_html=True)

with col_head2:
    st.markdown(
        f'<div style="text-align: right; padding-top: 10px;">'
        f'<span class="metric-badge badge-blue">{len(df_jobs)} / {len(df_jobs_raw)} Lowongan Aktif</span>'
        f'</div>',
        unsafe_allow_html=True
    )

# Peringatan bila data kosong karena filter terlalu ketat
if df_jobs.empty:
    st.warning("⚠️ Tidak ada lowongan yang sesuai dengan kombinasi filter yang dipilih. Silakan sesuaikan kembali filter di sidebar.")
    st.stop()


# ==============================================================================
# 6. TAB NAVIGASI UTAMA
# ==============================================================================
tab_overview, tab_salary, tab_skills, tab_regional, tab_explorer = st.tabs([
    "📊 Ringkasan Eksekutif",
    "💰 Analisis Gaji & Kompensasi",
    "🛠️ Kebutuhan Keahlian & Teknologi",
    "🗺️ Sebaran Geografis & Industri",
    "🔍 Eksplorasi Data Lowongan"
])


# ==============================================================================
# TAB 1: RINGKASAN EKSEKUTIF (EXECUTIVE OVERVIEW)
# ==============================================================================
with tab_overview:
    # --- Tingkat 1: KPI Cards (Visual Hierarchy Utama) ---
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

    total_jobs = len(df_jobs)
    disclosed_jobs = df_jobs[df_jobs["is_salary_disclosed"]]
    disclosure_rate = (len(disclosed_jobs) / total_jobs * 100) if total_jobs > 0 else 0
    median_national_sal = disclosed_jobs["salary_median"].median() if not disclosed_jobs.empty else 0
    avg_national_sal = disclosed_jobs["salary_median"].mean() if not disclosed_jobs.empty else 0
    total_skills_mapped = len(df_skills)

    with kpi_col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Lowongan Terdata</div>
            <div class="metric-value">{total_jobs:,}</div>
            <div class="metric-subtext">Dari {len(df_jobs_raw)} total populasi data</div>
        </div>
        """.replace(",", "."), unsafe_allow_html=True)

    with kpi_col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Median Gaji Nasional</div>
            <div class="metric-value">{format_rupiah_singkat(median_national_sal)}</div>
            <div class="metric-subtext">Rata-rata: {format_rupiah_singkat(avg_national_sal)}</div>
        </div>
        """, unsafe_allow_html=True)

    with kpi_col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Transparansi Gaji</div>
            <div class="metric-value">{format_percent(disclosure_rate)}</div>
            <div class="metric-subtext">{len(disclosed_jobs)} lowongan mencantumkan gaji</div>
        </div>
        """, unsafe_allow_html=True)

    with kpi_col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Keahlian Teknis Mapped</div>
            <div class="metric-value">{total_skills_mapped:,}</div>
            <div class="metric-subtext">Rerata {df_jobs['skills_count'].mean():.1f} skill / lowongan</div>
        </div>
        """.replace(",", "."), unsafe_allow_html=True)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # --- Tingkat 2: Visualisasi Tren & Distribusi Komposisi ---
    row2_col1, row2_col2 = st.columns([1, 1])

    with row2_col1:
        st.subheader("Distribusi Lowongan per Kelompok Profesi")
        st.caption("Pangsa pasar lowongan berdasarkan kelompok profesi data dan platform sumber.")
        
        df_role_src = df_jobs.groupby(["role_group", "source"]).size().reset_index(name="count")
        fig_role = px.bar(
            df_role_src,
            x="role_group",
            y="count",
            color="source",
            barmode="group",
            text="count",
            color_discrete_map={"Glints": ACCENT_BLUE, "JobStreet": SECONDARY_COLOR},
            labels={"role_group": "Kelompok Profesi", "count": "Jumlah Lowongan", "source": "Platform"}
        )
        fig_role.update_traces(textposition="outside")
        fig_role.update_layout(
            margin=dict(l=20, r=20, t=20, b=40),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="#f1f5f9")
        )
        st.plotly_chart(fig_role, use_container_width=True)

    with row2_col2:
        st.subheader("Penyerapan Talenta per Sektor Industri")
        st.caption("Sektor industri dengan pembukaan lowongan data terbanyak di Indonesia.")
        
        df_ind = df_jobs["industry_category"].value_counts().reset_index()
        df_ind.columns = ["industry_category", "count"]
        fig_ind = px.bar(
            df_ind.sort_values("count", ascending=True),
            x="count",
            y="industry_category",
            orientation="h",
            text="count",
            color="count",
            color_continuous_scale="Teal",
            labels={"count": "Lowongan", "industry_category": "Sektor Industri"}
        )
        fig_ind.update_traces(textposition="outside")
        fig_ind.update_layout(
            margin=dict(l=20, r=20, t=20, b=40),
            coloraxis_showscale=False,
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=True, gridcolor="#f1f5f9"),
            yaxis=dict(showgrid=False)
        )
        st.plotly_chart(fig_ind, use_container_width=True)

    # --- Baris 3: Mode Kerja & Jenjang Pengalaman ---
    row3_col1, row3_col2 = st.columns([1, 1])
    with row3_col1:
        st.subheader("Proporsi Pengaturan Kerja (Work Mode)")
        df_wm = df_jobs["work_mode"].value_counts().reset_index()
        df_wm.columns = ["work_mode", "count"]
        fig_wm = px.pie(
            df_wm,
            names="work_mode",
            values="count",
            hole=0.45,
            color_discrete_sequence=["#3B82F6", "#10B981", "#F59E0B", "#94A3B8"]
        )
        fig_wm.update_traces(textinfo="percent+label")
        fig_wm.update_layout(margin=dict(l=20, r=20, t=20, b=20), showlegend=False)
        st.plotly_chart(fig_wm, use_container_width=True)

    with row3_col2:
        st.subheader("Distribusi Jenjang Pengalaman")
        df_exp = df_jobs["experience_level"].value_counts().reset_index()
        df_exp.columns = ["experience_level", "count"]
        fig_exp = px.bar(
            df_exp,
            x="experience_level",
            y="count",
            text="count",
            color="experience_level",
            color_discrete_sequence=px.colors.qualitative.Safe,
            labels={"experience_level": "Jenjang Pengalaman", "count": "Jumlah Lowongan"}
        )
        fig_exp.update_traces(textposition="outside")
        fig_exp.update_layout(margin=dict(l=20, r=20, t=20, b=20), showlegend=False, plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_exp, use_container_width=True)


# ==============================================================================
# TAB 2: ANALISIS GAJI & KOMPENSASI (SALARY INTELLIGENCE)
# ==============================================================================
with tab_salary:
    st.subheader("💵 Analisis Struktur Kompensasi & Gaji Talenta Data")
    st.caption("Eksplorasi penawaran gaji bulanan yang telah dinormalisasi ke mata uang Rupiah.")

    if disclosed_jobs.empty:
        st.info("Tidak ada data gaji yang tersedia untuk kombinasi filter yang dipilih.")
    else:
        # Metrik Gaji Spesifik
        sal_c1, sal_c2, sal_c3, sal_c4 = st.columns(4)
        with sal_c1:
            st.metric("Gaji Terendah (Min)", format_rupiah(disclosed_jobs["salary_min"].min()))
        with sal_c2:
            st.metric("Median Gaji Nasional", format_rupiah(disclosed_jobs["salary_median"].median()))
        with sal_c3:
            st.metric("Rerata Gaji Nasional", format_rupiah(disclosed_jobs["salary_median"].mean()))
        with sal_c4:
            st.metric("Gaji Tertinggi (Max)", format_rupiah(disclosed_jobs["salary_max"].max()))

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

        sal_row1, sal_row2 = st.columns(2)
        with sal_row1:
            st.markdown("##### Sebaran Gaji per Kelompok Profesi (Box Plot)")
            df_sal_box = disclosed_jobs.copy()
            df_sal_box["salary_juta"] = df_sal_box["salary_median"] / 1_000_000
            
            fig_box = px.box(
                df_sal_box,
                x="role_group",
                y="salary_juta",
                color="role_group",
                color_discrete_map=ROLE_COLORS,
                points="all",
                labels={"role_group": "Profesi", "salary_juta": "Gaji Median (Juta IDR)"}
            )
            fig_box.update_layout(
                showlegend=False,
                margin=dict(l=20, r=20, t=20, b=40),
                plot_bgcolor="rgba(0,0,0,0)",
                yaxis=dict(showgrid=True, gridcolor="#f1f5f9")
            )
            st.plotly_chart(fig_box, use_container_width=True)

        with sal_row2:
            st.markdown("##### Median Gaji per Jenjang Pengalaman")
            df_exp_sal = disclosed_jobs.groupby("experience_level")["salary_median"].agg(["median", "count"]).reset_index()
            df_exp_sal["median_juta"] = df_exp_sal["median"] / 1_000_000
            df_exp_sal = df_exp_sal.sort_values("median_juta", ascending=True)

            fig_exp_sal = px.bar(
                df_exp_sal,
                x="median_juta",
                y="experience_level",
                orientation="h",
                text=df_exp_sal["median_juta"].apply(lambda v: f"Rp {v:.1f} Jt"),
                color="median_juta",
                color_continuous_scale="Blues",
                labels={"experience_level": "Jenjang", "median_juta": "Median (Juta IDR)"}
            )
            fig_exp_sal.update_traces(textposition="outside")
            fig_exp_sal.update_layout(
                coloraxis_showscale=False,
                margin=dict(l=20, r=20, t=20, b=40),
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(showgrid=True, gridcolor="#f1f5f9")
            )
            st.plotly_chart(fig_exp_sal, use_container_width=True)

        # Baris 2: Gaji per Sektor Industri
        st.markdown("##### Rata-rata dan Rentang Gaji per Sektor Industri")
        df_ind_sal = disclosed_jobs.groupby("industry_category")["salary_median"].agg(
            Rata_Rata="mean",
            Median="median",
            Minimum="min",
            Maksimum="max",
            Jumlah_Lowongan="count"
        ).reset_index().sort_values("Median", ascending=False)

        # Format mata uang untuk tabel presentasi
        df_ind_sal_disp = df_ind_sal.copy()
        df_ind_sal_disp["Rata_Rata"] = df_ind_sal_disp["Rata_Rata"].apply(format_rupiah)
        df_ind_sal_disp["Median"] = df_ind_sal_disp["Median"].apply(format_rupiah)
        df_ind_sal_disp["Minimum"] = df_ind_sal_disp["Minimum"].apply(format_rupiah)
        df_ind_sal_disp["Maksimum"] = df_ind_sal_disp["Maksimum"].apply(format_rupiah)
        
        st.dataframe(
            df_ind_sal_disp.rename(columns={"industry_category": "Sektor Industri"}),
            use_container_width=True,
            hide_index=True
        )


# ==============================================================================
# TAB 3: KEBUTUHAN KEAHLIAN & TEKNOLOGI (SKILLS INTELLIGENCE)
# ==============================================================================
with tab_skills:
    st.subheader("🛠️ Peta Kebutuhan Keterampilan Teknis & Tools Data")
    st.caption("Frekuensi dan tingkat penetrasi keahlian teknis yang paling dicari perusahaan.")

    if df_skills.empty:
        st.info("Tidak ada data keahlian teknis yang cocok dengan filter yang dipilih.")
    else:
        # Filter lokal kategori skill
        skill_cats = ["Semua Kategori"] + sorted(df_skills["skill_category"].dropna().unique().tolist())
        selected_cat = st.selectbox("📂 Filter Kategori Keahlian:", skill_cats)

        df_skills_filtered = df_skills if selected_cat == "Semua Kategori" else df_skills[df_skills["skill_category"] == selected_cat]

        sk_col1, sk_col2 = st.columns([1, 1])

        with sk_col1:
            st.markdown("##### Top 15 Keahlian Teknis Paling Dicari")
            skill_counts = df_skills_filtered.groupby(["skill_name", "skill_category"]).size().reset_index(name="job_count")
            skill_counts["penetration_pct"] = (skill_counts["job_count"] / len(df_jobs) * 100).round(1)
            top15_skills = skill_counts.sort_values("job_count", ascending=False).head(15)

            fig_top_skills = px.bar(
                top15_skills.sort_values("job_count", ascending=True),
                x="job_count",
                y="skill_name",
                orientation="h",
                text=top15_skills.sort_values("job_count", ascending=True)["penetration_pct"].apply(lambda v: f"{v}%"),
                color="skill_category",
                color_discrete_sequence=px.colors.qualitative.Bold,
                labels={"job_count": "Jumlah Lowongan", "skill_name": "Nama Skill", "skill_category": "Kategori"}
            )
            fig_top_skills.update_traces(textposition="outside")
            fig_top_skills.update_layout(
                margin=dict(l=20, r=20, t=20, b=40),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(showgrid=True, gridcolor="#f1f5f9")
            )
            st.plotly_chart(fig_top_skills, use_container_width=True)

        with sk_col2:
            st.markdown("##### Komposisi Kategori Keahlian")
            cat_counts = df_skills.groupby("skill_category").size().reset_index(name="count")
            fig_cat = px.pie(
                cat_counts,
                names="skill_category",
                values="count",
                hole=0.45,
                color_discrete_sequence=px.colors.qualitative.Safe
            )
            fig_cat.update_traces(textinfo="percent+label")
            fig_cat.update_layout(margin=dict(l=20, r=20, t=20, b=20), showlegend=False)
            st.plotly_chart(fig_cat, use_container_width=True)

        # Analisis Matriks Skill per Role Group
        st.markdown("##### Matriks Kebutuhan Skill Kunci per Kelompok Profesi")
        top_overall_names = df_skills["skill_name"].value_counts().head(12).index.tolist()
        df_matrix = df_skills[df_skills["skill_name"].isin(top_overall_names)].groupby(
            ["skill_name", "role_group"]
        ).size().unstack(fill_value=0)

        fig_matrix = px.imshow(
            df_matrix,
            labels=dict(x="Kelompok Profesi", y="Keahlian Teknis", color="Frekuensi"),
            x=df_matrix.columns,
            y=df_matrix.index,
            color_continuous_scale="YlGnBu",
            text_auto=True,
            aspect="auto"
        )
        fig_matrix.update_layout(margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig_matrix, use_container_width=True)


# ==============================================================================
# TAB 4: SEBARAN GEOGRAFIS & INDUSTRI (REGIONAL INTELLIGENCE)
# ==============================================================================
with tab_regional:
    st.subheader("🗺️ Sebaran Geografis & Konsentrasi Industri")
    st.caption("Pemetaan konsentrasi peluang karir data di berbagai wilayah Indonesia.")

    reg_col1, reg_col2 = st.columns([1, 1])

    with reg_col1:
        st.markdown("##### Konsentrasi Lowongan per Provinsi")
        df_prov = df_jobs["province"].value_counts().reset_index()
        df_prov.columns = ["province", "count"]
        df_prov["pct"] = (df_prov["count"] / len(df_jobs) * 100).round(1)

        fig_prov = px.bar(
            df_prov.head(10).sort_values("count", ascending=True),
            x="count",
            y="province",
            orientation="h",
            text=df_prov.head(10).sort_values("count", ascending=True)["pct"].apply(lambda v: f"{v}%"),
            color="count",
            color_continuous_scale="Purples",
            labels={"count": "Lowongan", "province": "Provinsi"}
        )
        fig_prov.update_traces(textposition="outside")
        fig_prov.update_layout(
            coloraxis_showscale=False,
            margin=dict(l=20, r=20, t=20, b=40),
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=True, gridcolor="#f1f5f9")
        )
        st.plotly_chart(fig_prov, use_container_width=True)

    with reg_col2:
        st.markdown("##### Top 10 Kota Perekrut Terbesar")
        df_city = df_jobs["city"].value_counts().reset_index()
        df_city.columns = ["city", "count"]

        fig_city = px.bar(
            df_city.head(10).sort_values("count", ascending=True),
            x="count",
            y="city",
            orientation="h",
            text="count",
            color="count",
            color_continuous_scale="Tealgrn",
            labels={"count": "Lowongan", "city": "Kota / Kabupaten"}
        )
        fig_city.update_traces(textposition="outside")
        fig_city.update_layout(
            coloraxis_showscale=False,
            margin=dict(l=20, r=20, t=20, b=40),
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=True, gridcolor="#f1f5f9")
        )
        st.plotly_chart(fig_city, use_container_width=True)

    # Matriks Industri vs Mode Kerja
    st.markdown("##### Distribusi Mode Kerja Berdasarkan Sektor Industri")
    df_ind_wm = df_jobs.groupby(["industry_category", "work_mode"]).size().reset_index(name="count")
    fig_ind_wm = px.bar(
        df_ind_wm,
        x="industry_category",
        y="count",
        color="work_mode",
        barmode="stack",
        labels={"industry_category": "Sektor Industri", "count": "Jumlah Lowongan", "work_mode": "Mode Kerja"},
        color_discrete_sequence=["#3B82F6", "#10B981", "#F59E0B", "#94A3B8"]
    )
    fig_ind_wm.update_layout(
        margin=dict(l=20, r=20, t=20, b=60),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, tickangle=-25),
        yaxis=dict(showgrid=True, gridcolor="#f1f5f9")
    )
    st.plotly_chart(fig_ind_wm, use_container_width=True)


# ==============================================================================
# TAB 5: EKSPLORASI DATA LOWONGAN (DATA EXPLORER & DRILL-DOWN)
# ==============================================================================
with tab_explorer:
    st.subheader("🔍 Penelusuran Detail Lowongan & Unduh Data")
    st.caption("Telusuri baris data granular atau unduh dataset hasil filter untuk analisis lanjutan.")

    search_query = st.text_input(
        "🔎 Cari berdasarkan posisi atau nama perusahaan:",
        placeholder="Contoh: Data Analyst, Tokopedia, Bank Mandiri, Python..."
    )

    df_display = df_jobs.copy()
    if search_query:
        mask = (
            df_display["title_raw"].str.contains(search_query, case=False, na=False) |
            df_display["company_raw"].str.contains(search_query, case=False, na=False) |
            df_display["city"].str.contains(search_query, case=False, na=False)
        )
        df_display = df_display[mask]

    col_btn1, col_btn2 = st.columns([3, 1])
    with col_btn1:
        st.markdown(f"Menampilkan **{len(df_display)}** lowongan yang sesuai.")
    with col_btn2:
        # Fitur Ekspor CSV
        csv_data = df_display.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Unduh Data CSV",
            data=csv_data,
            file_name=f"loker_data_filtered_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True
        )

    # Format Tampilan Tabel Bersih
    preview_cols = [
        "source", "title_raw", "company_raw", "role_group", 
        "industry_category", "province", "city", "work_mode", 
        "experience_level", "salary_median", "skills_count", "job_url"
    ]
    df_preview = df_display[preview_cols].copy()
    df_preview["salary_median"] = df_preview["salary_median"].apply(format_rupiah)
    
    st.dataframe(
        df_preview.rename(columns={
            "source": "Platform",
            "title_raw": "Posisi",
            "company_raw": "Perusahaan",
            "role_group": "Kelompok Profesi",
            "industry_category": "Industri",
            "province": "Provinsi",
            "city": "Kota",
            "work_mode": "Mode Kerja",
            "experience_level": "Pengalaman",
            "salary_median": "Gaji Median",
            "skills_count": "Jml Skill",
            "job_url": "Tautan Lowongan"
        }),
        column_config={
            "Tautan Lowongan": st.column_config.LinkColumn("Buka Lowongan", display_text="Lihat Detail 🔗")
        },
        use_container_width=True,
        hide_index=True
    )

    # Panel Rincian Keahlian Teknis per Lowongan
    if not df_display.empty:
        with st.expander("📌 Lihat Daftar Keahlian Teknis untuk Lowongan Tertentu"):
            selected_job_title = st.selectbox(
                "Pilih lowongan untuk melihat keahlian teknis terkait:",
                df_display["title_raw"] + " - " + df_display["company_raw"] + " (" + df_display["job_id"] + ")"
            )
            sel_job_id = selected_job_title.split("(")[-1].replace(")", "").strip()
            
            job_skills = df_skills[df_skills["job_id"] == sel_job_id]
            if not job_skills.empty:
                st.write(f"Keahlian teknis yang dibutuhkan untuk **{selected_job_title}**:")
                badges_html = " ".join([
                    f"<span style='background-color:#e0f2fe; color:#0369a1; padding:4px 10px; border-radius:12px; margin:4px; display:inline-block; font-weight:600; font-size:0.85rem;'>{row['skill_name']} <small style='color:#64748b;'>({row['skill_category']})</small></span>"
                    for _, row in job_skills.iterrows()
                ])
                st.markdown(badges_html, unsafe_allow_html=True)
            else:
                st.info("Tidak ada keterampilan spesifik yang diekstrak untuk lowongan ini.")


# ==============================================================================
# FOOTER DASHBOARD
# ==============================================================================
st.divider()
st.markdown(
    """
    <div style="text-align: center; color: #94a3b8; font-size: 0.85rem; padding: 10px;">
        Indonesian Data Job Market Intelligence © 2026 | Dibangun dengan Streamlit & Plotly berdasarkan <i>Panduan Komprehensif Perancangan Dashboard</i>
    </div>
    """,
    unsafe_allow_html=True
)
