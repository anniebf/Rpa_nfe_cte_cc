from datetime import datetime, timedelta

def gerar_intervalo_datas():
    hoje = datetime.now()
    ano = hoje.year
    mes = hoje.month
    dia = hoje.day

    #if dia < 10:
    # Pega o mês anterior
    primeiro_dia_anterior = datetime(ano, mes, 1) - timedelta(days=1)
    mes_anterior = primeiro_dia_anterior.month
    ano_anterior = primeiro_dia_anterior.year

    # Primeiro e último dia do mês anterior
    primeiro_dia = datetime(ano_anterior, mes_anterior, 1)
    ultimo_dia = primeiro_dia_anterior
    '''else:
        # Primeiro dia do mês atual
        primeiro_dia = datetime(ano, mes, 1)

        # Primeiro dia do próximo mês
        if mes == 12:
            proximo_mes = 1
            proximo_ano = ano + 1
        else:
            proximo_mes = mes + 1
            proximo_ano = ano'''

    #primeiro_dia_proximo_mes = datetime(proximo_ano, proximo_mes, 1)
    # Último dia do mês atual = dia anterior ao primeiro do próximo mês
    #ultimo_dia = primeiro_dia_proximo_mes - timedelta(days=1)

    # Formata as datas no padrão "ddmmyyyy"
    data_inicio = primeiro_dia.strftime("%d%m%Y")
    data_fim = ultimo_dia.strftime("%d%m%Y")

    return data_inicio, data_fim

# Teste
print(gerar_intervalo_datas())

if __name__ == "__main__":
    gerar_intervalo_datas()
