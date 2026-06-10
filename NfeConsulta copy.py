import os
import json
from time import sleep
from datetime import datetime
import shutil

# 1. IMPORTANTE: Importar o undetected-chromedriver e componentes do Selenium
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Módulos locais da sua aplicação
import anticaptcha
import resolvebase64
import database
import DatasMes
import ModificaCsv

hoje = datetime.now()
mesAtual = hoje.month
if mesAtual < 10:
    mesAtual = f'0{mesAtual}'

# Pega as informações que estão no json
# --------------json----------------
with open(r'json\contabilista.json', 'r') as file:
    dados = json.load(file)
userContabilista = dados["Contabilista"]
senhaContabilista = dados["SenhaContabilista"]

# Setando datas de consulta
# ---------------data-------------------
data_inicio, data_fim = DatasMes.gerar_intervalo_datas()

# Pegando uma lista com o grupo, filiais e cnpj do banco de dados
lista_filiais = database.retornoCnpj()

# -----------caminho download-------------------
caminho = rf'C:\Sefaz_RPA\downloads\xls'


def mainNfe():
    # 2. Configurar as opções usando o uc
    options = uc.ChromeOptions()
    
    # Dica: Evite usar --headless puro no uc. Se for estritamente necessário, use: options.add_argument('--headless=new')
    # options.add_argument('--headless') 
    options.add_argument('--no-sandbox')
    options.add_argument('--mute-audio')
    options.add_argument("--disable-popup-blocking")

    prefs = {
        "download.default_directory": caminho,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
        "plugins.always_open_pdf_externally": True
    }
    options.add_experimental_option("prefs", prefs)

    try:
        print("Abrindo o navegador (Undetected Chromedriver)")
        # Se precisar fixar a versão do Chrome devido a erros, use: version_main=148 como na referência
        driver = uc.Chrome(options=options)
        sleep(2)  # Tempo para o uc inicializar estavelmente

        url = "https://www.sefaz.mt.gov.br/acesso/pages/login/login.xhtml"
        driver.implicitly_wait(2)
        driver.get(url)
        driver.maximize_window()
        sleep(1)

        LoginEcaptcha(driver)
        loopNfe(driver, lista_filiais)
        
    except Exception as e:
        print(f"Erro na execução principal: {e}")
    finally:
        # O uc funciona muito melhor fechando explicitamente com .quit()
        try:
            driver.quit()
            print("Navegador finalizado com sucesso.")
        except:
            pass


# ----------Comecando login----------------
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
        
        # Tenta resolver o captcha 5x, caso não consiga, ele quebra o laço
        for x in range(5):
            print(f"Tentativa de login/captcha: {x+1}/5")
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

                # Resolvendo o captcha na sefaz
                captcha_element = driver.find_element(By.XPATH, '//img[contains(@src, "data:image/png;base64")]')
                src = captcha_element.get_attribute('src')
                
                # Converte o base64
                resolvebase64.decode64(src)
                sleep(1)
                
                # Resolve com anticaptcha
                captcha = anticaptcha.anticaptcha()
                print(f"Captcha resolvido: {captcha}")

                # Enviar captcha resolvido
                captchaResolvido = WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located((By.ID, 'formLogin:inputCaptcha'))
                )
                captchaResolvido.clear()
                captchaResolvido.send_keys(captcha)
                sleep(2)               

                # Localiza o botão de efetuar login
                efetuarLogin = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//button[contains(., 'Efetuar Login')]"))
                )

                # 3. Dispara o clique nativo através do Chrome DevTools Protocol (CDP)
                # Coleta as coordenadas de hardware reais do elemento na tela
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

                # Verifica se ocorreu algum erro na tela
                try:
                    erro = None
                    erro = WebDriverWait(driver, 5).until(
                        EC.visibility_of_element_located((By.CLASS_NAME, 'ui-messages-error'))
                    )
                except:
                    pass
                if erro:
                    print(f"Erro detectado no login: {erro.text}. Tentando novamente...")
                    continue

                # Verifica tela de sessão duplicada
                try:
                    outraSessaoAberta = None
                    outraSessaoAberta = WebDriverWait(driver, 5).until(
                        EC.visibility_of_element_located((By.XPATH, "//*[contains(@id, 'superPanelMensagem')]"))
                    )
                except:
                    pass
                if outraSessaoAberta:
                    print('Existe outra sessão aberta. Substituindo...')
                    senhaSessao = WebDriverWait(driver, 10).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, "input[type='password'].ui-password"))
                    )
                    senhaSessao.send_keys(senhaContabilista)

                    substituir = WebDriverWait(driver, 10).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, "input.btnPadrao[value='Substituir']"))
                    )
                    substituir.click()
                    break

                # Valida se entrou na tela inicial com sucesso
                try:
                    telaInicial = None 
                    telaInicial = WebDriverWait(driver, 5).until(
                        EC.visibility_of_element_located((By.ID, "tst"))
                    )
                except:
                    pass
                
                if telaInicial:
                    print("Tela inicial localizada.")
                    break
        
            except Exception as inner_e:
                print(f"Erro na tentativa interna do laço: {inner_e}")
                pass
                
        print('Passou do login com êxito!')
    except Exception as e:
        print('Erro crítico ao tentar logar')
        print(e)


def loopNfe(driver, lista_filiais):
    try:
        for filiais in lista_filiais:
            grupo = filiais[0]
            filial = filiais[1]
            cnpj = filiais[2]

            while True:
                # Abre uma nova aba com o link da consulta de nfe
                driver.execute_script("window.open('');")
                sleep(1)

                WebDriverWait(driver, 10).until(lambda d: len(d.window_handles) > 1)
                driver.switch_to.window(driver.window_handles[1])
                driver.get('https://www.sefaz.mt.gov.br/nfe/pages/consultaemitidasrecebidas/consultaemitidasrecebidas.xhtml')
                sleep(1)

                # Preenchimento dos dados da consulta
                dadosConsulta(driver, cnpj)

                # Tratamento de Mensagens de Erro da Sefaz
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
                    print(fr'Ocorreu um erro no CNPJ: {cnpj} na hora de colocar o CNPJ no site. Tentando novamente...')
                    sleep(2)
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                    sleep(2)
                    continue  

                mensagemErroData = None
                try:
                    mensagemErroData = WebDriverWait(driver, 5).until(
                        EC.visibility_of_element_located((By.XPATH, "//div[contains(text(),'Data inválida')]"))
                    )
                except:
                    pass

                if mensagemErroData:
                    print(fr'Ocorreu um erro no CNPJ: {cnpj} na hora de colocar as datas no site. Tentando novamente...')
                    sleep(2)
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                    sleep(2)
                    continue 
                
                # Validação do Botão de Exportação
                exportarExcel = None
                try:
                    exportarExcel = WebDriverWait(driver, 10).until(
                        EC.visibility_of_element_located((By.XPATH, "//a[text()='Exportar para Excel']"))
                    )
                except:
                    pass
                    
                if exportarExcel:
                    exportarExcel.click()
                    caminhoPadrao = fr'C:\Sefaz_RPA\Consulta de NF-e EmitidaRecebida\mes_{mesAtual}'
                    print('Clicado para exportar')
                    sleep(15)
                    
                    try:
                        nomeArquivoAtual = ModificaCsv.coverterExcelpCsv('Nfe', grupo, filial)
                        print(fr"Criado o arquivo {nomeArquivoAtual}")
                        
                        if os.path.isfile(fr'downloads\csv\mes_{mesAtual}\{nomeArquivoAtual}'):
                            tamanhoCsv = os.path.getsize(fr'downloads\csv\mes_{mesAtual}\{nomeArquivoAtual}')

                            if tamanhoCsv > 20.48:
                                print(f'O arquivo é maior que 1024 bytes.')
                                shutil.copy(fr'downloads\csv\mes_{mesAtual}\{nomeArquivoAtual}', fr'{caminhoPadrao}\{nomeArquivoAtual}')
                                print(fr"Arquivo foi copiado para a pasta: {caminhoPadrao}\{nomeArquivoAtual}")                         
                                
                                driver.close()
                                driver.switch_to.window(driver.window_handles[0])
                                print('Janela de consulta fechada.')
                                break
                            else:
                                print(f'O arquivo não é maior que 1024 bytes (pode estar corrompido).')
                                driver.close()
                                driver.switch_to.window(driver.window_handles[0])
                                break
                        else:
                            print(f'O arquivo não existe no diretório.')
                            driver.close()
                            driver.switch_to.window(driver.window_handles[0])
                            break

                    except Exception as e:
                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])
                        print(f"Erro ao processar o arquivo baixado: {e}")
                        break
                else:
                    print("Botão de exportar Excel não apareceu.")
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                    break

    except Exception as e:
        print(f"Erro no loop de CNPJs: {e}")
        try:
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
        except:
            pass


# ------------------dados da consulta-------------------
def dadosConsulta(driver, cnpj):

    botaoDest = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.XPATH, '//*[@id="j_idt14:sorEmissorDest"]/tbody/tr/td[2]/div/div[2]/span'))
    )
    botaoDest.click()

    botaoInsc = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.XPATH, "//label[text()='Inscrição Estadual']"))
    )
    botaoInsc.click()

    insc = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.XPATH, "//li[text()='CNPJ']"))
    )
    insc.click()
    print('Escolhendo o tipo de documento: CNPJ')
    sleep(2)
    
    inputCnpj = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.XPATH, "//div[@class='ui-panel-content ui-widget-content']//input[contains(@class, 'ui-inputmask')]"))
    )

    sleep(5)
    inputCnpj.click()
    inputCnpj.send_keys(cnpj)
    print('Escrevendo o cnpj atual')

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

    consultar = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.XPATH, "//button[.//span[text()='Consultar']]"))
    )
    sleep(2)
    consultar.click()


if __name__ == "__main__":
    mainNfe()