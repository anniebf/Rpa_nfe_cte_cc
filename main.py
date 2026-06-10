#ARQUIVO PARA RODAR O CODIGO 
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
import modificaCsv
import os
import NfeConsulta

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
caminho = fr'downloads\xls'

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
    NfeConsulta.LoginEcaptcha(driver)
    NfeConsulta.loopNfe(driver,lista_filiais)
