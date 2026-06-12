import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
import anticaptcha
import resolvebase64
import json
import database
import DatasMes
import ModificaCsv
import base64
import os
import shutil
#from #escreveLog import #escreveLog
from datetime import datetime

from datetime import datetime

hoje = datetime.now()
# Garantimos que mesAtual seja um INTEIRO
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

# Para garantir os dois caracteres que você precisa na string:
mes_formatado = f"{mesAnterior:02d}"

print(f"Mês Anterior Formatado: {mes_formatado}")
print(f"Ano Anterior: {anoAnterior}")

#pega as informacoes que estao no json
#--------------json----------------
with open('json\contabilista.json', 'r') as file:
    dados = json.load(file)
userContabilista = dados["Contabilista"]
senhaContabilista = dados["SenhaContabilista"]

#setando datas de consulta
#---------------data-------------------
mesPassado, anoPassado = DatasMes.dataContaCorrente()

#---------------------------------------
#pegando uma lista com o grupo, filliais e cnpj do banco de dados
lista_InscEstd = database.retornoInscEstd()

#-----------caminho download-------------------
caminho = fr'S:\Sefaz_RPA\downloads\pdf'


def mainCC():
    ##escreveLog('CC',"INICIANDO...")
    
    #setando opçoes no chromedriver
    options = uc.ChromeOptions()
    options.add_experimental_option("prefs", {
    "download.default_directory": caminho,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
    })

    #options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--mute-audio')
    options.add_argument("--disable-popup-blocking")
    driver = uc.Chrome(options=options)
    sleep(2)
    url = "https://www.sefaz.mt.gov.br/acesso/pages/login/login.xhtml"
    driver.implicitly_wait(2)
    driver.get(url)
    try:
        LoginEcaptcha(driver)
        loopNfe(driver,lista_InscEstd)
        driver.quit()
        ##escreveLog('CC',"...FINALIZANDO")
    except:
        driver.quit()
        ##escreveLog('CC',"...FINALIZANDO")
        

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
                    EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/div[3]/div/div[2]/div/div/form/div[3]/div[5]/div/button"))
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


def loopNfe(driver,lista_InscEstd):
    try:
        for InscEstd in lista_InscEstd:

            while True:
            
                #escreveLog('CC',fr"Cnpj: {InscEstd} atualmente sendo executado...")

                #abre uma nova aba com o link da consulta de nfe
                driver.execute_script("window.open('');")
                sleep(1)

                WebDriverWait(driver, 10).until(lambda driver: len(driver.window_handles) > 1)
                driver.switch_to.window(driver.window_handles[1])
                driver.get('https://www.sefaz.mt.gov.br/ccfiscal/lancamento/consulta')
                sleep(1)
                #escreveLog('CC',"Abrindo nova aba")
                dadosInscEstd(driver,InscEstd)
                #escreveLog('CC',fr"Cnpj: {InscEstd} atualmente foi concluida...")
                sleep(1)
                break
    except Exception as e:
        print(e)
        pass

def dadosInscEstd(driver,InscEstd):
    #escreveLog('CC',"Prenchendo dados da  consulta de conta corrente")
    
    inscricaoEstadual = InscEstd[0].strip()
    filial = InscEstd[1].strip()
    codfilial = InscEstd[2]
    grupo = InscEstd[3]
    
    NumDoc = WebDriverWait(driver, 30).until(
        EC.visibility_of_element_located((By.NAME, "numeroPessoaContribuinte")))
    NumDoc.send_keys(inscricaoEstadual)

    select_mes = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.NAME, "mesInicio")))
    selectMes = Select(select_mes)
    selectMes.select_by_value(str(mesPassado))

    select_ano = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.NAME, "anoInicio")))
    selectAno = Select(select_ano)
    selectAno.select_by_value(str(anoPassado))

    pesquisarNumDoc = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.NAME, "bttnPesquisar")))
    pesquisarNumDoc.click()

    sleep(5)

    try:
        elemento = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Erro inesperado')]")))
        
        print("Elemento encontrado:", elemento.text)
        #escreveLog('CC',FR"ERRO: {elemento.text}")
        
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
        print('aba fechada')
    except:

        pesquisar = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.NAME, "botaoConfirmar")))
        pesquisar.click()
        sleep(5)
        driver.execute_script("document.body.style.zoom = '40%'")
        pdf = driver.execute_cdp_cmd("Page.printToPDF", {
            "printBackground": True,
             "landscape": True
        })
        #escreveLog('CC',FR"Salvando pagina como pdf")
        
        #------------------------------------
        # salvando pagina para pdf
        #------------------------------------
        caminhoInsc = fr"downloads\\pdf\\Conta_Corrente_{mesAnterior}.{anoAtual}_{codfilial}.pdf"
        if dia < 22:
            nomeArquivo = fr'CONTA_CORRENTE_{mesAnterior}.{anoAnterior}_EMP_{grupo}_FILIAL_{codfilial}.pdf'
        else:
            nomeArquivo = fr'CONTA_CORRENTE_APOS_SPED_{mesAnterior}.{anoAnterior}_EMP_{grupo}_FILIAL_{codfilial}.pdf'
            


        with open(caminhoInsc, "wb") as f:
            f.write(base64.b64decode(pdf['data']))

        if os.path.exists(caminhoInsc):
            #escreveLog('CC',"Prenchendo dados da  consulta de conta corrente")
            #escreveLog('CC',FR"PDF Salvo como: {nomeArquivo}")
                
            print(f'Conta Corrente {inscricaoEstadual} salva com sucesso!')
            caminhoPadrao = fr'C:\Sefaz_RPA\Conta Corrente\mes_{mesAnterior:02d}_{anoAnterior}'

            # 3. Montagem do Arquivo (Usando os.path.join para evitar erro de barras)
            caminhoDestino = os.path.join(caminhoPadrao, nomeArquivo)

            print(f"Caminho Gerado: {caminhoDestino}")
            shutil.copy(caminhoInsc, caminhoDestino)
            print(fr"Arquivo foi copiado para a pasta: {caminhoPadrao}\{nomeArquivo}")                          
            #escreveLog('CC',FR"Arquivo copiado para {caminhoPadrao}")
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            print('aba fechada')

    return


if __name__ == "__main__":
    mainCC()