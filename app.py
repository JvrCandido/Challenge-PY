import re
import json
import cx_Oracle
import requests
from flask import Flask, render_template, request, redirect, url_for

DB_USER = 'RM557129'
DB_PASSWORD = '100306'
DB_HOST = 'oracle.fiap.com.br'
DB_PORT = '1521'
DB_SERVICE = 'ORCL'

dsn = cx_Oracle.makedsn(DB_HOST, DB_PORT, service_name=DB_SERVICE)

app = Flask(__name__)

def conectar_bd():
    try:
        connection = cx_Oracle.connect(user=DB_USER, password=DB_PASSWORD, dsn=dsn)
        print("Conexão estabelecida com sucesso!")
        return connection
    except cx_Oracle.DatabaseError as e:
        error, = e.args
        print(f"Ocorreu um erro ao conectar ao banco de dados: {error.message}")
        return None

def validar_email(email):
    padrao = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(padrao, email)

def validar_senha(senha):
    padrao = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'
    return re.match(padrao, senha)

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/cadastrar_cliente', methods=['GET', 'POST'])
def cadastrar_cliente():
    if request.method == 'POST':
        nome = request.form['nome']
        idoso = 'sim' == request.form.get('idoso')
        pcd = 'sim' == request.form.get('pcd')
        
        email = request.form['email']
        senha = request.form['senha']
        
        if not validar_email(email):
            print("Email inválido.")
            return "Email inválido.", 400
        if not validar_senha(senha):
            print("Senha inválida.")
            return "Senha inválida. A senha deve ter 8 caracteres, com letras maiúsculas, minúsculas, números e caracteres especiais.", 400
        
        connection = conectar_bd()
        if connection:
            try:
                cursor = connection.cursor()
                cursor.execute("""INSERT INTO t_as_cliente (id_nome, id_email, cd_senha, pcd, idoso) VALUES (:1, :2, :3, :4, :5)""",
                               (nome, email, senha, pcd, idoso))
                connection.commit()
                print("Cliente cadastrado com sucesso.")
            except cx_Oracle.DatabaseError as e:
                error, = e.args
                print(f"Erro ao cadastrar cliente: {error.message}")
            finally:
                cursor.close()
                connection.close()
        else:
            print("Erro ao conectar ao banco de dados.")
        
        return redirect(url_for('index'))
    return render_template("cadastrar_cliente.html")

@app.route('/consultar_cliente', methods=['GET'])
def consultar_cliente():
    email = request.args.get('email')
    connection = conectar_bd()
    if connection:
        cursor = connection.cursor()
        cursor.execute("""SELECT id_nome, id_email, pcd, idoso FROM t_as_cliente WHERE id_email = :1""", (email,))
        cliente = cursor.fetchone()
        cursor.close()
        connection.close()
        
        if cliente:
            exportar_cliente_para_json(cliente)
            return json.dumps({
                "nome": cliente[0],
                "email": cliente[1],
                "pcd": cliente[2],
                "idoso": cliente[3]
            })
        return "Cliente não encontrado.", 404
    return "Erro de conexão com o banco de dados.", 500

def exportar_cliente_para_json(cliente):
    with open(f"{cliente[1]}.json", 'w') as json_file:
        json.dump({
            "nome": cliente[0],
            "email": cliente[1],
            "pcd": cliente[2],
            "idoso": cliente[3]
        }, json_file)

@app.route('/consulta_cep', methods=['GET'])
def consulta_cep():
    cep = request.args.get('cep')
    response = requests.get(f'https://viacep.com.br/ws/{cep}/json/')
    if response.status_code == 200:
        dados_endereco = response.json()
        if "erro" not in dados_endereco:
            return json.dumps(dados_endereco)
        else:
            return "CEP não encontrado.", 404
    return "Erro ao consultar o CEP.", 500

if __name__ == '__main__':
    app.run(debug=True)
