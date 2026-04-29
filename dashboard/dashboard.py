"""
Dashboard Analisis Bike Sharing — Capital Bikeshare D.C. (2011–2012)
Streamlit Dashboard
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Bike Sharing Analytics",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 12px;
        color: white;
        text-align: center;
    }
    .metric-card h2 { font-size: 2rem; margin: 0; }
    .metric-card p  { margin: 4px 0 0; opacity: 0.85; font-size: 0.9rem; }
    .section-header {
        border-left: 5px solid #667eea;
        padding-left: 12px;
        margin-top: 1.5rem;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# ── Data Loading ───────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    day_df  = pd.read_csv("dashboard/main_data.csv")
    hour_df = pd.read_csv("dashboard/main_data_hour.csv")

    for df in [day_df, hour_df]:
        df["dteday"] = pd.to_datetime(df["dteday"])
        df["season_label"]  = df["season"].map({1:"Spring",2:"Summer",3:"Fall",4:"Winter"})
        df["weather_label"] = df["weathersit"].map({
            1:"Clear/Partly Cloudy",2:"Mist/Cloudy",
            3:"Light Rain/Snow",4:"Heavy Rain/Snow"})
        df["weekday_label"] = df["weekday"].map(
            {0:"Sun",1:"Mon",2:"Tue",3:"Wed",4:"Thu",5:"Fri",6:"Sat"})
        df["year_label"]   = df["yr"].map({0:"2011",1:"2012"})
        df["day_type"]     = df["workingday"].map({1:"Hari Kerja",0:"Akhir Pekan/Libur"})

    # Clustering kolom pada day_df
    day_df["casual_ratio"] = day_df["casual"] / day_df["cnt"]
    bins_cnt = [0, 2000, 4000, 6000, 10000]
    labels_cnt = ["Low (<2K)","Medium (2K–4K)","High (4K–6K)","Very High (>6K)"]
    day_df["usage_cluster"] = pd.cut(day_df["cnt"], bins=bins_cnt, labels=labels_cnt)

    bins_ratio = [0, 0.15, 0.30, 1.0]
    labels_ratio = ["Registered-Dominant","Mixed","Casual-Dominant"]
    day_df["user_type_cluster"] = pd.cut(day_df["casual_ratio"],
                                         bins=bins_ratio, labels=labels_ratio)
    return day_df, hour_df

day_df, hour_df = load_data()

# ── Sidebar ────────────────────────────────────────────────────────────────────
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/1/13/Capital_Bikeshare_logo.svg/320px-Capital_Bikeshare_logo.svg.png",
                 use_column_width=True)
st.sidebar.title("Filter Data")

year_filter = st.sidebar.multiselect(
    "Tahun", options=["2011","2012"], default=["2011","2012"])
season_filter = st.sidebar.multiselect(
    "Musim", options=["Spring","Summer","Fall","Winter"],
    default=["Spring","Summer","Fall","Winter"])
weather_filter = st.sidebar.multiselect(
    "Kondisi Cuaca",
    options=["Clear/Partly Cloudy","Mist/Cloudy","Light Rain/Snow"],
    default=["Clear/Partly Cloudy","Mist/Cloudy","Light Rain/Snow"])

# Apply filter
day_filtered = day_df[
    day_df["year_label"].isin(year_filter) &
    day_df["season_label"].isin(season_filter) &
    day_df["weather_label"].isin(weather_filter)
]
hour_filtered = hour_df[
    hour_df["year_label"].isin(year_filter) &
    hour_df["season_label"].isin(season_filter) &
    hour_df["weather_label"].isin(weather_filter)
]

# ── Header ─────────────────────────────────────────────────────────────────────
st.title("Dashboard Analisis Bike Sharing")
st.caption("Data: 2011–2012")
st.markdown("---")

# ── KPI Cards ──────────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
total_rentals   = day_filtered["cnt"].sum()
avg_daily       = day_filtered["cnt"].mean()
total_casual    = day_filtered["casual"].sum()
total_registered= day_filtered["registered"].sum()

with col1:
    st.metric("Total Penyewaan", f"{total_rentals:,.0f}", help="Total penyewaan sepeda (filtered)")
with col2:
    st.metric("Rata-rata Harian", f"{avg_daily:,.0f}", help="Rata-rata penyewaan per hari")
with col3:
    st.metric("Casual Users", f"{total_casual:,.0f}",
              delta=f"{total_casual/total_rentals*100:.1f}% dari total")
with col4:
    st.metric("Registered Users", f"{total_registered:,.0f}",
              delta=f"{total_registered/total_rentals*100:.1f}% dari total")

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB LAYOUT
# ═══════════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4 = st.tabs([
    "Pertanyaan 1: Pola Per Jam",
    "Pertanyaan 2: Cuaca & Musim",
    "Analisis Lanjutan",
    "Data & Insight"
])

# ──────────────────────────────────────────────────────────────────────────────
# TAB 1 — Pola Per Jam
# ──────────────────────────────────────────────────────────────────────────────
with tab1:
    st.markdown("""
    <div class='section-header'>
        <h3>Pertanyaan Bisnis 1</h3>
    </div>
    <p><em>Bagaimana pola rata-rata penyewaan sepeda per jam berdasarkan hari
    (hari kerja vs. libur) dan pada jam berapa terjadi
    puncak penyewaan di masing-masing kategori?</em></p>
    """, unsafe_allow_html=True)

    hourly_pattern = (hour_filtered
                      .groupby(["hr","day_type"])[["casual","registered","cnt"]]
                      .mean()
                      .reset_index())

    # Peak info
    for day_type in ["Hari Kerja","Libur"]:
        sub = hourly_pattern[hourly_pattern["day_type"] == day_type]
        if sub.empty: continue
        peak = sub.loc[sub["cnt"].idxmax()]
        st.info(f"**{day_type}** — Puncak pada jam **{int(peak['hr']):02d}:00** "
                f"dengan rata-rata **{peak['cnt']:.1f}** penyewaan")

    fig, axes = plt.subplots(1, 2, figsize=(14, 5), sharey=False)
    fig.patch.set_facecolor("#0e1117")

    colors_map = {"casual":"#f4a261","registered":"#457b9d","cnt":"#2a9d8f"}
    titles_map = {"Hari Kerja":"Hari Kerja",
                  "Libur":"Libur"}

    for ax, day_type in zip(axes, ["Hari Kerja","Libur"]):
        ax.set_facecolor("#1a1a2e")
        sub = hourly_pattern[hourly_pattern["day_type"] == day_type]
        if sub.empty:
            ax.text(12, 0.5, "No data", ha="center"); continue

        ax.fill_between(sub["hr"], sub["registered"], alpha=0.2,
                        color=colors_map["registered"])
        ax.fill_between(sub["hr"], sub["casual"], alpha=0.2,
                        color=colors_map["casual"])
        ax.plot(sub["hr"], sub["cnt"], color=colors_map["cnt"],
                linewidth=2.5, label="Total")
        ax.plot(sub["hr"], sub["registered"], color=colors_map["registered"],
                linewidth=1.8, linestyle="--", label="Registered")
        ax.plot(sub["hr"], sub["casual"], color=colors_map["casual"],
                linewidth=1.8, linestyle=":", label="Casual")

        peak_row = sub.loc[sub["cnt"].idxmax()]
        ax.axvline(peak_row["hr"], color="white", linestyle="--", alpha=0.4)
        ax.annotate(f"Jam {int(peak_row['hr']):02d}:00\n({peak_row['cnt']:.0f})",
                    xy=(peak_row["hr"], peak_row["cnt"]),
                    xytext=(peak_row["hr"]+2, peak_row["cnt"]*0.9),
                    color="white", fontsize=8,
                    arrowprops=dict(arrowstyle="->", color="white", lw=0.8))

        ax.set_title(titles_map[day_type], color="white", fontsize=12, fontweight="bold")
        ax.set_xlabel("Jam (0–23)", color="white", fontsize=10)
        ax.set_ylabel("Rata-rata Penyewaan", color="white", fontsize=10)
        ax.tick_params(colors="white")
        ax.set_xticks(range(0, 24, 2))
        ax.legend(facecolor="#1a1a2e", labelcolor="white", fontsize=9)
        ax.grid(True, alpha=0.2, color="white")
        for spine in ax.spines.values(): spine.set_color("gray")

    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

    st.success("""
    **Kesimpulan Pertanyaan 1:**
    - **Hari Kerja** → puncak 08:00 & 17:00–18:00 didominasi pengguna registered.
    - **Libur** → puncak 12:00–14:00, pengguna casual lebih besar.
    """)

# ──────────────────────────────────────────────────────────────────────────────
# TAB 2 — Cuaca & Musim
# ──────────────────────────────────────────────────────────────────────────────
with tab2:
    st.markdown("""
    <div class='section-header'>
        <h3>Pertanyaan 2</h3>
    </div>
    <p><em>Seberapa besar pengaruh cuaca dan musim terhadap penyewaan harian? dan kondisi manakah yang menghasilkan rata-rata penyewaan tertinggi dan terendah?</em></p>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)

    # --- Boxplot Musim ---
    with c1:
        st.subheader("Distribusi per Musim")
        season_order = ["Spring","Summer","Fall","Winter"]
        palette_s = ["#a8dadc","#457b9d","#e9c46a","#264653"]

        fig1, ax1 = plt.subplots(figsize=(7, 5))
        fig1.patch.set_facecolor("#0e1117")
        ax1.set_facecolor("#1a1a2e")

        valid_seasons = [s for s in season_order if s in day_filtered["season_label"].values]
        df_plot = day_filtered[day_filtered["season_label"].isin(valid_seasons)].copy()
        df_plot["season_label"] = pd.Categorical(df_plot["season_label"],
                                                  categories=valid_seasons, ordered=True)
        sns.boxplot(data=df_plot, x="season_label", y="cnt",
                    palette=palette_s[:len(valid_seasons)], ax=ax1,
                    order=valid_seasons, width=0.5)

        means_s = df_plot.groupby("season_label")["cnt"].mean()
        for i, s in enumerate(valid_seasons):
            if s in means_s.index:
                ax1.scatter(i, means_s[s], color="red", zorder=5, s=70, marker="D")
                ax1.text(i, means_s[s]+150, f'{means_s[s]:.0f}',
                         ha="center", fontsize=9, color="red", fontweight="bold")

        ax1.set_title("Penyewaan Harian per Musim", color="white", fontweight="bold")
        ax1.set_xlabel("Musim", color="white"); ax1.set_ylabel("Jumlah Penyewaan", color="white")
        ax1.tick_params(colors="white")
        ax1.grid(axis="y", alpha=0.2, color="white")
        for spine in ax1.spines.values(): spine.set_color("gray")
        plt.tight_layout()
        st.pyplot(fig1); plt.close()

    # --- Bar Cuaca ---
    with c2:
        st.subheader("Rata-rata per Kondisi Cuaca")
        weather_order = ["Clear/Partly Cloudy","Mist/Cloudy","Light Rain/Snow"]
        w_avg = (day_filtered.groupby("weather_label")["cnt"]
                 .mean()
                 .reindex([w for w in weather_order if w in day_filtered["weather_label"].values]))

        fig2, ax2 = plt.subplots(figsize=(7, 5))
        fig2.patch.set_facecolor("#0e1117")
        ax2.set_facecolor("#1a1a2e")

        palette_w = ["#2a9d8f","#e9c46a","#e76f51"][:len(w_avg)]
        bars = ax2.bar(range(len(w_avg)), w_avg.values, color=palette_w,
                       edgecolor="white", linewidth=0.5, width=0.5)
        for bar, val in zip(bars, w_avg.values):
            ax2.text(bar.get_x()+bar.get_width()/2, bar.get_height()+50,
                     f'{val:.0f}', ha="center", va="bottom", color="white",
                     fontsize=11, fontweight="bold")

        ax2.set_xticks(range(len(w_avg)))
        labels_w = [l.replace("/","\n") for l in w_avg.index]
        ax2.set_xticklabels(labels_w, color="white", fontsize=9)
        ax2.set_title("Rata-rata Penyewaan per Kondisi Cuaca", color="white", fontweight="bold")
        ax2.set_xlabel("Kondisi Cuaca", color="white"); ax2.set_ylabel("Rata-rata", color="white")
        ax2.tick_params(colors="white")
        ax2.grid(axis="y", alpha=0.2, color="white")
        for spine in ax2.spines.values(): spine.set_color("gray")
        plt.tight_layout()
        st.pyplot(fig2); plt.close()

    # Trend bulanan
    st.subheader("Tren Penyewaan Bulanan")
    monthly = (day_filtered.groupby(["yr","mnth"])["cnt"].sum().reset_index())
    monthly["Period"] = monthly["mnth"].map(
        {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
         7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"})
    monthly["Label"] = monthly.apply(
        lambda r: f"{'2011' if r['yr']==0 else '2012'}-{r['Period']}", axis=1)

    fig3, ax3 = plt.subplots(figsize=(14, 4))
    fig3.patch.set_facecolor("#0e1117")
    ax3.set_facecolor("#1a1a2e")
    for yr_val, color, label in zip([0,1],["#457b9d","#f4a261"],["2011","2012"]):
        sub = monthly[monthly["yr"] == yr_val]
        ax3.plot(sub["mnth"], sub["cnt"], marker="o", color=color, label=label, linewidth=2)
        ax3.fill_between(sub["mnth"], sub["cnt"], alpha=0.1, color=color)
    ax3.set_xticks(range(1,13))
    ax3.set_xticklabels(["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"],
                         color="white")
    ax3.tick_params(colors="white")
    ax3.set_title("Tren Total Penyewaan per Bulan (2011 vs 2012)", color="white", fontweight="bold")
    ax3.set_xlabel("Bulan", color="white"); ax3.set_ylabel("Total Penyewaan", color="white")
    ax3.legend(facecolor="#1a1a2e", labelcolor="white")
    ax3.grid(alpha=0.2, color="white")
    for spine in ax3.spines.values(): spine.set_color("gray")
    plt.tight_layout()
    st.pyplot(fig3); plt.close()

    st.success("""
    **Kesimpulan Pertanyaan 2:**
    - **fall (gugur)** adalah musim terbaik (~5.644/hari), **spring** terendah (~2.605/hari).
    - cuaca hujan/salju menurunkan penyewaan hingga **>60%** dibanding cuaca cerah.
    """)

# ──────────────────────────────────────────────────────────────────────────────
# TAB 3 — Analisis Lanjutan
# ──────────────────────────────────────────────────────────────────────────────
with tab3:
    st.markdown("""
    <div class='section-header'>
        <h3>Analisis Lanjutan: Manual Clustering</h3>
    </div>
    <p>pengelompokan hari berdasarkan <b>volume penyewaan</b> dan <b>tipe pengguna</b></p>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)

    with c1:
        # Scatter plot
        st.subheader("Volume Penyewaan vs. Suhu")
        cluster_colors = {
            "Low (<2K)":"#e76f51",
            "Medium (2K–4K)":"#e9c46a",
            "High (4K–6K)":"#2a9d8f",
            "Very High (>6K)":"#264653"
        }
        fig4, ax4 = plt.subplots(figsize=(7, 5))
        fig4.patch.set_facecolor("#0e1117"); ax4.set_facecolor("#1a1a2e")

        day_f2 = day_filtered.dropna(subset=["usage_cluster"])
        for cluster, color in cluster_colors.items():
            sub = day_f2[day_f2["usage_cluster"] == cluster]
            if sub.empty: continue
            ax4.scatter(sub["temp"]*41, sub["cnt"], alpha=0.5, s=20,
                        color=color, label=cluster)
        ax4.set_xlabel("Suhu Aktual (°C)", color="white")
        ax4.set_ylabel("Penyewaan Harian", color="white")
        ax4.tick_params(colors="white")
        ax4.legend(facecolor="#1a1a2e", labelcolor="white", fontsize=8,
                   title="Kluster Volume", title_fontsize=8)
        ax4.grid(alpha=0.2, color="white")
        for spine in ax4.spines.values(): spine.set_color("gray")
        plt.tight_layout(); st.pyplot(fig4); plt.close()

    with c2:
        # Pie chart
        st.subheader("Distribusi Tipe Pengguna")
        type_counts = day_filtered["user_type_cluster"].value_counts().dropna()
        fig5, ax5 = plt.subplots(figsize=(7, 5))
        fig5.patch.set_facecolor("#0e1117"); ax5.set_facecolor("#0e1117")
        wedge_colors = ["#457b9d","#a8dadc","#f4a261"]
        if not type_counts.empty:
            wedges, texts, autotexts = ax5.pie(
                type_counts.values, labels=type_counts.index,
                autopct="%1.1f%%", colors=wedge_colors[:len(type_counts)],
                startangle=140, pctdistance=0.75,
                textprops={"color":"white","fontsize":9})
            for at in autotexts: at.set_fontweight("bold")
        ax5.set_title("Kluster Tipe Pengguna", color="white", fontweight="bold")
        plt.tight_layout(); st.pyplot(fig5); plt.close()

    # Ringkasan kluster
    st.subheader("Ringkasan Kluster")
    cluster_summary = (day_filtered
                       .dropna(subset=["usage_cluster","user_type_cluster"])
                       .groupby(["usage_cluster","user_type_cluster"], observed=True)
                       .agg(Jumlah_Hari=("cnt","count"),
                            Rata_cnt=("cnt","mean"),
                            Hari_Kerja_Pct=("workingday","mean"))
                       .reset_index())
    cluster_summary["Rata_cnt"] = cluster_summary["Rata_cnt"].round(0)
    cluster_summary["Hari_Kerja_Pct"] = (cluster_summary["Hari_Kerja_Pct"]*100).round(1)
    st.dataframe(cluster_summary, use_container_width=True)

# ──────────────────────────────────────────────────────────────────────────────
# TAB 4 — Data & Insight
# ──────────────────────────────────────────────────────────────────────────────
with tab4:
    st.subheader("Data Harian (Filtered)")
    st.dataframe(day_filtered[["dteday","season_label","weather_label","day_type",
                                "casual","registered","cnt"]].reset_index(drop=True),
                 use_container_width=True, height=300)

    st.subheader("Statistik Deskriptif")
    st.dataframe(day_filtered[["casual","registered","cnt","temp","hum","windspeed"]]
                 .describe().round(2), use_container_width=True)

    st.markdown("---")
    st.subheader("✅ Rekomendasi Action Item")
    st.markdown("""
    1. **Tambah sepeda pada jam 07:30–09:00 & 16:30–18:30
       di hari kerja

    2. **Promosi berbasis cuaca untuk menjaga volume penyewaan tetap stabil di hari mist/cloudy agar volume tidak langsung turun
    """)
