// Cliente HTTP central: toda chamada ao backend passa por aqui.
const BASE_URL = 'http://127.0.0.1:5000';

const CHAVE_TOKEN = 'token';
const CHAVE_USUARIO = 'usuario';

function salvarSessao(token, usuario) {
    localStorage.setItem(CHAVE_TOKEN, token);
    localStorage.setItem(CHAVE_USUARIO, JSON.stringify(usuario));
}

function encerrarSessao() {
    localStorage.removeItem(CHAVE_TOKEN);
    localStorage.removeItem(CHAVE_USUARIO);
}

function usuarioLogado() {
    const salvo = localStorage.getItem(CHAVE_USUARIO);
    return salvo ? JSON.parse(salvo) : null;
}

// Faz a requisição e devolve { ok, status, dados }.
// Se houver token salvo, ele vai no header Authorization automaticamente.
async function apiRequest(metodo, rota, corpo) {
    const headers = { 'Content-Type': 'application/json' };
    const token = localStorage.getItem(CHAVE_TOKEN);
    if (token) {
        headers.Authorization = `Bearer ${token}`;
    }

    const resp = await fetch(`${BASE_URL}/api${rota}`, {
        method: metodo,
        headers,
        body: corpo ? JSON.stringify(corpo) : undefined,
    });

    // 401 em rota protegida = token vencido ou inválido: limpa e manda pro login
    if (resp.status === 401 && token && rota !== '/login') {
        encerrarSessao();
        window.location.href = 'login.html';
    }

    // DELETE devolve 204 sem corpo
    const dados = resp.status === 204 ? null : await resp.json();
    return { ok: resp.ok, status: resp.status, dados };
}

async function testarConexao() {
    try {
        const { dados } = await apiRequest('GET', '/teste');
        return dados;
    } catch (erro) {
        console.error("Erro ao conectar com a API:", erro);
        return { mensagem: "Falha na conexão" };
    }
}
