import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import plotly.express as px


DATA_URL = ("https://data.cityofnewyork.us/resource/h9gi-nx95.csv")

st.title("Vehicle Collisions in NYC")

@st.cache(persist=True)
def load_data(nrows):
    data = pd.read_csv(DATA_URL, nrows=nrows, parse_dates=[['CRASH DATE', 'CRASH TIME']])
    data.dropna(subset=['LATITUDE', 'LONGITUDE'], inplace=True)
    lowercase = lambda x: str(x).lower()
    data.rename(lowercase, axis='columns', inplace=True)
    data.rename(columns={'crash date_crash time': "date/time",
                         'number of pedestrians injured': 'pedestrians_injured',
                         'number of cyclist injured': 'cyclists_injured',
                         'number of motorist injured': 'motorists_injured',
                         'on street name': 'street', }, inplace=True)
    data['date/time'] = pd.to_datetime(data['date/time'])
    return data


data = load_data(100000)
original_data = data

injured_people = st.slider("Number of injured persons", 0, 12)

st.map(data.query('`number of persons injured` >= @injured_people')[['latitude', 'longitude']].dropna(how="any"))

st.header("How many collisions occur during a given time of day?")
hour = st.slider("Hour to look at", 0, 23)

data = data[data['date/time'].dt.hour == hour]

st.markdown(f'Colissions between {hour} and {(hour + 1) % 24}')

midpoint = (np.average(data['latitude']), np.average(data['longitude']))

st.write(pdk.Deck(
    map_style="mapbox://styles/mapbox/light-v9",
    initial_view_state={
        "latitude": midpoint[0],
        "longitude": midpoint[1],
        "zoom": 11,
        "pitch": 50,
    },
    layers=[
        pdk.Layer(
            "HexagonLayer",
            data=data[['date/time', 'latitude', 'longitude']],
            get_position=['longitude', 'latitude'],
            radius=50,
            extruded=True,
            pickable=True,
            elevation_scale=5,
            elevation_range=[10, 1000],
        ),
    ]
))

st.subheader(f'Breakdown by minute between {hour} and {(hour+1)%24}')

filtered = data[
    (data['date/time'].dt.hour >= hour) & (data['date/time'].dt.hour < (hour+1))
]

hist = np.histogram(filtered['date/time'].dt.minute, bins=61, range=(0,60))[0]

chart_data = pd.DataFrame({'minute': range(61), 'crashes': hist})

fig = px.bar(chart_data, x='minute', y='crashes', hover_data=['minute', 'crashes'], height=400)
st.write(fig)

st.header('Top 5 most dangerous streets')
select = st.selectbox('Affected type of people', ['Pedestrians', 'Cyclists', 'Motorists'])
select = select.lower()
st.write(data.query(f'{select}_injured >= 1')[['street', f'{select}_injured']].sort_values(by=[f'{select}_injured'], ascending=False).dropna(how='any')[:5])

if st.checkbox('Show Raw Data', False):
    st.subheader('Raw Data')
    st.write(data)
