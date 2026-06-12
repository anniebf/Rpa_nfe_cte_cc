import oracledb
import pandas
import os
from dotenv import load_dotenv  

load_dotenv()

usernameBd = os.getenv('usernameBd')
passwordBd = os.getenv('passwordBd')
dsn = os.getenv('dsn')

connectionBd = oracledb.connect(user=usernameBd, password=passwordBd, dsn=dsn)
cursor = connectionBd.cursor()

def retornoCnpj():
    cursor.execute("""
            SELECT M0_CODIGO, M0_FILIAL, M0_CGC, M0_CODFIL from PROTHEUS11.sigaemp 
            WHERE LENGTH(trim(M0_CGC)) >= 12 
            --AND m0_insc not in ('ISENTO',' ')OR m0_insc = NULL
            """)
    # Usar fetchall() para pegar todas as linhas
    Resutadocnpj = cursor.fetchall()
    #print(type(Resutadocnpj))
    #for filial in Resutadocnpj:
    #    print(filial)
    
    #df = pandas.DataFrame(Resutadocnpj)
    #df.to_csv(fr'sequencianotas\cnpjFiliais\resultado.csv', index=False, header=False)
    
    return Resutadocnpj

def retornoInscEstd():
    cursor.execute("""
            SELECT m0_insc, M0_FILIAL, M0_CODFIL, M0_CODIGO from PROTHEUS11.sigaemp 
            WHERE LENGTH(trim(M0_CGC)) >= 12 AND 
            m0_insc not in ('ISENTO',' ') OR m0_insc = null 
            """)
    ResutadoInscEstd= cursor.fetchall()
    return ResutadoInscEstd

if __name__ == "__main__":
    retornoCnpj()
    retornoInscEstd()