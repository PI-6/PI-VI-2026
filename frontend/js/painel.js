// Base comum das telas internas (admin e gerente): sessão, menu por perfil e utilitários.
// Carregar depois do api.js e antes do script da tela.
//
// A checagem de perfil aqui só decide o que mostrar. Quem garante o acesso é o backend,
// que confere o token e o perfil em toda requisição.
const Painel = (() => {
    const PERFIS_EQUIPE = ['admin', 'gerente'];
    const PAGINAS_SO_GERENTE = ['servicos.html', 'profissionais.html', 'estoque.html', 'financeiro.html'];

    function paginaAtual() {
        return window.location.pathname.split('/').pop() || 'dashboard.html';
    }

    // ---------- Sessão e menu ----------

    // Confere se há alguém da equipe logado. Sem login vai para o login (e volta depois);
    // cliente vai para a área dele; admin numa tela só do gerente volta ao Dashboard.
    function exigirAcesso() {
        const usuario = usuarioLogado();
        if (!usuario) {
            window.location.replace(`login.html?next=${paginaAtual()}`);
            return null;
        }
        if (!PERFIS_EQUIPE.includes(usuario.perfil)) {
            window.location.replace('salao.html');
            return null;
        }
        if (usuario.perfil !== 'gerente' && PAGINAS_SO_GERENTE.includes(paginaAtual())) {
            window.location.replace('dashboard.html');
            return null;
        }
        montarMenu(usuario);
        return usuario;
    }

    function montarMenu(usuario) {
        const ehGerente = usuario.perfil === 'gerente';

        // O admin só vê Dashboard e Agenda (RF05 e RF06)
        document.querySelectorAll('.sidebar-nav a').forEach((link) => {
            const destino = link.getAttribute('href');
            if (!ehGerente && PAGINAS_SO_GERENTE.includes(destino)) {
                link.closest('li').remove();
            }
        });

        const avatar = document.querySelector('.user-avatar');
        const nome = document.querySelector('.user-info p');
        if (avatar) avatar.textContent = (usuario.nome || '?').trim().charAt(0).toUpperCase();
        if (nome) nome.textContent = `${primeiroNome(usuario.nome)} · ${ehGerente ? 'Gerente' : 'Admin'}`;

        const sair = document.querySelector('.btn-logout');
        if (sair) {
            sair.addEventListener('click', (e) => {
                e.preventDefault();
                encerrarSessao();
                window.location.href = 'login.html';
            });
        }

        if (ehGerente) atualizarBadgeEstoque();
        montarMenuCelular();
        rotularTabelas();
    }

    // No celular as tabelas viram cards e cada valor precisa do nome da coluna ao lado (#78).
    // As linhas são recriadas pelo script de cada tela, então um observador repõe os rótulos.
    function rotularTabelas() {
        document.querySelectorAll('.table-container table').forEach((tabela) => {
            const titulos = [...tabela.querySelectorAll('thead th')].map((th) => th.textContent.trim());
            const tbody = tabela.querySelector('tbody');
            if (!tbody || !titulos.length) return;

            const rotular = () => {
                tbody.querySelectorAll('tr').forEach((tr) => {
                    [...tr.children].forEach((td, i) => {
                        if (!td.hasAttribute('colspan') && titulos[i]) td.dataset.label = titulos[i];
                    });
                });
            };
            rotular();
            new MutationObserver(rotular).observe(tbody, { childList: true });
        });
    }

    // No celular a barra lateral fica escondida e abre pelo botão ☰ (#78).
    // O botão e o fundo escuro existem sempre, mas o CSS só os mostra abaixo de 768px.
    function montarMenuCelular() {
        const sidebar = document.querySelector('.sidebar');
        if (!sidebar || document.querySelector('.pn-menu-toggle')) return;

        const botao = document.createElement('button');
        botao.type = 'button';
        botao.className = 'pn-menu-toggle';
        botao.setAttribute('aria-label', 'Abrir menu');
        botao.setAttribute('aria-expanded', 'false');
        botao.textContent = '☰';

        const fundo = document.createElement('div');
        fundo.className = 'pn-menu-fundo';

        function alternar(abrir) {
            document.body.classList.toggle('pn-menu-aberto', abrir);
            botao.setAttribute('aria-expanded', String(abrir));
            botao.setAttribute('aria-label', abrir ? 'Fechar menu' : 'Abrir menu');
            botao.textContent = abrir ? '✕' : '☰';
        }

        botao.addEventListener('click', () => alternar(!document.body.classList.contains('pn-menu-aberto')));
        fundo.addEventListener('click', () => alternar(false));
        sidebar.querySelectorAll('.sidebar-nav a').forEach((link) => {
            link.addEventListener('click', () => alternar(false));
        });
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') alternar(false);
        });

        document.body.append(botao, fundo);
    }

    // Número no item "Estoque" do menu: quantos produtos estão em estoque baixo
    async function atualizarBadgeEstoque() {
        const badge = document.querySelector('a[href="estoque.html"] .nav-badge');
        if (!badge) return;
        const { ok, dados } = await chamar('GET', '/produtos?estoque_baixo=1');
        const total = ok ? dados.length : 0;
        badge.textContent = total;
        badge.hidden = total === 0;
    }

    // ---------- API ----------

    // apiRequest com tratamento de falha de rede: sempre devolve { ok, status, dados }
    async function chamar(metodo, rota, corpo) {
        try {
            return await apiRequest(metodo, rota, corpo);
        } catch (erro) {
            console.error('Falha ao chamar a API:', erro);
            return { ok: false, status: 0, dados: { erro: 'Não foi possível conectar ao servidor.' } };
        }
    }

    // Texto para mostrar ao usuário a partir de uma resposta de erro da API
    function mensagemDeErro(resposta, padrao = 'Não foi possível concluir a operação.') {
        const dados = resposta && resposta.dados;
        if (!dados) return padrao;
        const detalhes = dados.detalhes || {};
        const primeiro = Object.values(detalhes).find((v) => typeof v === 'string');
        return primeiro ? `${dados.erro} ${primeiro}` : (dados.erro || padrao);
    }

    // ---------- Formatação ----------

    const moeda = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' });
    const numero = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 3 });

    function formatarMoeda(valor) {
        return moeda.format(Number(valor) || 0);
    }

    function formatarNumero(valor) {
        return numero.format(Number(valor) || 0);
    }

    function formatarPercentual(valor) {
        if (valor === null || valor === undefined) return '—';
        const sinal = valor > 0 ? '+' : '';
        return `${sinal}${numero.format(valor)}%`;
    }

    // Data local em AAAA-MM-DD (toISOString usaria UTC e trocaria o dia à noite)
    function dataISO(data = new Date()) {
        const mes = String(data.getMonth() + 1).padStart(2, '0');
        const dia = String(data.getDate()).padStart(2, '0');
        return `${data.getFullYear()}-${mes}-${dia}`;
    }

    // "2026-11-13" -> Date local, sem o deslocamento de fuso do new Date("2026-11-13")
    function lerDataISO(texto) {
        const [ano, mes, dia] = texto.split('-').map(Number);
        return new Date(ano, mes - 1, dia);
    }

    function dataPorExtenso(data, opcoes = { weekday: 'long', day: '2-digit', month: 'long', year: 'numeric' }) {
        const valor = typeof data === 'string' ? lerDataISO(data) : data;
        return valor.toLocaleDateString('pt-BR', opcoes);
    }

    function primeiroNome(nome) {
        return (nome || '').trim().split(/\s+/)[0];
    }

    // Todo texto vindo da API passa por aqui antes de entrar em innerHTML
    function escapar(texto) {
        return String(texto ?? '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    // ---------- Componentes de tela ----------

    // Modal de confirmação reutilizável (toda exclusão passa por ele). Devolve Promise<boolean>.
    function confirmar(mensagem, { titulo = 'Confirmar', textoBotao = 'Confirmar', perigo = true } = {}) {
        return new Promise((resolve) => {
            const fundo = document.createElement('div');
            fundo.className = 'pn-overlay';
            fundo.innerHTML = `
                <div class="pn-dialog" role="dialog" aria-modal="true">
                    <h3>${escapar(titulo)}</h3>
                    <p>${escapar(mensagem)}</p>
                    <div class="pn-dialog-acoes">
                        <button type="button" class="pn-btn" data-resposta="nao">Voltar</button>
                        <button type="button" class="pn-btn ${perigo ? 'pn-btn-perigo' : 'pn-btn-ouro'}" data-resposta="sim">
                            ${escapar(textoBotao)}
                        </button>
                    </div>
                </div>`;

            function fechar(resposta) {
                document.removeEventListener('keydown', aoTeclar);
                fundo.remove();
                resolve(resposta);
            }
            function aoTeclar(e) {
                if (e.key === 'Escape') fechar(false);
            }

            fundo.addEventListener('click', (e) => {
                if (e.target === fundo) fechar(false);
                const botao = e.target.closest('[data-resposta]');
                if (botao) fechar(botao.dataset.resposta === 'sim');
            });
            document.addEventListener('keydown', aoTeclar);
            document.body.appendChild(fundo);
            fundo.querySelector('[data-resposta="sim"]').focus();
        });
    }

    // Aviso rápido no canto da tela
    function avisar(texto, tipo = 'sucesso') {
        let area = document.querySelector('.pn-toasts');
        if (!area) {
            area = document.createElement('div');
            area.className = 'pn-toasts';
            document.body.appendChild(area);
        }
        const toast = document.createElement('div');
        toast.className = `pn-toast pn-toast-${tipo}`;
        toast.textContent = texto;
        area.appendChild(toast);
        setTimeout(() => toast.remove(), tipo === 'erro' ? 6000 : 3500);
    }

    // Caixa de "carregando", "vazio" ou "erro" dentro de um contêiner
    function estado(container, texto, tipo = 'vazio') {
        container.innerHTML = `<div class="pn-estado pn-estado-${tipo}">${escapar(texto)}</div>`;
    }

    // Mostra a mensagem de erro do formulário e marca os campos que a API apontou.
    // mapaCampos liga o nome do campo na API ao id do input na tela.
    function mostrarErrosFormulario(form, resposta, mapaCampos = {}) {
        limparErrosFormulario(form);
        const detalhes = (resposta.dados && resposta.dados.detalhes) || {};
        Object.keys(detalhes).forEach((campo) => {
            const id = mapaCampos[campo];
            const input = id && document.getElementById(id);
            if (input) input.classList.add('pn-campo-erro');
        });
        let msg = form.querySelector('.pn-form-msg');
        if (!msg) {
            msg = document.createElement('p');
            msg.className = 'pn-form-msg';
            form.querySelector('.modal-footer').before(msg);
        }
        msg.textContent = mensagemDeErro(resposta);
    }

    function limparErrosFormulario(form) {
        form.querySelectorAll('.pn-campo-erro').forEach((el) => el.classList.remove('pn-campo-erro'));
        const msg = form.querySelector('.pn-form-msg');
        if (msg) msg.remove();
    }

    // Converte "1.234,50" ou "1234.5" em número (o backend também aceita, mas assim validamos antes)
    function lerNumero(texto) {
        const limpo = String(texto ?? '').trim().replace(/\s/g, '').replace('R$', '');
        if (!limpo) return NaN;
        const normalizado = limpo.includes(',') ? limpo.replace(/\./g, '').replace(',', '.') : limpo;
        return Number(normalizado);
    }

    return {
        exigirAcesso,
        atualizarBadgeEstoque,
        chamar,
        mensagemDeErro,
        formatarMoeda,
        formatarNumero,
        formatarPercentual,
        dataISO,
        lerDataISO,
        dataPorExtenso,
        primeiroNome,
        escapar,
        confirmar,
        avisar,
        estado,
        mostrarErrosFormulario,
        limparErrosFormulario,
        lerNumero,
    };
})();
