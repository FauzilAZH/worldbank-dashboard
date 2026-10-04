import streamlit as st
import pandas as pd
import plotly.express as px
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score

# Set konfigurasi halaman Dashboard
st.set_page_config(page_title="World Bank Dashboard", page_icon="🌍", layout="wide")

# --- 1. FUNGSI UNTUK LOAD & CLEAN DATA ---
@st.cache_data
def load_data():
    try:
        # Load Data
        df_country = pd.read_csv("dim_country.csv")
        df_fact = pd.read_csv("fact_worldbank_data.csv")
        
        # Clean & Pivot Fact Data
        df_fact = df_fact.dropna(subset=['value'])
        df_pivot = df_fact.pivot_table(
            index=['country_code', 'year'],
            columns='indicator_code',
            values='value'
        ).reset_index()
        
        # Rename kolom agar mudah dipanggil
        df_pivot.rename(columns={'NY.GDP.MKTP.CD': 'gdp_value', 'SP.POP.TOTL': 'population'}, inplace=True)
        
        # PERBAIKAN: Menggunakan fungsi ffill yang terbaru agar tidak error di Streamlit Cloud
        df_pivot.ffill(inplace=True)
        df_pivot.fillna(0, inplace=True)
        
        # Join Table
        df_master = pd.merge(df_pivot, df_country, on='country_code', how='left')
        
        # FEATURE ENGINEERING: Tambah kolom GDP per Kapita
        df_master['gdp_per_capita'] = df_master['gdp_value'] / df_master['population']
        
        return df_master
    
    except Exception as e:
        st.error(f"Gagal memuat data. Pastikan file CSV ada di folder yang sama. Error: {e}")
        return pd.DataFrame()

df_master = load_data()

if not df_master.empty:
    # --- 2. SIDEBAR (NAVIGASI & FILTER) ---
    st.sidebar.title("🌍 GEDI Dashboard")
    st.sidebar.caption("Global Economic & Demographic Insights")
    st.sidebar.markdown("---")
    
    menu = st.sidebar.radio("Pilih Menu:", [
        "1. Tinjauan Eksekutif", 
        "2. Analisis Mendalam (EDA)", 
        "3. Prediksi Machine Learning"
    ])
    
    st.sidebar.markdown("---")
    
    # --- 3. MENU 1: TINJAUAN EKSEKUTIF ---
    if menu == "1. Tinjauan Eksekutif":
        st.title("📈 Tinjauan Eksekutif Global")
        st.write("Ringkasan kondisi ekonomi dan populasi dunia.")
        
        # FILTER TAHUNAN
        st.sidebar.subheader("Filter Tahun (Untuk Metrik & Peta)")
        min_year = int(df_master['year'].min())
        max_year = int(df_master['year'].max())
        selected_year = st.sidebar.slider("Pilih Tahun:", min_value=min_year, max_value=max_year, value=max_year)
        
        df_terbaru = df_master[df_master['year'] == selected_year]
        
        # Kolom Metrik
        col1, col2, col3 = st.columns(3)
        col1.metric("Negara Dianalisis", f"{df_terbaru['country_code'].nunique()} Negara")
        col2.metric(f"Populasi Global ({selected_year})", f"{df_terbaru['population'].sum() / 1e9:.2f} Miliar Jiwa")
        col3.metric(f"Total GDP Global ({selected_year})", f"${df_terbaru['gdp_value'].sum() / 1e12:.2f} Triliun")
        
        st.markdown("---")
        
        # Peta Geospasial
        st.subheader(f"🗺️ Peta Sebaran Populasi Global ({selected_year})")
        fig_map = px.choropleth(
            df_terbaru, locations="country_code", color="population",
            hover_name="country_name", color_continuous_scale=px.colors.sequential.Plasma
        )
        fig_map.update_layout(geo=dict(showframe=False, showcoastlines=True), margin={"r":0,"t":0,"l":0,"b":0})
        st.plotly_chart(fig_map, use_container_width=True)
        
        st.markdown("---")
        
        # Tren Historis Global
        st.subheader("📊 Tren Pertumbuhan GDP Global (Seluruh Tahun)")
        df_trend = df_master.groupby('year')['gdp_value'].sum().reset_index()
        fig_trend = px.area(df_trend, x='year', y='gdp_value', title="Pertumbuhan Ekonomi Dunia")
        fig_trend.update_traces(line_color='#00b4d8', fillcolor='rgba(0, 180, 216, 0.3)')
        st.plotly_chart(fig_trend, use_container_width=True)


    # --- 4. MENU 2: ANALISIS MENDALAM (EDA) ---
    elif menu == "2. Analisis Mendalam (EDA)":
        st.title("🔍 Analisis Ekonomi Mendalam")
        st.write("Eksplorasi hubungan antar variabel secara komprehensif (rata-rata dari seluruh tahun yang tersedia).")
        
        # Kumpulan Bar Chart
        col_bar1, col_bar2 = st.columns(2)
        with col_bar1:
            st.subheader("🏆 Top 10 Total GDP")
            top_gdp = df_master.groupby('country_name')['gdp_value'].mean().sort_values(ascending=False).head(10).reset_index()
            fig_b1 = px.bar(top_gdp, x='gdp_value', y='country_name', orientation='h', color='gdp_value', color_continuous_scale='Viridis')
            st.plotly_chart(fig_b1, use_container_width=True)
            
        with col_bar2:
            st.subheader("💰 Top 10 GDP per Kapita (Negara Terkaya)")
            top_percap = df_master.groupby('country_name')['gdp_per_capita'].mean().sort_values(ascending=False).head(10).reset_index()
            fig_b2 = px.bar(top_percap, x='gdp_per_capita', y='country_name', orientation='h', color='gdp_per_capita', color_continuous_scale='Magma')
            st.plotly_chart(fig_b2, use_container_width=True)

        st.markdown("---")
        
        col_pie, col_scatter = st.columns([1, 1.5])
        
        with col_pie:
            st.subheader("🌍 Persentase Status Income")
            income_counts = df_master[['country_code', 'income_level']].drop_duplicates()['income_level'].value_counts().reset_index()
            income_counts.columns = ['income_level', 'count']
            fig_pie = px.pie(income_counts, values='count', names='income_level', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with col_scatter:
            st.subheader("📌 Korelasi Populasi vs GDP")
            # Kita ambil rata-rata tiap negara agar titiknya pas
            df_scatter = df_master.groupby(['country_name', 'region'])[['population', 'gdp_value']].mean().reset_index()
            fig_scatter = px.scatter(
                df_scatter, x='population', y='gdp_value', color='region', 
                hover_name='country_name', log_x=True, log_y=True, opacity=0.7,
                title="Sumbu X (Populasi) dan Y (GDP) dalam skala Logaritmik"
            )
            st.plotly_chart(fig_scatter, use_container_width=True)

        st.markdown("---")
        
        st.subheader("🏢 Rata-rata GDP Berdasarkan Kawasan (Region)")
        df_region = df_master.groupby('region')['gdp_value'].mean().sort_values(ascending=False).reset_index()
        fig_reg = px.bar(df_region, x='region', y='gdp_value', color='region')
        st.plotly_chart(fig_reg, use_container_width=True)


    # --- 5. MENU 3: PREDIKSI MACHINE LEARNING ---
    elif menu == "3. Prediksi Machine Learning":
        st.title("🤖 Kecerdasan Buatan (Regresi Linear)")
        st.write("Pilih negara untuk memprediksi arah tren ekonominya di masa depan.")
        
        list_negara = df_master['country_name'].dropna().unique()
        default_index = list(list_negara).index('Indonesia') if 'Indonesia' in list_negara else 0
        selected_country = st.selectbox("Pilih Negara Target:", list_negara, index=default_index)
        
        df_ml = df_master[df_master['country_name'] == selected_country].sort_values('year').copy()
        
        if len(df_ml) < 4:
            st.warning("Data historis negara ini tidak mencukupi untuk membuat model yang akurat (butuh > 4 tahun).")
        else:
            X = df_ml[['year']]
            y = df_ml['gdp_value']
            
            # Split Data Manual
            jumlah_test = 2
            X_train, X_test = X.iloc[:-jumlah_test], X.iloc[-jumlah_test:]
            y_train, y_test = y.iloc[:-jumlah_test], y.iloc[-jumlah_test:]
            
            # Melatih AI (Training)
            model_lr = LinearRegression()
            model_lr.fit(X_train, y_train)
            
            y_pred_test = model_lr.predict(X_test)
            garis_tren = model_lr.predict(X)
            
            mae = mean_absolute_error(y_test, y_pred_test)
            r2 = r2_score(y_test, y_pred_test)
            
            # Tampilan Metrik Evaluasi
            st.success("✨ Model berhasil mempelajari pola sejarah!")
            col_m1, col_m2 = st.columns(2)
            col_m1.info(f"🎯 **Akurasi Pola (R-Squared):** {r2 * 100:.2f}%")
            col_m2.info(f"💵 **Rata-rata Meleset (MAE):** USD {mae:,.0f}")
            
            # Visualisasi
            fig_pred = px.line(title=f"Grafik Prediksi Tren GDP - {selected_country}")
            fig_pred.add_scatter(x=df_ml['year'], y=y, mode='lines+markers', name='GDP Asli (Aktual)', line=dict(color='#023e8a', width=3))
            fig_pred.add_scatter(x=X_test['year'], y=y_pred_test, mode='markers', name='Tebakan Model (Test)', marker=dict(color='#d90429', size=12, symbol='x'))
            fig_pred.add_scatter(x=df_ml['year'], y=garis_tren, mode='lines', name='Garis Tren Linier', line=dict(color='#00b4d8', dash='dash'))
            
            fig_pred.update_layout(hovermode="x unified")
            st.plotly_chart(fig_pred, use_container_width=True)
            
            st.markdown("""
            **Cara Membaca Grafik:**
            * Garis **Biru Gelap** adalah data asli dari World Bank.
            * Garis **Putus-putus Biru Muda** adalah tarikan garis lurus tren ekonomi berdasarkan rumus regresi.
            * Tanda **'X' Merah** menunjukkan prediksi model di tahun terbaru, perhatikan seberapa dekat ia dengan data aslinya!
            """)
