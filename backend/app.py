from flask import Flask, jsonify
from flask_cors import CORS 

app = Flask(__name__)
CORS(app) 


@app.route('/api/teste', methods=['GET'])
def teste():
    return jsonify({"mensagem": "Conexão bem-sucedida! O Front e o Back estão conversando."}), 200

if __name__ == '__main__':
    app.run(debug=True)