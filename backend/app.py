from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

from db import IntegrityErrors, buscar_um, executar

app = Flask(__name__)
CORS(app)


@app.route('/api/teste', methods=['GET'])
def teste():
    return jsonify({"mensagem": "Conexão bem-sucedida! O Front e o Back estão conversando."}), 200


@app.route('/api/cadastro', methods=['POST'])
def cadastro():
    dados = request.get_json() or {}
    nome = (dados.get('nome') or '').strip()
    email = (dados.get('email') or '').strip().lower()
    senha = dados.get('senha') or ''

    if not nome or not email or not senha:
        return jsonify({"erro": "Preencha nome, e-mail e senha."}), 400
    if len(senha) < 6:
        return jsonify({"erro": "A senha precisa ter pelo menos 6 caracteres."}), 400

    try:
        executar(
            "INSERT INTO usuarios (nome, email, senha_hash, tipo) VALUES (%s, %s, %s, 'cliente')",
            (nome, email, generate_password_hash(senha)),
        )
    except IntegrityErrors:
        return jsonify({"erro": "E-mail já cadastrado."}), 409

    return jsonify({"mensagem": "Cadastro realizado com sucesso."}), 201


@app.route('/api/login', methods=['POST'])
def login():
    dados = request.get_json() or {}
    email = (dados.get('email') or '').strip().lower()
    senha = dados.get('senha') or ''

    if not email or not senha:
        return jsonify({"erro": "Informe e-mail e senha."}), 400

    usuario = buscar_um(
        "SELECT id, nome, email, senha_hash, tipo FROM usuarios WHERE email = %s",
        (email,),
    )

    if not usuario or not check_password_hash(usuario['senha_hash'], senha):
        return jsonify({"erro": "E-mail ou senha inválidos."}), 401

    return jsonify({
        "id": usuario['id'],
        "nome": usuario['nome'],
        "tipo": usuario['tipo'],
    }), 200


if __name__ == '__main__':
    app.run(debug=True)