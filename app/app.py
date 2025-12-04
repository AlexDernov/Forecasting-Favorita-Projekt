import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# -------------------------------
# 1️⃣ Sidebar: Beschreibung der App
# -------------------------------
st.sidebar.title("Sales Forecast Dashboard")
st.sidebar.markdown("""
**Zielgruppe:**  
- Demand Planning Team  
- Regional Sales Manager  
- Supply Chain Analyst  

**Warum nützlich?**  
- Schneller Überblick über erwartete Verkäufe pro Tag und Store  
- Summenprognosen helfen, Lagerbestände zu planen  
- Interaktive N-Tage Auswahl erlaubt Simulation unterschiedlicher Planungshorizonte  
- Visualisierung erleichtert das Erkennen von Peaks und Trends  

**Hinweis:**  
Die Prognosen basieren auf einem Modell, das auf historischen Daten von Juli 2015 bis August 2017 trainiert wurde.
""")

# -------------------------------
# 2️⃣ Funktion: Daten laden
# -------------------------------
def load_data_with_chunks(local_paths, cloud_url=None, chunk_size=10**6):
    for path in local_paths:
        try:
            chunks = []
            for chunk in pd.read_csv(path, chunksize=chunk_size, sep=','):
                chunks.append(chunk)
            df = pd.concat(chunks, ignore_index=True)
            st.sidebar.success(f"Lokale Daten geladen: {path}")
            return df
        except Exception as e:
            st.sidebar.error(f"Fehler beim Laden von {path}: {e}")
    
    if cloud_url:
        try:
            file_id = cloud_url.split('/')[-2]
            download_url = f'https://drive.google.com/uc?id={file_id}'
            chunks = []
            for chunk in pd.read_csv(download_url, chunksize=chunk_size, sep=','):
                chunks.append(chunk)
            df = pd.concat(chunks, ignore_index=True)
            st.sidebar.success("Daten von Cloud geladen")
            return df
        except Exception as e:
            st.sidebar.error(f"Cloud-Download fehlgeschlagen: {e}")
    st.sidebar.warning("Keine Datenquelle verfügbar")
    return None

# -------------------------------
# 3️⃣ Daten laden
# -------------------------------
forecast_df = load_data_with_chunks(
    local_paths=['../data/data_forecast/.csv'],
    cloud_url='https://drive.google.com/file/d/166SQFUQ6U9RC3yO8NElJqclxaEjv_8ro/view?usp=sharing'
)

if forecast_df is None:
    st.error("Forecast-Daten konnten nicht geladen werden.")
    st.stop()

forecast_df['date'] = pd.to_datetime(forecast_df['date'])

st.write("## Vorschau Forecast-Daten")
st.dataframe(forecast_df.head())

# -------------------------------
# 4️⃣ N-Tage Auswahl (Slider)
# -------------------------------
n_days = st.sidebar.slider(
    "Wähle die Anzahl der Tage für die Prognose", 
    min_value=2, max_value=14, value=5
)

start_date = pd.Timestamp("2017-08-16")
end_date = start_date + pd.Timedelta(days=n_days-1)

forecast_period = forecast_df[
    (forecast_df["date"] >= start_date) & (forecast_df["date"] <= end_date)
].copy()

st.write(f"### Prognosen für {n_days} Tage von {start_date.date()} bis {end_date.date()}")
st.dataframe(forecast_period.head())

# -------------------------------
# 5️⃣ Summierte Prognose pro Tag
# -------------------------------
agg_forecast = forecast_period.groupby("date")["forecast"].sum().reset_index()
agg_forecast.rename(columns={"forecast": "total_forecast"}, inplace=True)

st.write("### Summierte Prognose pro Tag")
st.line_chart(agg_forecast.rename(columns={"date":"index"}).set_index("index")["total_forecast"])

# -------------------------------
# 6️⃣ Aggregierte Prognose pro Store/Item
# -------------------------------
agg_by_store_item = (
    forecast_period.groupby(['store_nbr', 'item_nbr'])['forecast']
    .sum()
    .reset_index()
    .rename(columns={'forecast': 'total_forecast'})
    .sort_values(['store_nbr','item_nbr'])
)

st.write("### Aggregierte Prognose pro Store/Item")
# Anzeige mit slicing: Top 20
# Anzahl Zeilen pro Seite
rows_per_page = 20

# Gesamtanzahl Seiten
total_rows = agg_by_store_item.shape[0]
total_pages = (total_rows // rows_per_page) + 1

# Slider, um die Seite auszuwählen
page = st.slider("Seite auswählen", min_value=1, max_value=total_pages, value=1)

# Berechne Start- und Endindex
start_idx = (page - 1) * rows_per_page
end_idx = start_idx + rows_per_page

# Zeige die entsprechende Seite
st.dataframe(agg_by_store_item.iloc[start_idx:end_idx])
