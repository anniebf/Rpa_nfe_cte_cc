import sys
import base64


def decode64(base64_string):
    # Decodificar a string base64       
    #print(base64_string)
    base64_string = base64_string[22:]
    #print(base64_string)
    decoded_data = base64.b64decode(base64_string)
    # Caminho do arquivo de saída
    output_file_path = fr'img\captcha.jpg'
    # Escrever os dados decodificados no arquivo
    with open(output_file_path, 'wb') as output_file:
        output_file.write(decoded_data)    
    #print("Arquivo salvo com sucesso em:", output_file_path)
    return 

if __name__ == "__main__":
    # Capturar o argumento passado
    #base64_string = sys.argv[1]
    decode64("")