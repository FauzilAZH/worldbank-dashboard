from datetime import datetime, timedelta
import requests
import pandas as pd
from airflow.decorators import dag, task
from airflow.providers.mysql.hooks.mysql import MySqlHook

default_args = {
    'owner': 'data_engineer',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

@dag(
    dag_id='worldbank_api_to_mysql',
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule='@monthly', 
    catchup=False,
    tags=['worldbank', 'etl', 'mysql'],
    description='ETL Data World Bank (GDP, Populasi, Emisi Karbon) ke MySQL'
)
def worldbank_etl():

    @task
    def extract_data():
        """Menarik data dari API indikator dan API profil negara."""
        indicator_list = ['NY.GDP.MKTP.CD', 'SP.POP.TOTL', 'EN.ATM.CO2E.KT']
        all_indicators = []
        
        # 1. Tarik data metrik
        for ind_code in indicator_list:
            url = f"http://api.worldbank.org/v2/country/all/indicator/{ind_code}"
            params = {"date": "2014:2025", "format": "json", "per_page": 5000}
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            if len(data) > 1 and data[1] is not None:
                all_indicators.extend(data[1])

        # 2. Tarik data profil negara
        country_url = "http://api.worldbank.org/v2/country/all"
        country_params = {"format": "json", "per_page": 350} 
        country_response = requests.get(country_url, params=country_params)
        country_response.raise_for_status()
        
        country_data = []
        country_json = country_response.json()
        if len(country_json) > 1 and country_json[1] is not None:
            country_data = country_json[1]

        return {
            "indicators": all_indicators,
            "countries": country_data
        }

    @task
    def transform_data(raw_data: dict) -> dict:
        import pandas as pd
        
        # 1. Dimensi Negara
        countries = []
        for row in raw_data["countries"]:
            region_dict = row.get('region')
            if region_dict and isinstance(region_dict, dict):
                region_val = region_dict.get('value', '')
                # Filter: Hanya ambil yang memiliki region jelas dan bukan agregat
                if region_val and region_val != 'Aggregates':
                    countries.append({
                        'country_code': row['id'], 
                        'country_name': row['name'],
                        'region': region_val,
                        'income_level': row.get('incomeLevel', {}).get('value', 'Unknown')
                    })
        df_country = pd.DataFrame(countries).drop_duplicates(subset=['country_code'])
        
        # KUNCI PERBAIKAN: Ekstrak daftar kode negara yang 100% valid masuk tabel dimensi
        valid_country_codes = set(df_country['country_code'].tolist())

        # 2. Dimensi Indikator
        indicators = []
        for row in raw_data["indicators"]:
            ind_dict = row.get('indicator')
            if ind_dict and isinstance(ind_dict, dict):
                indicators.append({
                    'indicator_code': ind_dict.get('id'),
                    'indicator_name': ind_dict.get('value'),
                    'source_note': 'Data from World Bank API'
                })
        df_indicator = pd.DataFrame(indicators).drop_duplicates(subset=['indicator_code'])
        
        # Ekstrak daftar kode indikator yang valid
        valid_indicator_codes = set(df_indicator['indicator_code'].tolist())

        # 3. Fakta Nilai Metrik
        facts = []
        for row in raw_data["indicators"]:
            country_code = row.get('countryiso3code')
            ind_code = row.get('indicator', {}).get('id')
            val = row.get('value')
            
            # FILTER KETAT: Pastikan metrik dimasukkan HANYA JIKA country_code ada di dimensi
            # Pastikan country_code bukan string kosong dan panjangnya 3 karakter
            if pd.notnull(val) and country_code and len(str(country_code)) == 3:
                if (country_code in valid_country_codes) and (ind_code in valid_indicator_codes):
                    facts.append({
                        'country_code': country_code,
                        'indicator_code': ind_code,
                        'year': int(row['date']),
                        'value': float(val)
                    })
        df_fact = pd.DataFrame(facts)

        return {
            "countries": df_country.to_dict(orient='records'),
            "indicators": df_indicator.to_dict(orient='records'),
            "facts": df_fact.to_dict(orient='records')
        }

    @task
    def load_data(transformed_data: dict):
        """Memasukkan data ke MySQL."""
        mysql_hook = MySqlHook(mysql_conn_id='mysql_default')
        
        # Load dim_country
        country_records = [
            (c['country_code'], c['country_name'], c['region'], c['income_level']) 
            for c in transformed_data['countries']
        ]
        if country_records:
            mysql_hook.insert_rows(
                table="dim_country", 
                rows=country_records, 
                target_fields=["country_code", "country_name", "region", "income_level"], 
                replace=True
            )

        # Load dim_indicator
        indicator_records = [
            (i['indicator_code'], i['indicator_name'], i['source_note']) 
            for i in transformed_data['indicators']
        ]
        if indicator_records:
            mysql_hook.insert_rows(
                table="dim_indicator", 
                rows=indicator_records, 
                target_fields=["indicator_code", "indicator_name", "source_note"], 
                replace=True
            )

        # Load fact_worldbank_data
        fact_records = [
            (f['country_code'], f['indicator_code'], f['year'], f['value']) 
            for f in transformed_data['facts']
        ]
        if fact_records:
            mysql_hook.insert_rows(
                table="fact_worldbank_data", 
                rows=fact_records, 
                target_fields=["country_code", "indicator_code", "year", "value"],
                replace=True 
            )

    # Definisi alur kerja
    raw_api_data = extract_data()
    clean_data = transform_data(raw_api_data)
    load_data(clean_data)

# Inisialisasi
dag_instance = worldbank_etl()