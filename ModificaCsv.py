import os
import pandas as pd
from datetime import datetime

hoje = datetime.now()
ano = hoje.year
mes = hoje.month
if mes < 10:
    mes = f'0{mes}'

usuario = os.getlogin()
caminhoxls = fr'downloads\xls'
caminhocsv = fr'downloads\xls'


def ultimoArquivoDownloads():
    # Atualiza a lista de arquivos a cada chamada
    lista = os.listdir(caminhoxls)
    lis_dat = []
    for arquivo in lista:
        caminho_arquivo = fr"{caminhoxls}/{arquivo}"
        if os.path.isfile(caminho_arquivo):  # Garante que é arquivo
            data = os.path.getmtime(caminho_arquivo)
            lis_dat.append((data, arquivo))

    # Verifica se encontrou arquivos
    if not lis_dat:
        print("Nenhum arquivo encontrado.")
        return None

    # Ordena e retorna o mais recente
    lis_dat.sort(reverse=True)
    ult_arq = lis_dat[0]
    print(f"Último arquivo: {ult_arq}")
    return ult_arq

def coverterExcelpCsv(consulta,grupo,filial):
    nomeArquivo = f"{consulta}_{grupo}_{filial.strip()}_{mes}_{ano}.csv"

    ultimoArq  =  ultimoArquivoDownloads()
    #le o excel e converte em csv
    read = pd.read_excel(fr"{caminhoxls}\{ultimoArq[1]}")
    read.to_csv(fr"downloads\csv\mes_{mes}\{nomeArquivo}", index=False)
    #le as linhas do csv
    df = pd.read_csv(fr"downloads\csv\mes_{mes}\{nomeArquivo}",index_col=None)

    # Exclui as 5 primeiras linhas
    df = df.iloc[5:]
    df.replace(' " ', "")
    print('tira as primeiras 5 linhas do csv')
    # Salva o DataFrame modificado em um novo arquivo CSV
    df.to_csv(fr"downloads\csv\mes_{mes}\{nomeArquivo}", header=False, index=False, sep=';')
    #remove o ultimo download feito deixando somente o csv 
    os.remove(fr"{caminhoxls}\{ultimoArq[1]}")
    print("removido o ultimo arquivo do downloads")

    return nomeArquivo

if __name__ == "__main__":
    coverterExcelpCsv('','','')    