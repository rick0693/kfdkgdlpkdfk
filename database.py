import pandas as pd
import requests

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
    
    # Selecionando apenas as colunas "roll" e "color"
    selected_columns = ["roll", "color"]
    data = [{col: entry[col] for col in selected_columns} for entry in api_data]
    
    return pd.DataFrame(data)

# Obtendo os dados da API
api_data = get_api_data()

# Criando o DataFrame com as colunas "roll" e "color"
df = create_dataframe(api_data)

# Exibindo o DataFrame resultante
print(df)
