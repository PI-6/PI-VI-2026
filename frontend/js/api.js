const BASE_URL = 'http://127.0.0.1:5000';

async function testarConexao() {
    try {
        const resposta = await fetch(`${BASE_URL}/api/teste`);
        
        const dados = await resposta.json();
        
        return dados; 
    } catch (erro) {
        console.error("Erro ao conectar com a API:", erro);
        return { mensagem: "Falha na conexão" };
    }
}