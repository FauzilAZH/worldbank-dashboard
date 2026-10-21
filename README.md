# worldbank-dashboard

# 🌍 Global Economic & Demographic Insights (GEDI)
### Automated World Bank ETL Pipeline, Data Warehouse & Predictive Analytics

[![Apache Airflow](https://img.shields.io/badge/Orchestration-Apache%20Airflow-017CEE?style=for-the-badge&logo=Apache%20Airflow&logoColor=white)](https://airflow.apache.org/)
[![Astronomer](https://img.shields.io/badge/Astro%20CLI-Runtime%203.3--8-7B3FF2?style=for-the-badge&logo=docker&logoColor=white)](https://www.astronomer.io/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![MySQL](https://img.shields.io/badge/Database-MySQL%208.x-4479A1?style=for-the-badge&logo=mysql&logoColor=white)](https://www.mysql.com/)
[![Pandas](https://img.shields.io/badge/Data%20Processing-Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![Scikit-Learn](https://img.shields.io/badge/Machine%20Learning-Scikit--Learn-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)

---

## 📖 Ringkasan Proyek

Repository ini berisi implementasi **End-to-End Data Engineering & Predictive Analytics Pipeline** berbasis data terbuka dari **World Bank (Bank Dunia)**. 

Proyek ini mengotomatiskan siklus hidup data mulai dari ekstraksi data API secara terjadwal menggunakan **Apache Airflow (Astronomer CLI)**, pembersihan serta transformasi data dengan skema bintang (*Star Schema*), pemuatan ke data warehouse **MySQL**, hingga analisis eksplorasi data (*Exploratory Data Analysis / EDA*) dan peramalan tren ekonomi masa depan (*Predictive Machine Learning*).

---

## 🎯 Tujuan & Fitur Utama

1. **Automated ETL Pipeline (Data Engineering)**:
   - Menarik data indikator pembangunan global (*GDP*, *Total Population*, dan *CO2 Emissions*) serta profil metadata negara dari REST API World Bank (2014–2025).
   - Validasi data ketat: memfilter agregat wilayah regional non-negara, mencocokkan kode negara standar ISO-3, membuang data duplikat dan *missing values*.
   - Menggunakan Airflow TaskFlow API dengan `MySqlHook` untuk operasi *upsert* / *replace*.
2. **Data Warehouse Modeling (Star Schema)**:
   - Memodelkan data ke dalam tabel dimensi (`dim_country`, `dim_indicator`) dan tabel fakta (`fact_worldbank_data`).
3. **Exploratory Data Analysis (Data Analytics)**:
   - Menjawab pertanyaan bisnis mengenai peringkat negara berdasarkan GDP, distribusi tingkat pendapatan (*Income Level*), korelasi populasi vs. ekonomi, serta pemetaan geospasial populasi global.
4. **Predictive Modeling (Machine Learning)**:
   - Proyeksi dan estimasi nilai GDP negara (studi kasus: Indonesia) menggunakan regresi berbasis deret waktu (*Time-Series Linear Regression*).

---

## 🏗️ Arsitektur Sistem & Alur Data

```mermaid
flowchart TD
    subgraph Data_Source ["1. Data Source"]
        WB_API["World Bank Open Data REST API<br/>(GDP, Population, CO2 & Countries)"]
    end

    subgraph Orchestration ["2. Apache Airflow (Astronomer Runtime)"]
        direction TB
        Task1["extract_data()<br/>Tarik JSON API (Indikator & Profil Negara)"]
        Task2["transform_data()<br/>Cleaning, Filter ISO-3 & Pemodelan Dimensi/Fakta"]
        Task3["load_data()<br/>MySqlHook Upsert ke RDBMS"]
        
        Task1 --> Task2 --> Task3
    end

    subgraph Storage ["3. Data Warehouse (MySQL)"]
        direction TB
        DC[("dim_country<br/>(country_code, country_name, region, income_level)")]
        DI[("dim_indicator<br/>(indicator_code, indicator_name, source_note)")]
        FD[("fact_worldbank_data<br/>(id, country_code, indicator_code, year, value)")]
        
        DC --- FD
        DI --- FD
    end

    subgraph Analytics ["4. Data Science & Machine Learning"]
        direction TB
        EDA["Exploratory Data Analysis (EDA)<br/>(Bar Chart, Donut Chart, Heatmap, Choropleth Map)"]
        ML["Machine Learning Forecasting<br/>(Linear Regression GDP Prediction)"]
    end

    WB_API --> Task1
    Task3 --> Storage
    Storage --> EDA
    Storage --> ML
```

---

## 🗄️ Model Data (Star Schema)

Database `worldbank_db` dirancang dengan arsitektur **Star Schema**:

```mermaid
erDiagram
    dim_country ||--o{ fact_worldbank_data : "1:N (country_code)"
    dim_indicator ||--o{ fact_worldbank_data : "1:N (indicator_code)"

    dim_country {
        varchar(3) country_code PK
        varchar(100) country_name
        varchar(50) region
        varchar(50) income_level
    }

    dim_indicator {
        varchar(50) indicator_code PK
        varchar(255) indicator_name
        text source_note
    }

    fact_worldbank_data {
        int id PK
        varchar(3) country_code FK
        varchar(50) indicator_code FK
        int year
        decimal value
    }
```

### Indikator Bank Dunia yang Digunakan
| Kode Indikator | Nama Indikator | Deskripsi Singkat |
|---|---|---|
| `NY.GDP.MKTP.CD` | GDP (Current US$) | Produk Domestik Bruto dalam USD berjalan |
| `SP.POP.TOTL` | Population, total | Jumlah total estimasi penduduk |
| `EN.ATM.CO2E.KT` | CO2 emissions (kt) | Emisi karbon dioksida dalam kiloton |

---

## 📂 Struktur Direktori Proyek

```text
worldbank-etl/
├── .astro/                                       # Konfigurasi internal Astronomer CLI
├── dags/
│   ├── .airflowignore                            # File pengabaian Airflow
│   └── worldbank_etl_dag.py                      # DAG Airflow: Ekstraksi, Transformasi & Load ke MySQL
├── E1E124065_La_Ode_Muhammad_Fauzilazhim.ipynb   # Notebook Analisis: EDA & Linear Regression Model
├── Salinan_dari_data_world_bank_kedua.ipynb      # Notebook Eksperimen Alternatif (XGBoost Regressor)
├── worldbank_db.sql                              # Backup DDL & Dump Data Star Schema MySQL
├── airflow_settings.yaml                         # Konfigurasi lokal koneksi & variabel Airflow
├── requirements.txt                              # Dependensi Python untuk runtime Airflow
├── Dockerfile                                    # Dockerfile Astronomer Runtime
├── packages.txt                                  # Dependensi tingkat OS Linux (opsional)
├── .gitignore                                    # File pengabaian Git
└── README.md                                     # Dokumentasi lengkap proyek
```

---

## 📊 Pertanyaan Bisnis & Analisis Data

Notebook analisis menjawab 5 pertanyaan kunci:

1. **Top 10 Negara dengan Rata-rata GDP Tertinggi**:
   - Membandingkan performa perekonomian negara terbesar di dunia (misal: USA, China, Jepang, Jerman) berdasarkan rata-rata GDP historis.
2. **Distribusi Negara Berdasarkan Tingkat Pendapatan (*Income Level*)**:
   - Menganalisis proporsi persentase pembagian status ekonomi negara (*High income*, *Upper middle income*, *Lower middle income*, *Low income*).
3. **Korelasi Antara Jumlah Populasi dan GDP Global**:
   - Uji korelasi numerik untuk melihat apakah negara berpopulasi tinggi selalu memiliki ekonomi yang lebih besar.
4. **Analisis Spasial / Geospasial Populasi Global**:
   - Visualisasi peta tematik (*Choropleth Map*) untuk memetakan konsentrasi kepadatan demografi di berbagai benua.
5. **Prediksi Tren GDP Masa Depan (Studi Kasus: Indonesia)**:
   - Pelatihan model **Linear Regression** pada deret waktu historis untuk memproyeksikan GDP Indonesia pada tahun 2026–2027.
   - Evaluasi performa model menggunakan metrik $R^2$ (*Coefficient of Determination*) dan MAE (*Mean Absolute Error*).

---

## 🚀 Panduan Instalasi & Menjalankan Proyek

### 1. Prasyarat Sistem
Pastikan perangkat Anda telah terpasang:
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Harus dalam keadaan *running*)
- [Astro CLI (Astronomer)](https://www.astronomer.io/docs/astro/cli/install-cli)
- [Python 3.10+](https://www.python.org/)
- [MySQL Server](https://dev.mysql.com/downloads/mysql/) atau [XAMPP / phpMyAdmin](https://www.apachefriends.org/)

---

### 2. Konfigurasi Database MySQL
1. Buat database baru bernama `worldbank_db` di server MySQL Anda:
   ```sql
   CREATE DATABASE worldbank_db;
   ```
2. Import skema dan data awal menggunakan file [worldbank_db.sql](worldbank_db.sql):
   ```bash
   mysql -u root -p worldbank_db < worldbank_db.sql
   ```
   *(Atau import melalui antarmuka phpMyAdmin)*.

---

### 3. Konfigurasi Koneksi Airflow ke MySQL
Karena Airflow berjalan di dalam container Docker, host database lokal harus diarahkan ke `host.docker.internal`:

Anda dapat mengaturnya melalui file `airflow_settings.yaml` atau langsung di **Airflow UI** (`Admin` -> `Connections`):

- **Connection Id**: `mysql_default`
- **Connection Type**: `MySQL`
- **Host**: `host.docker.internal` (atau IP lokal host)
- **Database/Schema**: `worldbank_db`
- **Login / Username**: `root` (sesuaikan dengan kredensial Anda)
- **Password**: *(password MySQL Anda)*
- **Port**: `3306`

---

### 4. Menjalankan Apache Airflow
Buka terminal pada direktori proyek, lalu jalankan:

```bash
# Inisialisasi dan jalankan container Airflow
astro dev start
```

Perintah di atas akan mengunduh image dan menyalakan 5 container utama:
- `Postgres` (Metadata Database Airflow)
- `Scheduler`
- `DAG Processor`
- `Triggerer`
- `Webserver / API Server`

Setelah selesai, buka antarmuka Airflow di browser:
- **URL**: [http://localhost:8080](http://localhost:8080)
- **Username Default**: `admin`
- **Password Default**: `admin`

Cari DAG bernama `worldbank_api_to_mysql`, aktifkan tombol **Toggle**, lalu klik tombol **Trigger DAG** untuk menjalankan pipeline ETL.

Untuk menghentikan Airflow jika selesai digunakan:
```bash
astro dev stop
```

---

### 5. Menjalankan Notebook Analisis & Machine Learning
Jalankan Jupyter Notebook atau VS Code:

```bash
# Install paket analisis data yang dibutuhkan
pip install pandas numpy matplotlib seaborn plotly scikit-learn jupyter

# Jalankan Jupyter Notebook
jupyter notebook
```

Buka file [E1E124065_La_Ode_Muhammad_Fauzilazhim.ipynb](E1E124065_La_Ode_Muhammad_Fauzilazhim.ipynb) dan jalankan seluruh cell (*Run All*) untuk melihat visualisasi dan hasil peramalan Machine Learning.

---

## 🛠️ Teknologi & Pustaka

| Kategori | Teknologi / Pustaka |
|---|---|
| **Orchestration** | Apache Airflow, Astronomer Runtime |
| **Containerization** | Docker, Docker Compose |
| **Database & DWH** | MySQL, phpMyAdmin |
| **Data Ingestion** | Python `requests`, World Bank REST API v2 |
| **Data Transformation** | Pandas, NumPy |
| **Machine Learning** | Scikit-Learn (`LinearRegression`, `metrics`) |
| **Visualisasi Data** | Matplotlib, Seaborn, Plotly Express |

---

## 👤 Penulis / Pengembang

- **Nama**: La Ode Muhammad Fauzilazhim
- **NIM**: E1E124065
- **Topik**: Data Engineering & Predictive Data Analytics (World Bank Data Pipeline)

---

## 📄 Lisensi
Proyek ini dibuat untuk keperluan akademik, portofolio data engineering, dan penelitian analisis data terbuka. Lisensi bebas digunakan dan dikembangkan kembali (*Open Source*).
