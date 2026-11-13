// Dashboard (RF05): dados do funcionário logado, vindos de GET /api/dashboard.
(() => {
    const usuario = Painel.exigirAcesso();
    if (!usuario) return;

    const { escapar, formatarMoeda, formatarNumero } = Painel;

    const SITUACOES = {
        realizado: 'Realizado',
        em_andamento: 'Em andamento',
        a_seguir: 'A seguir',
    };

    const UNIDADES = { un: 'unidade(s)', ml: 'ml', g: 'g', l: 'litro(s)' };

    function texto(id, valor) {
        document.getElementById(id).textContent = valor;
    }

    function preencherCards(dados) {
        const { agendamentos_hoje: ag, receita } = dados;
        texto('val-agendamentos', ag.total);
        texto('sub-agendamentos', dados.profissional
            ? `${ag.realizados} realizado(s) · ${ag.a_seguir} a seguir`
            : 'Você não tem agenda de atendimentos');

        texto('val-receita-dia', formatarMoeda(receita.dia));
        texto('sub-receita-dia', `Prevista para hoje: ${formatarMoeda(receita.dia_prevista)}`);

        const mes = Painel.dataPorExtenso(dados.data, { month: 'long', year: 'numeric' });
        texto('val-receita-mes', formatarMoeda(receita.mes));
        texto('sub-receita-mes', `${receita.mes_atendimentos} atendimento(s) em ${mes}`);
    }

    function preencherEstoque(estoque) {
        const lista = document.getElementById('lista-estoque');
        if (!estoque.total) {
            Painel.estado(lista, 'Nenhum produto com estoque baixo.');
            return;
        }

        const itens = estoque.produtos.map((p) => {
            const unidade = UNIDADES[p.unidade] || p.unidade;
            return `
                <div class="alert-item">
                    <div class="alert-info">
                        <h4>${escapar(p.nome)}</h4>
                        <p>Mínimo definido: ${formatarNumero(p.quantidade_minima)} ${unidade}</p>
                    </div>
                    <div class="alert-badge">${formatarNumero(p.quantidade)} ${unidade} restante(s)</div>
                </div>`;
        });

        // O endpoint traz no máximo 3; o gerente pode abrir o Estoque para ver o resto
        const restantes = estoque.total - estoque.produtos.length;
        if (restantes > 0) {
            const aviso = usuario.perfil === 'gerente'
                ? `<a class="alert-more" href="estoque.html">+ ${restantes} produto(s) em estoque baixo</a>`
                : `<p class="alert-more">+ ${restantes} produto(s) em estoque baixo</p>`;
            itens.push(aviso);
        }
        lista.innerHTML = itens.join('');
    }

    function preencherAgenda(dados) {
        const lista = document.getElementById('lista-agenda');
        if (!dados.agenda_hoje.length) {
            Painel.estado(lista, dados.profissional
                ? 'Nenhum atendimento agendado para hoje.'
                : 'Seu usuário não está cadastrado como profissional, então não há agenda pessoal.');
            return;
        }

        lista.innerHTML = dados.agenda_hoje.map((item) => `
            <div class="alert-item today-item">
                <div class="today-time">${item.hora_inicio} – ${item.hora_fim}</div>
                <div class="alert-info">
                    <h4>${escapar(item.servico.nome)}</h4>
                    <p>Cliente: ${escapar(item.cliente.nome)}</p>
                </div>
                <span class="situacao situacao-${item.situacao}">${SITUACOES[item.situacao] || item.situacao}</span>
            </div>`).join('');
    }

    async function carregar() {
        const resposta = await Painel.chamar('GET', '/dashboard');
        if (!resposta.ok) {
            const msg = Painel.mensagemDeErro(resposta, 'Não foi possível carregar o dashboard.');
            Painel.estado(document.getElementById('lista-estoque'), msg, 'erro');
            Painel.estado(document.getElementById('lista-agenda'), msg, 'erro');
            return;
        }

        const dados = resposta.dados;
        const nome = dados.profissional ? dados.profissional.nome : usuario.nome;
        texto('current-date', `${Painel.dataPorExtenso(dados.data)} · Olá, ${Painel.primeiroNome(nome)}`);
        preencherCards(dados);
        preencherEstoque(dados.estoque_baixo);
        preencherAgenda(dados);
    }

    texto('current-date', Painel.dataPorExtenso(new Date()));
    carregar();
})();
