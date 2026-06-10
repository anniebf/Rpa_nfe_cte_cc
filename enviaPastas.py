import os
import re
import shutil
from datetime import datetime

# Caminhos
base_path = r'C:\Sefaz_RPA'
origem_dir = r'downloads\csv'

# Tipos e seus respectivos diretórios
tipos = {
    'NFe': r'Consulta de NF-e EmitidaRecebida',
    'CTe': r'Consulta de CT-e EmitidaRecebida'
}

# Mês atual com dois dígitos
hoje = datetime.now()
mes_atual = f'{hoje.month:02d}'

# Criar apenas as pastas do mês atual se não existirem
for tipo_pasta in tipos.values():
    nome_pasta = f'Mes_{mes_atual}'
    caminho = os.path.join(base_path, tipo_pasta, nome_pasta)
    if not os.path.exists(caminho):
        os.makedirs(caminho)

# Buscar o arquivo mais recente na origem
arquivos = [os.path.join(origem_dir, f) for f in os.listdir(origem_dir) if os.path.isfile(os.path.join(origem_dir, f))]

if not arquivos:
    print("Nenhum arquivo encontrado na pasta de origem.")
else:
    arquivo_mais_recente = max(arquivos, key=os.path.getmtime)
    nome_arquivo = os.path.basename(arquivo_mais_recente)
    print(f"Arquivo mais recente encontrado: {nome_arquivo}")

    # Detectar tipo (NFe ou CTe)
    match = re.match(r'^(NFe|CTe)_', nome_arquivo)
    if not match:
        print("Formato do nome do arquivo inválido. Esperado: NFe_algo_082025 ou CTe_algo_082025")
    else:
        tipo_doc = match.group(1)
        tipo_destino = tipos[tipo_doc]

        # Caminho destino usando mês atual
        destino_pasta = os.path.join(base_path, tipo_destino, f'Mes_{mes_atual}')
        os.makedirs(destino_pasta, exist_ok=True)

        destino = os.path.join(destino_pasta, nome_arquivo)
        shutil.copy(arquivo_mais_recente, destino)
        print(f"Arquivo copiado para: {destino}")
