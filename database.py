import streamlit as st
import requests
import pytz
from datetime import datetime
from dateutil import parser
import time
import pandas as pd
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

# Inicialize o SDK do Firebase com suas credenciais
cred = credentials.Certificate('bancoblaze-firebase-adminsdk-e6pzh-9213df4821.json')
firebase_admin.initialize_app(cred)

# Inicialize o cliente do Firestore
db = firestore.client()

valor_inicial = 0.10
maior_valor_inicial = 0.10

def obter_novo_dado(dados_api, ultimo_server_seed):
    novo_server_seed = dados_api[0]["server_seed"]

    if novo_server_seed != ultimo_server_seed:
        color4 = dados_api[3]["color"]
        color1 = dados_api[2]["color"]
        color2 = dados_api[1]["color"]
        color3 = dados_api[0]["color"]
        numero4 = dados_api[3]["roll"]
        numero1 = dados_api[2]["roll"]
        numero2 = dados_api[1]["roll"]
        numero3 = dados_api[0]["roll"]

        created_at = dados_api[0]["created_at"]

        retorno = verificar_numero(numero1, numero3)  # Obtém o valor de retorno

        return color1, color2, color3, color4, numero1, numero2, numero3, created_at, novo_server_seed, retorno

    return None

rodada = 1

def verificar_numero(numero2, numero3):
    global rodada

    if rodada % 2 == 0:
        rodada += 1
        return 2
    else:
        rodada += 1
        return 1
    
def make_request():
    response = requests.get("https://blaze.com/api/roulette_games/recent")
    data = response.json()
    sorted_data = sorted(data, key=lambda x: x['created_at'], reverse=True)
    return sorted_data

def converter_para_horario_brasilia(created_at):
    fuso_horario_utc = pytz.timezone('UTC')
    fuso_horario_brasilia = pytz.timezone('America/Sao_Paulo')
    horario_utc = parser.isoparse(created_at)
    horario_utc = horario_utc.replace(tzinfo=fuso_horario_utc)
    horario_brasilia = horario_utc.astimezone(fuso_horario_brasilia)
    return horario_brasilia.strftime("%Y-%m-%d %H:%M:%S")

# Cria um DataFrame vazio para armazenar os dados existentes
existing_dataframe = pd.DataFrame()

def armazenar_dados_firestore(dados):
    doc_ref = db.collection('teste1').document()
    doc_ref.set(dados)
    st.write("Dados armazenados no Firestore:", dados)

def save_to_dataframe(data, retorno):
    global existing_dataframe

    most_recent_entry = data[0]
    server_seed = most_recent_entry.get('server_seed', '')
    color = most_recent_entry.get('color', '')
    roll = most_recent_entry.get('roll', '')
    created_at = converter_para_horario_brasilia(most_recent_entry.get('created_at', ''))

    df = pd.DataFrame({
        'server_seed': [server_seed],
        'color': [color],
        'roll': [roll],
        'created_at_brasilia': [created_at],
        'retorno': [retorno],
        'resultado': ['']  # Nova coluna com valores em branco
    })

    df_concatenated = pd.concat([existing_dataframe, df], ignore_index=True)
    df_concatenated = df_concatenated.sort_values(by='created_at_brasilia', ascending=False)
    df_concatenated = df_concatenated.reset_index(drop=True)

    existing_dataframe = df_concatenated.copy()

    if len(existing_dataframe) > 1:
        color_last = existing_dataframe.loc[0, "color"]
        retorno_last = existing_dataframe.loc[1, "retorno"]

        if color_last == retorno_last:
            existing_dataframe.loc[0, "resultado"] = "Ganhou"
        else:
            existing_dataframe.loc[0, "resultado"] = "Perdeu"

    # Contagem de 'Perdeu' consecutivas
    consecutivo = 0
    maior_consecutivo = 0

    for i in range(len(existing_dataframe)):
        if existing_dataframe.loc[i, 'resultado'] == 'Perdeu':
            consecutivo += 1
            if consecutivo > maior_consecutivo:
                maior_consecutivo = consecutivo
        else:
            consecutivo = 0

    # Contagem de 'Perdeu' consecutivas
    count_perdeu_consecutivas = 0
    for i in range(len(existing_dataframe)):
        if existing_dataframe.loc[i, "resultado"] == "Perdeu":
            count_perdeu_consecutivas += 1
        else:
            break

    if count_perdeu_consecutivas == 0:
        resultado_aposta = valor_inicial
        st.write('Valor da aposta:', resultado_aposta)
    else:
        valor_aposta = valor_inicial * (2 ** count_perdeu_consecutivas)
        resultado_aposta = valor_aposta
        st.write('Aposta na cor:', valor_aposta)

    existing_dataframe.loc[0, "aposta"] = resultado_aposta  # Adiciona o valor de resultado_aposta à coluna "aposta"

    st.write(existing_dataframe)
    st.write("Quantidade de 'Perdeu' consecutivas:", count_perdeu_consecutivas)
    st.write("Maior sequência consecutiva de 'Perdeu':", maior_consecutivo)

    # Verifica se o DataFrame foi atualizado
    if len(existing_dataframe) > 0:
        novo_dado = existing_dataframe.loc[0].to_dict()
        armazenar_dados_firestore(novo_dado)

def check_server_seed(previous_server_seed):
    request_count = 0

    while True:
        request_count += 1
        try:
            data = make_request()
            new_data = obter_novo_dado(data, previous_server_seed)
            if new_data:
                color1, color2, color3, color4, numero1, numero2, numero3, created_at, server_seed, retorno = new_data
                created_at_brasilia = converter_para_horario_brasilia(created_at)
                save_to_dataframe(data, retorno)

                previous_server_seed = server_seed
            else:
                time.sleep(1)  # Espera 10 segundos antes de fazer uma nova requisição

        except requests.exceptions.RequestException as e:
            time.sleep(1)  # Espera 10 segundos antes de fazer uma nova requisição

def main():
    st.title('Exemplo de exibição de dados com Streamlit')
    st.write("Clique no botão abaixo para atualizar os dados.")

    previous_server_seed = ''
    check_server_seed(previous_server_seed)

if __name__ == '__main__':
    main()
