import streamlit as st
import pandas as pd
import requests
import time

# Função para obter os dados da API
def get_api_data():
    url = "https://blaze.com/api/roulette_games/recent/"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return None

# Função para criar um DataFrame com os dados da API
def create_dataframe(api_data):
    if not api_data:
        return pd.DataFrame()
    return pd.DataFrame(api_data)

# Configuração da aplicação Streamlit
st.title("Dados da API em tempo real")
st.write("Atualizando a cada 5 segundos...")

# Loop while para atualizar os dados a cada 5 segundos
while True:
    api_data = get_api_data()
    df = create_dataframe(api_data)

    if not df.empty:
        st.write(df)

    time.sleep(5)  # Espera 5 segundos antes de atualizar novamente
