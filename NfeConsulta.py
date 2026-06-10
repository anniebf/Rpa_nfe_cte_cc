from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
import anticaptcha
import resolvebase64
import json
import database
import DatasMes
import ModificaCsv
import os
from datetime import datetime

hoje = datetime.now()
mesAtual = hoje.month
if mesAtual < 10:
    mesAtual = f'0{mesAtual}'

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
caminho = fr'C:\RPA_NFE_CTE\Sefaz_RPA\downloads\xls'

def mainNfe():
    #setando opçoes no chromedriver
    options = webdriver.ChromeOptions()
    options.add_experimental_option("prefs", {
    "download.default_directory": caminho,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
    })

    #options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--mute-audio')

    driver = webdriver.Chrome(options=options)
    url = "https://www.sefaz.mt.gov.br/acesso/pages/login/login.xhtml"
    driver.implicitly_wait(2)
    driver.get(url)
    LoginEcaptcha(driver)
    loopNfe(driver,lista_filiais)

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
                efetuarLogin.click() 

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

def loopNfe(driver,lista_filiais):
    try:
        for filiais in lista_filiais:
            grupo = filiais[0]
            filial = filiais[1]
            cnpj = filiais[2]

            while True:
            
                '''if len(driver.window_handles) > 1:
                    driver.switch_to.window(driver.window_handles[0])
                    driver.close()'''
                #abre uma nova aba com o link da consulta de nfe
                driver.execute_script("window.open('');")
                sleep(1)

                WebDriverWait(driver, 10).until(lambda driver: len(driver.window_handles) > 1)
                driver.switch_to.window(driver.window_handles[1])
                driver.get('https://www.sefaz.mt.gov.br/nfe/pages/consultaemitidasrecebidas/consultaemitidasrecebidas.xhtml')
                sleep(1)

                #----------------------------------
                #iniciando o preenchimento do dados do contabilista e datas para a consulta
                dadosConsulta(driver,cnpj)
                #----------------------------------

                mensagemErro = None
                try:
                    mensagemErro = WebDriverWait(driver, 5).until(
                        EC.visibility_of_element_located((By.XPATH, "//div[contains(@class, 'ui-dialog-content') and contains(text(), 'Contabilista não representa')]"))
                    )
                except:
                    pass

                if mensagemErro:
                    print(fr'Ocorreu um erro no CNPJ: {cnpj}')
                    sleep(2)
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                    sleep(2)
                    break  
                
                mensagemErroDoc = None
                try:
                    mensagemErroDoc = WebDriverWait(driver, 5).until(
                        EC.visibility_of_element_located((By.XPATH, "//div[contains(text(),'Documento deve ser informado')]"))
                    )
                except:
                    pass

                if mensagemErroDoc:
                    print(fr'Ocorreu um erro no CNPJ: {cnpj} na hora de colocar o CNPJ no site')
                    sleep(2)
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                    sleep(2)
                    continue  

                mensagemErroData = None
                try:
                    mensagemErroData = WebDriverWait(driver, 5).until(
                        EC.visibility_of_element_located((By.XPATH, "//div[contains(text(),'Data inválida')]"))  # ajuste aqui se necessário
                    )
                except:
                    pass

                if mensagemErroData:
                    print(fr'Ocorreu um erro no CNPJ: {cnpj} na hora de colocar as datas no site')
                    sleep(2)
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                    sleep(2)
                    continue 
                
                try:
                    exportarExcel = None
                    exportarExcel = WebDriverWait(driver, 10).until(
                            EC.visibility_of_element_located((By.XPATH, "//a[text()='Exportar para Excel']"))
                    )
                except:
                    pass
                    
                if exportarExcel:
                    exportarExcel.click()
                    caminhoPadrao = fr'C:\SPED_fiscal\Consulta de NF-e EmitidaRecebida\mes_{mesAtual}'
#------------------------------------------------------------------
#Fazendo modificacoes do arquivo baixado
                    print('clicado para exportar')
                    sleep(15)
                    try:
                        nomeAruivoAtual = modificaCsv.coverterExcelpCsv('Nfe', grupo, filial)
                        print(fr"criado o arquivo {nomeAruivoAtual}")
                        import shutil
                        if os.path.isfile(fr'downloads\csv\mes_{mesAtual}\{nomeAruivoAtual}'):
                            tamanhoCsv = os.path.getsize(fr'downloads\csv\mes_{mesAtual}\{nomeAruivoAtual}')

                            if tamanhoCsv > 20.48:
                                print(f'O arquivo  é maior que 1024 bytes.')

                                shutil.copy(fr'downloads\csv\mes_{mesAtual}\{nomeAruivoAtual}', fr'{caminhoPadrao}\{nomeAruivoAtual}')
                     
                                print(fr"Arquivo foi copiado para a pasta: {caminhoPadrao}\{nomeAruivoAtual}'")                          
                                driver.close()
                                driver.switch_to.window(driver.window_handles[0])
                                print('janela fechada')
                                break
                            else:
                                print(f'O arquivo  não é maior que 1024 bytes.')
                                driver.close()
                                driver.switch_to.window(driver.window_handles[0])
                                break
                        else:
                            print(f'O arquivo  nao existe no diretorio')
                            driver.close()
                            driver.switch_to.window(driver.window_handles[0])
                            break

                    except Exception as e:
                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])
                        print(e)
                        break
#------------------------------------------------------------------
    except Exception as e:
        print(e)
        driver.close()
        driver.switch_to.window(driver.window_handles[0])   


#------------------dados da consulta-------------------
#Essa funçao preenche os dados da Consulta de NF-e Emitida/Recebida
def dadosConsulta(driver,cnpj):
    botaoInsc = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.XPATH, "//label[text()='Inscrição Estadual']"))
    )
    botaoInsc.click()

    insc = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.XPATH, "//li[text()='CNPJ']"))
    )
    insc.click()
    sleep(2)
    inputCnpj = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.XPATH, "//div[@class='ui-panel-content ui-widget-content']//input[contains(@class, 'ui-inputmask')]"))
    )

    sleep(5)
    inputCnpj.click()
    inputCnpj.send_keys(cnpj)

    sleep(3)
    dataInicial = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.XPATH, "(//input[contains(@class, 'hasDatepicker')])[1]"))
    )
    sleep(2)
    dataInicial.click()
    dataInicial.send_keys(data_inicio)

    dataFinal = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.XPATH, "(//input[contains(@class, 'hasDatepicker')])[2]"))
    )
    sleep(2)
    dataFinal.click()
    sleep(2)
    dataFinal.send_keys(data_fim)

    conusltar = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.XPATH, "//button[.//span[text()='Consultar']]"))
    )
    sleep(2)
    conusltar.click()
    return

if __name__ == "__main__":
    mainNfe()