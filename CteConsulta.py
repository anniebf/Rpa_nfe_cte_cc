import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
import anticaptcha
import glob 
import resolvebase64
import json
import database
import DatasMes
import ModificaCsv
import pandas as pd
import shutil
import os
from datetime import datetime

hoje = datetime.now()
mesAtual = int(hoje.month) 
anoAtual = hoje.year
dia = hoje.day

print(f"Mês identificado: {mesAtual}") # Verifique se aparece '1' no console

if mesAtual == 1:
    print("Sucesso: Entrou no bloco de Janeiro")
    mesAnterior = 12
    anoAnterior = anoAtual - 1
else:
    print("Entrou no bloco Else")
    mesAnterior = mesAtual - 1
    anoAnterior = anoAtual

#pega as informacoes que estao no json
#--------------json----------------
with open('json\contabilista.json', 'r') as file:
    dados = json.load(file)
userContabilista = dados["Contabilista"]
senhaContabilista = dados["SenhaContabilista"]

#setando datas de consulta
#---------------data-------------------
data_inicio, data_fim = DatasMes.gerar_intervalo_datas()

#---------------------------------------
#pegando uma lista com o grupo, filliais e cnpj do banco de dados
lista_filiais = database.retornoCnpj()

#-----------caminho download-------------------
caminhoDownload = fr'C:\Sefaz_RPA\downloads\csv'

def mainCte():
    #setando opçoes no chromedriver
    options = uc.ChromeOptions()
    options.add_experimental_option("prefs", {
    "download.default_directory": caminhoDownload,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True,
    "plugins.always_open_pdf_externally": True
    })

    #options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--mute-audio')
    options.add_argument("--disable-popup-blocking")

    driver = uc.Chrome(options=options)
    url = "https://www.sefaz.mt.gov.br/acesso/pages/login/login.xhtml"
    driver.implicitly_wait(2)
    driver.maximize_window()
    driver.get(url)

    LoginEcaptcha(driver)
    loopCTE(driver,lista_filiais)

#----------Comecando login----------------
def LoginEcaptcha(driver):
    try:
        tipoUsuario = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'formLogin:selectTipoUsuario_label')))
        tipoUsuario.click()

        # Depois espera o item 'Contabilista' ficar visível e clica
        contabilista = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, 'formLogin:selectTipoUsuario_1')))

        contabilista.click() 
        sleep(2)
        #tenta resolver o captcha 5x, caso nao consiga, ele fecha o programa
        cnpjs = database.retornoCnpj()
        for x in range(5):
            try:
                crc = WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located((By.ID, 'formLogin:inputLogin'))
                )
                crc.clear()
                sleep(1)
                crc.send_keys(userContabilista)

                senha = WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located((By.ID, 'formLogin:inputSenha'))
                )
                senha.clear()
                senha.send_keys(senhaContabilista)
                sleep(2)

#------------------------------------------------------
                #resolvendo o captcha na sefaz
                captcha_element = driver.find_element(By.XPATH, '//img[contains(@src, "data:image/png;base64")]')
                # Pegando o atributo src
                src = captcha_element.get_attribute('src')
                #print(src)
                #o decode64 pega a imagem que vem em base 64 e converte em jpg
                resolvebase64.decode64(src)
                sleep(1)
                #anticaptcha resolve o captch
                captcha = anticaptcha.anticaptcha()

                print(captcha)

                #a enviar captcha resolvido
                captchaResolvido = WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located((By.ID, 'formLogin:inputCaptcha'))
                )
                captchaResolvido.clear()
                captchaResolvido.send_keys(captcha)
                sleep(2)               

                efetuarLogin = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Efetuar Login')]"))
                )
                location = efetuarLogin.location
                size = efetuarLogin.size
                x_coord = int(location['x'] + (size['width'] / 2))
                y_coord = int(location['y'] + (size['height'] / 2))

                print(f"Disparando clique nativo por CDP em: X={x_coord}, Y={y_coord}")
                driver.execute_cdp_cmd("Input.dispatchMouseEvent", {
                    "type": "mousePressed",
                    "x": x_coord,
                    "y": y_coord,
                    "button": "left",
                    "clickCount": 1
                })
                sleep(0.5)  # Micro-atraso simulando comportamento humano
                driver.execute_cdp_cmd("Input.dispatchMouseEvent", {
                    "type": "mouseReleased",
                    "x": x_coord,
                    "y": y_coord,
                    "button": "left",
                    "clickCount": 1
                })
                sleep(2)

#-----------------------------------
                #Verifica se ocorreu algum erro
                #se eocorreu tenta novamente
                try:
                    erro = None
                    erro = WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located((By.CLASS_NAME, 'ui-messages-error')))
                except:
                    pass
                if erro:
                    continue

#-----------------------------------
                #tenta ver se existe a tela de sessao duplicada
                #se a sessao esta duplicada, substitue e acessa            
                try:
                    outraSessaoAberta = None
                    outraSessaoAberta = WebDriverWait(driver, 10).until(
                        EC.visibility_of_element_located((By.XPATH, "//*[contains(@id, 'superPanelMensagem')]"))
                    )
                except:
                    pass
                if outraSessaoAberta:
                    senhaSessao = WebDriverWait(driver, 10).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, "input[type='password'].ui-password"))
                    )
                    senhaSessao.send_keys(senhaContabilista)

                    substituir  = WebDriverWait(driver, 10).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, "input.btnPadrao[value='Substituir']"))
                    )
                    substituir.click()
                    break
#---------------------------

                try:
                    telaInicial = None 
                    telaInicial = WebDriverWait(driver, 10).until(
                        EC.visibility_of_element_located((By.ID, "tst"))
                    )
                except:
                    pass
                
                if telaInicial:
                    break
                else:
                    pass
        
            except:
                pass
        print('Pasou do login com exito!')
        #print(cnpjs)
    except Exception as e:
        print('Erro ao tentar logar')
        print(e)

#---------------------------
#1-Essa funçao abre uma abre uma aba para conseguir acessar a consulta de NFe
#2-chama outra funcao que preenche os dados
#3-e faz o download do arquivo

def loopCTE(driver,lista_filiais):
    try:
        for filiais in lista_filiais:
            grupo = filiais[0]
            filial = filiais[1]
            cnpj = filiais[2]
            codigoFilial = filiais[3]

            while True:
                #escreveLog('CTE',"...")
                #escreveLog('CTE',fr"Cnpj: {cnpj} atualmente sendo executado...")
                '''if len(driver.window_handles) > 1:
                    driver.switch_to.window(driver.window_handles[0])
                    driver.close()'''
                #abre uma nova aba com o link da consulta d
                driver.execute_script("window.open('');")
                sleep(1)

                WebDriverWait(driver, 10).until(lambda driver: len(driver.window_handles) > 1)
                driver.switch_to.window(driver.window_handles[1])
                driver.get('https://www.sefaz.mt.gov.br/cte/portal/consultaremitidorecebido')
                sleep(3)
                #escreveLog('CTE',"Abrindo nova aba")

                #----------------------------------
                #iniciando o preenchimento do dados do contabilista e datas para a consulta
                #escreveLog('CTE',"--Prenchimento dos dados do cte")    
                botaoInsc = WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located((By.XPATH, '//*[@id="tipoConsulta"]'))
                )
                botaoInsc.click()
                sleep(2)

                insc = WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located((By.XPATH, '//*[@id="tipoConsulta"]/option[4]'))
                )
                insc.click()
                #escreveLog('CTE',"Inscrição Estadual selecionada")    
                
                sleep(2)
                # Localiza o elemento select pelo id
                select_element = driver.find_element(By.ID, "idenTomador")

                # Cria objeto Select
                select = Select(select_element)

                # Seleciona a opção pelo valor "2"
                select.select_by_value("2")

                # WebDriverWait(driver, 10).until(
                #     EC.visibility_of_element_located((By.XPATH, '//*[@id="idenTomador"]/option[3]'))
                # ).click()
                # sleep(2)

                # inputCnpj.click()
                # inputCnpj.send_keys(cnpj)
                sleep(3)
                print(cnpj)
                # preenche com com cnpj
                cnpj_login = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, '//*[@id="campoCnpjTomador"]'))
                )
                cnpj_login.click()
                cnpj_login.send_keys(cnpj)
                #escreveLog('CTE',"CNPJ preenchido")    
                
                sleep(2)

                dataInicial = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, '//*[@id="tabelaFiltro"]/table/tbody/tr[1]/td[2]/input[1]'))
                )

                sleep(2)


                dataInicial.click()
                dataInicial.send_keys(data_inicio)

                dataFinal = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, '//*[@id="tabelaFiltro"]/table/tbody/tr[1]/td[2]/input[2]'))
                )

                sleep(2)
                dataFinal.click()
                sleep(2)
                dataFinal.send_keys(data_fim)
                #escreveLog('CTE',"Datas preenchidas") 
                conusltar = WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located((By.XPATH, '//*[@id="btnConsultar"]'))
                )
                sleep(2)
                conusltar.click()   
                
                sleep(5)
                try:
                    registroNone =WebDriverWait(driver, 10).until(
                        EC.visibility_of_element_located((By.XPATH,'/html/body/center/form/table[2]/tbody/tr/td'))
                    )
                    registroNone = registroNone.text
                    #print(registroNone)
                    if registroNone =='Não foram encontrados registros para a consulta solicitada.':
                        print("Não foram encontrados registros para a consulta solicitada.")
                        #escreveLog('CTE',"Não foram encontrados registros para a consulta solicitada.")
                        sleep(2)
                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])
                        print('erro de registro')
                        print('fechando aba')
                        sleep(2)
                        break
                except:
                    pass

                try:
                    verificar = WebDriverWait(driver, 10).until(
                        EC.visibility_of_element_located((By.XPATH, '/html/body/center/table[3]/tbody/tr/td/ul/li'))
                    )

                    verificarText = verificar.text
                    if verificarText == 'Acesso não permitido. Problemas com o banco de dados (null)':
                        print('Acesso não permitido. Problemas com o banco de dados (null)')
                        #escreveLog('CTE',"Acesso não permitido. Problemas com o banco de dados (null)")
                        
                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])
                        print('fechando aba')
                        sleep(2)
                        break
                    if verificarText == 'Não foi possível encontrar o contribuinte pelo seu documento de identificação representado pelo contabilista.':
                        print('Não foi possível encontrar o contribuinte pelo seu documento de identificação representado pelo contabilista.')
                        #escreveLog('CTE',"Não foi possível encontrar o contribuinte pelo seu documento de identificação representado pelo contabilista.)")
                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])
                        print('fechando aba')
                        sleep(2)
                        break
                    
                except:
                    # Se não achou o elemento
                    print("nada de erro")
                    #escreveLog('CTE',"Dados inserido com sucesso")
                    
                    pass
                #----------------------------------


                #espera o botao de download 
                #TROCAR O XPATH DO BOTAO DE DOWNLOAD PARA O DO CTE E FAZER AS ETAPAS ABAIXO 

                try:
                    exportarExcel = None
                    exportarExcel = WebDriverWait(driver, 10).until(
                            EC.visibility_of_element_located((By.XPATH, '//*[@id="btnGerarExcelConsulta"]'))
                    )
                except:
                    pass
                    
                if exportarExcel:
                    exportarExcel.click()
                    #escreveLog('CTE',"Baixando arquivo xls")
                    sleep(15)
                    padrao = os.path.join(caminhoDownload, "*ConsultaCteEmitidoRecebido*")
                    # Lista todos os arquivos que correspondem
                    arquivoscte = glob.glob(padrao)
                    if arquivoscte:
                        # Pega o mais recente
                        arquivo_mais_recente = max(arquivoscte, key=os.path.getmtime)
                        print("Arquivo encontrado:", arquivo_mais_recente)
                        #escreveLog('CTE',"Arquivo baixado com sucesso!")
                        
                    else:
                        print("Nenhum arquivo encontrado.")
                        #escreveLog('CTE',"Nennhum arquivo encontrado para realizar o download")
                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])
                        print('fechando aba')
                        break
                    caminhoPadrao = fr'C:\Sefaz_RPA\Consulta de CT-e EmitidaRecebida\mes_{mesAtual:02d}'
                    #Fazendo modificacoes do arquivo baixado
                    print('clicado para exportar')
                    #sleep(15)
                    try:
                        nomeArquivo = fr"CTE_GRUPO-{grupo}_FILIAL-{codigoFilial}_{mesAtual}.{anoAtual}.csv"

                        #le o excel e converte em csv
                        read = pd.read_excel(arquivo_mais_recente)
                        read.to_csv(fr"C:\Sefaz_RPA\downloads\csv\{nomeArquivo}", index=False)
                        #le as linhas do csv
                        df = pd.read_csv(fr"C:\Sefaz_RPA\downloads\csv\{nomeArquivo}",index_col=None)

                        # Exclui as 5 primeiras linhas
                        df = df.iloc[5:]
                        df.replace(' " ', "")
                        print('tira as primeiras 5 linhas do csv')
                        # Salva o DataFrame modificado em um novo arquivo CSV
                        df.to_csv(fr"C:\Sefaz_RPA\downloads\csv\{nomeArquivo}", header=False, index=False, sep=';')
                        #remove o ultimo download feito deixando somente o csv 
                        os.remove(arquivo_mais_recente)
                        print("removido o ultimo arquivo do downloads")

                        if os.path.isfile(fr'C:\Sefaz_RPA\downloads\csv\{nomeArquivo}'):
                            tamanhoCsv = os.path.getsize(fr'C:\Sefaz_RPA\downloads\csv\{nomeArquivo}')

                            if tamanhoCsv > 20.48:
                                #escreveLog('CTE',"Arquivo NAO esta corrompido")
                                
                                print(f'O arquivo  é maior que 1024 bytes.')
                                print(f'Arquivo modificado e salvo como: {nomeArquivo}')
                                print(fr'{caminhoPadrao}\{nomeArquivo}')

                                shutil.copy(fr'C:\Sefaz_RPA\downloads\csv\{nomeArquivo}', fr'{caminhoPadrao}\{nomeArquivo}')
                                #escreveLog('CTE',fr"Arquivo: {nomeArquivo} copiado para: {caminhoPadrao}")

                                print(fr"Arquivo foi copiado para a pasta: {caminhoPadrao}\{nomeArquivo}'")                          
                                driver.close()
                                driver.switch_to.window(driver.window_handles[0])
                                print('tudo certo')
                                sleep(2)
                                break
                            else:
                                print(f'O arquivo  não é maior que 1024 bytes.')
                                ##escreveLog('CTE',"Arquivo ESTA corrompido")
                                
                                driver.close()
                                driver.switch_to.window(driver.window_handles[0])
                                print('fechando aba')
                                break
                        else:
                            print(f'O arquivo  nao existe no diretorio')
                            ##escreveLog('CTE',"Arquivo NAO existe no diretorio")
                            driver.close()
                            driver.switch_to.window(driver.window_handles[0])
                            print('fechando aba')
                            break

                    except Exception as e:
                        
                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])
                        print(e)
                        print('fechando aba')
                        break
#------------------------------------------------------------------
    except Exception as e:

        print(e)
        driver.close()
        driver.switch_to.window(driver.window_handles[0])   


if __name__ == "__main__":
    mainCte()