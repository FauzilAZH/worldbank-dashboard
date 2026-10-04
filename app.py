import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score
import numpy as np

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
        
        df_pivot.rename(columns={'NY.GDP.MKTP.CD': 'gdp_value', 'SP.POP.TOTL': 'population'}, inplace=True)
        df_pivot.ffill(inplace=True)
        df_pivot.fillna(0, inplace=True)
        
        # Join Table
        df_master = pd.merge(df_pivot, df_country, on='country_code', how='left')
        return df_master
    
    except Exception as e:
        st.error(f"Gagal memuat data. Pastikan file CSV ada di folder yang sama. Error: {e}")
        return pd.DataFrame()

df_master = load_data()

if not df_master.empty:
    # --- 2. SIDEBAR (NAVIGASI & FILTER) ---
    st.sidebar.title("🌍 Navigasi & Filter")
    menu = st.sidebar.radio("Pilih Menu:", ["Tinjauan Global (EDA)", "Prediksi Machine Learning"])
    
    st.sidebar.markdown("---")
    
    # --- 3. MENU 1: TINJAUAN GLOBAL (EDA) ---
    if menu == "Tinjauan Global (EDA)":
        st.title("📈 Tinjauan Ekonomi & Demografi Global")
        
        # FILTER TAHUNAN DI SIDEBAR
        st.sidebar.subheader("Filter Data")
        min_year = int(df_master['year'].min())
        max_year = int(df_master['year'].max())
        
        # Membuat slider dari tahun terkecil sampai terbesar
        selected_year = st.sidebar.slider("Pilih Tahun:", min_value=min_year, max_value=max_year, value=max_year)
        
        # Menyaring data hanya untuk tahun yang dipilih di slider
        df_terbaru = df_master[df_master['year'] == selected_year]
        
        # Kolom Metrik Angka
        col1, col2, col3 = st.columns(3)
        col1.metric(label="Total Negara Dianalisis", value=df_terbaru['country_code'].nunique())
        col2.metric(label=f"Populasi Global ({selected_year})", value=f"{df_terbaru['population'].sum() / 1e9:.2f} Miliar")
        col3.metric(label=f"GDP Global ({selected_year})", value=f"${df_terbaru['gdp_value'].sum() / 1e12:.2f} Triliun")
        
        st.markdown("---")
        
        # Peta Geospasial (Berubah sesuai tahun)
        st.subheader(f"🗺️ Peta Sebaran Populasi Global (Tahun {selected_year})")
        fig_map = px.choropleth(
            df_terbaru, locations="country_code", color="population",
            hover_name="country_name", color_continuous_scale=px.colors.sequential.Plasma
        )
        fig_map.update_layout(geo=dict(showframe=False, showcoastlines=True))
        st.plotly_chart(fig_map, use_container_width=True)
        
        # Chart Terbagi 2 Kolom
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.subheader(f"🏆 Top 10 GDP Tertinggi ({selected_year})")
            top_gdp = df_terbaru.groupby('country_name')['gdp_value'].max().sort_values(ascending=False).head(10).reset_index()
            fig_bar = px.bar(top_gdp, x='gdp_value', y='country_name', orientation='h', color='gdp_value')
            st.plotly_chart(fig_bar, use_container_width=True)
            
        with col_chart2:
            st.subheader("📊 Distribusi Income Level")
            # Income level tidak berubah per tahun, jadi pakai df_master
            income_counts = df_master[['country_code', 'income_level']].drop_duplicates()['income_level'].value_counts().reset_index()
            income_counts.columns = ['income_level', 'count']
            fig_pie = px.pie(income_counts, values='count', names='income_level', hole=0.3)
            st.plotly_chart(fig_pie, use_container_width=True)

    # --- 4. MENU 2: PREDIKSI MACHINE LEARNING (LINEAR REGRESSION) ---
    elif menu == "Prediksi Machine Learning":
        st.title("🤖 Prediksi GDP dengan Regresi Linear")
        st.write("Silakan pilih negara untuk melihat bagaimana model AI memprediksi tren GDP-nya di masa depan.")
        
        list_negara = df_master['country_name'].dropna().unique()
        default_index = list(list_negara).index('Indonesia') if 'Indonesia' in list_negara else 0
        
        selected_country = st.selectbox("Pilih Negara:", list_negara, index=default_index)
        
        # Filter data sesuai negara
        df_ml = df_master[df_master['country_name'] == selected_country].sort_values('year').copy()
        
        if len(df_ml) < 4:
            st.warning("Data historis tidak cukup untuk membuat prediksi (butuh minimal 4 tahun data).")
        else:
            X = df_ml[['year']]
            y = df_ml['gdp_value']
            
            # Split Data Manual (Misal ambil 2 tahun terakhir untuk Ujian)
            jumlah_test = 2
            X_train = X.iloc[:-jumlah_test]
            X_test  = X.iloc[-jumlah_test:]
            y_train = y.iloc[:-jumlah_test]
            y_test  = y.iloc[-jumlah_test:]
            
            # Train Model (Linear Regression)
            model_lr = LinearRegression()
            model_lr.fit(X_train, y_train)
            
            # Prediksi
            y_pred_train = model_lr.predict(X_train)
            y_pred_test = model_lr.predict(X_test)
            garis_tren = model_lr.predict(X) # Prediksi full untuk digambar garis lurusnya
            
            # Metrik
            mae = mean_absolute_error(y_test, y_pred_test)
            r2 = r2_score(y_test, y_pred_test)
            
            st.success(f"Model Linear Regression berhasil dilatih!")
            col_m1, col_m2 = st.columns(2)
            col_m1.info(f"**R-Squared (Test):** {r2 * 100:.2f}% (Seberapa akurat garis menangkap tren)")
            col_m2.info(f"**MAE (Test):** ${mae:,.2f} (Rata-rata error/meleset)")
            
            # Visualisasi Prediksi vs Asli menggunakan Plotly
            fig_pred = px.line(title=f"Prediksi Tren GDP ({selected_country})")
            
            # Tambah data asli
            fig_pred.add_scatter(x=df_ml['year'], y=y, mode='lines+markers', name='GDP Asli', line=dict(color='blue'))
            
            # Tambah hasil tebakan test
            fig_pred.add_scatter(x=X_test['year'], y=y_pred_test, mode='markers', name='Prediksi 2 Tahun Terakhir', marker=dict(color='red', size=10, symbol='x'))
            
            # Tambah garis tren hijau
            fig_pred.add_scatter(x=df_ml['year'], y=garis_tren, mode='lines', name='Garis Tren Pembelajaran', line=dict(color='green', dash='dot'))
            
            st.plotly_chart(fig_pred, use_container_width=True)
            st.info("💡 **Penjelasan:** Titik 'X' merah adalah hasil tebakan di data baru. Garis putus-putus hijau adalah hasil rumusan garis lurus (trend) yang ditemukan oleh AI dari masa lalu hingga masa depan.")
