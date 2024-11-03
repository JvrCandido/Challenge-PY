import re
import json
import cx_Oracle
import requests
from flask import Flask, render_template, request, redirect, url_for, flash

DB_USER = 'RM557129'
DB_PASSWORD = '100306'
DB_HOST = 'oracle.fiap.com.br'
DB_PORT = '1521'
DB_SERVICE = 'ORCL'

dsn = cx_Oracle.makedsn(DB_HOST, DB_PORT, service_name=DB_SERVICE)

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta'  

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
        cep = request.form['cep']  
        
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
                cursor.execute("""INSERT INTO T_AS_CLIENTE (id_nome, id_email, cd_senha, cd_cep, pcd, idoso) VALUES (:1, :2, :3, :4, :5, :6)""",
                               (nome, email, senha, cep, pcd, idoso))
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
    print(f"Consultando cliente com email: {email}")  
    
    connection = conectar_bd()
    if not connection:
        print("Erro ao conectar ao banco de dados.")
        flash("Erro ao conectar ao banco de dados.", "error")
        return render_template('consultar_cliente.html', cliente=None)

    cliente = None
    
    try:
        cursor = connection.cursor()
        cursor.execute("""SELECT id_nome, id_email, cd_cep, pcd, idoso FROM T_AS_CLIENTE WHERE id_email = :1""", (email,))
        cliente = cursor.fetchone()
        print(f"Cliente encontrado: {cliente}")  
    except cx_Oracle.DatabaseError as e:
        error, = e.args
        print(f"Erro ao consultar cliente: {error.message}")  
        flash(f"Erro ao consultar cliente: {error.message}", "error")
    finally:
        cursor.close()
        connection.close()

    
    if cliente:
        return render_template('consultar_cliente.html', cliente=cliente)
    else:
        flash("Nenhum cliente encontrado.", "warning") 
        return render_template('consultar_cliente.html', cliente=None)  



@app.route('/alterar_cliente/<email>', methods=['GET', 'POST'])
def alterar_cliente(email):
    connection = conectar_bd()
    if not connection:
        return "Erro de conexão com o banco de dados.", 500

    if request.method == 'POST':
        nome = request.form['nome']
        cep = request.form['cep']
        pcd = 'sim' == request.form.get('pcd')
        idoso = 'sim' == request.form.get('idoso')

        try:
            cursor = connection.cursor()
            cursor.execute("""UPDATE T_AS_CLIENTE
                              SET id_nome = :1, cd_cep = :2, pcd = :3, idoso = :4
                              WHERE id_email = :5""",
                           (nome, cep, pcd, idoso, email))
            connection.commit()
            flash("Cliente atualizado com sucesso!", "success")
            return redirect(url_for('consultar_cliente', email=email))
        except cx_Oracle.DatabaseError as e:
            error, = e.args
            flash(f"Erro ao atualizar cliente: {error.message}", "error")
        finally:
            cursor.close()
            connection.close()
    else:
        cursor = connection.cursor()
        cursor.execute("""SELECT id_nome, id_email, cd_cep, pcd, idoso
                          FROM T_AS_CLIENTE
                          WHERE id_email = :1""", (email,))
        cliente = cursor.fetchone()
        cursor.close()
        connection.close()
        
        if cliente:
            return render_template('alterar_cliente.html', cliente=cliente)
        else:
            flash("Cliente não encontrado.", "error")
            return redirect(url_for('index'))

@app.route('/deletar_cliente', methods=['POST'])
def deletar_cliente():
    email = request.form['email']
    connection = conectar_bd()
    if not connection:
        return "Erro de conexão com o banco de dados.", 500

    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM T_AS_CLIENTE WHERE id_email = :1", (email,))
        connection.commit()
        flash("Cliente deletado com sucesso!", "success")
    except cx_Oracle.DatabaseError as e:
        error, = e.args
        flash(f"Erro ao deletar cliente: {error.message}", "error")
    finally:
        cursor.close()
        connection.close()

    return redirect(url_for('index'))

@app.route('/consulta_cep', methods=['GET'])
def consulta_cep():
    cep = request.args.get('cep')
    dados_endereco = None

    if cep:
        response = requests.get(f"https://viacep.com.br/ws/{cep}/json/")
        
        if response.status_code == 200:
            dados_endereco = response.json()
        else:
            flash("Erro ao consultar o CEP. Verifique se o CEP está correto.", "error")

    return render_template('consulta_cep.html', dados_endereco=dados_endereco)

if __name__ == '__main__':
    app.run(debug=True)
