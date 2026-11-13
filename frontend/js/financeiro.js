// Financeiro / BI (RF10). Só o gerente.
// Atendimento realizado = agendamento não cancelado cujo horário já terminou (regra do backend).
// Gráficos com Chart.js (CDN carregado no financeiro.html, escolha do layout do Airton).
(() => {
    const usuario = Painel.exigirAcesso();
    if (!usuario) return;

    const { escapar, formatarMoeda, formatarPercentual, dataISO, lerDataISO } = Painel;

    const OURO = '#D4AF37';
    const CORES_PIZZA = ['#D4AF37', '#8b5cf6', '#3b82f6', '#F3E5AB', '#10b981', '#f472b6', '#f97316', '#475569'];
    const NOMES_PERIODO = { semana: 'Semana', mes: 'Mês', ano: 'Ano' };

    const estado = { periodo: 'mes', data: new Date() };
    const graficos = {};
    const el = (id) => document.getElementById(id);
    const temChart = typeof window.Chart !== 'undefined';

    if (temChart) {
        Chart.defaults.color = '#9BA4B5';
        Chart.defaults.font.family = "'Poppins', sans-serif";
    }

    // ---------- Gráficos ----------

    // Sem o Chart.js (ex.: sem internet para o CDN) a tela continua funcionando, só sem os gráficos
    function semGrafico(caixaId, texto) {
        const caixa = el(caixaId);
        caixa.querySelector('canvas').hidden = true;
        let aviso = caixa.querySelector('.pn-estado');
        if (!aviso) {
            aviso = document.createElement('div');
            aviso.className = 'pn-estado';
            caixa.appendChild(aviso);
        }
        aviso.textContent = texto;
    }

    function comGrafico(caixaId) {
        const caixa = el(caixaId);
        caixa.querySelector('canvas').hidden = false;
        const aviso = caixa.querySelector('.pn-estado');
        if (aviso) aviso.remove();
    }

    const tooltipMoeda = {
        backgroundColor: 'rgba(0,0,0,0.85)', titleColor: '#F8F8F8', bodyColor: OURO,
        padding: 12, cornerRadius: 8, displayColors: false,
        callbacks: { label: (ctx) => formatarMoeda(ctx.parsed.y) },
    };

    function desenharBarras(id, caixaId, rotulos, valores) {
        if (!temChart) {
            semGrafico(caixaId, 'Gráfico indisponível: a biblioteca de gráficos não carregou (verifique a internet).');
            return;
        }
        comGrafico(caixaId);
        if (graficos[id]) graficos[id].destroy();
        graficos[id] = new Chart(el(id), {
            type: 'bar',
            data: {
                labels: rotulos,
                datasets: [{ label: 'Receita', data: valores, backgroundColor: OURO, borderRadius: 4, barPercentage: 0.6 }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false }, tooltip: tooltipMoeda },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { callback: (v) => formatarMoeda(v).replace(/,00$/, '') },
                        grid: { color: 'rgba(255,255,255,0.05)' },
                    },
                    x: { grid: { display: false } },
                },
            },
        });
    }

    function desenharPizza(servicos) {
        if (!servicos.length) {
            if (graficos.donut) { graficos.donut.destroy(); delete graficos.donut; }
            semGrafico('caixaRosca', 'Nenhum atendimento realizado no período.');
            return;
        }
        if (!temChart) {
            semGrafico('caixaRosca', 'Gráfico indisponível: a biblioteca de gráficos não carregou (verifique a internet).');
            return;
        }
        comGrafico('caixaRosca');
        if (graficos.donut) graficos.donut.destroy();

        // Mais de 7 serviços: os menores viram "Outros" para a pizza continuar legível
        const principais = servicos.slice(0, 7);
        const resto = servicos.slice(7);
        const fatias = principais.map((s) => ({ nome: s.nome, qtd: s.atendimentos, pct: s.percentual }));
        if (resto.length) {
            fatias.push({
                nome: 'Outros',
                qtd: resto.reduce((t, s) => t + s.atendimentos, 0),
                pct: Math.round(resto.reduce((t, s) => t + s.percentual, 0) * 10) / 10,
            });
        }

        graficos.donut = new Chart(el('donutChart'), {
            type: 'doughnut',
            data: {
                labels: fatias.map((f) => f.nome),
                datasets: [{
                    data: fatias.map((f) => f.qtd),
                    backgroundColor: CORES_PIZZA,
                    borderWidth: 2,
                    borderColor: '#020203',
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '60%',
                plugins: {
                    legend: { position: 'bottom', labels: { padding: 16, usePointStyle: true, font: { size: 11 } } },
                    tooltip: {
                        callbacks: {
                            label: (ctx) => ` ${ctx.parsed} atendimento(s) · ${fatias[ctx.dataIndex].pct}%`,
                        },
                    },
                },
            },
        });
    }

    // ---------- Partes da tela ----------

    function variacaoHtml(valor, texto) {
        if (valor === null || valor === undefined) return `<span>sem base de comparação ${texto}</span>`;
        const classe = valor > 0 ? 'sobe' : (valor < 0 ? 'desce' : '');
        return `<span class="${classe}">${formatarPercentual(valor)}</span> ${texto}`;
    }

    function subtitulo(resumo) {
        const inicio = lerDataISO(resumo.inicio);
        const curto = { day: '2-digit', month: '2-digit' };
        let nome;
        if (resumo.periodo === 'ano') nome = `Ano ${inicio.getFullYear()}`;
        else if (resumo.periodo === 'mes') nome = Painel.dataPorExtenso(inicio, { month: 'long', year: 'numeric' });
        else nome = `Semana de ${Painel.dataPorExtenso(resumo.inicio, curto)} a ${Painel.dataPorExtenso(resumo.fim, curto)}`;

        const hoje = dataISO();
        const emAndamento = resumo.inicio <= hoje && hoje <= resumo.fim;
        const sufixo = emAndamento ? ' · em andamento (conta só o que já foi atendido)' : '';
        return nome.charAt(0).toUpperCase() + nome.slice(1) + sufixo;
    }

    function preencherResumo(resumo) {
        el('period-subtitle').textContent = subtitulo(resumo);
        el('val-receita').textContent = formatarMoeda(resumo.receita);
        el('val-atend').textContent = resumo.atendimentos;
        el('val-ticket').textContent = resumo.ticket_medio === null ? '—' : formatarMoeda(resumo.ticket_medio);

        const anterior = resumo.periodo_anterior;
        const anteriorTexto = {
            semana: ['a semana anterior', 'na semana anterior'],
            mes: ['o mês anterior', 'no mês anterior'],
            ano: ['o ano anterior', 'no ano anterior'],
        }[resumo.periodo];
        el('sub-receita').innerHTML = variacaoHtml(anterior.variacao_percentual, `vs. ${anteriorTexto[0]}`);
        el('sub-atend').textContent = `${anterior.atendimentos} ${anteriorTexto[1]}`;

        desenharBarras('barChart', 'caixaBarras', resumo.serie.map((p) => p.rotulo), resumo.serie.map((p) => p.receita));
    }

    function preencherRanking(dados) {
        const lista = el('ranking');
        if (!dados.profissionais.length) {
            Painel.estado(lista, 'Nenhum atendimento realizado no período.');
            return;
        }
        lista.innerHTML = dados.profissionais.map((p) => `
            <div class="rank-item">
                <div class="rank-pos">${p.posicao}</div>
                <div class="rank-info">
                    <h4>${escapar(p.nome)}</h4>
                    <p>${p.atendimentos} atendimento(s) · ${p.clientes} cliente(s)</p>
                </div>
                <div class="rank-value">${formatarMoeda(p.receita)}</div>
            </div>`).join('');
    }

    function preencherComparativo(dados) {
        el('anoComparativo').textContent = dados.ano;
        el('totalAno').textContent =
            `Total do ano: ${formatarMoeda(dados.total.receita)} em ${dados.total.atendimentos} atendimento(s)`;
        desenharBarras('monthChart', 'caixaMensal', dados.meses.map((m) => m.nome), dados.meses.map((m) => m.receita));

        el('mesesVariacao').innerHTML = dados.meses.map((m) => {
            let detalhe;
            if (m.situacao === 'futuro') detalhe = 'ainda não começou';
            else if (m.variacao_percentual === null) detalhe = 'sem comparação';
            else detalhe = variacaoHtml(m.variacao_percentual, '');
            if (m.situacao === 'em_andamento') detalhe += ' · parcial';
            return `
                <div class="mes-item ${m.situacao === 'futuro' ? 'futuro' : ''}">
                    <strong>${m.nome} · ${formatarMoeda(m.receita)}</strong>
                    <span>${detalhe}</span>
                </div>`;
        }).join('');
    }

    // ---------- Carregamento ----------

    function mostrarErro(resposta) {
        const msg = Painel.mensagemDeErro(resposta, 'Não foi possível carregar o Financeiro.');
        el('period-subtitle').textContent = msg;
        Painel.avisar(msg, 'erro');
    }

    async function carregar() {
        const consulta = `periodo=${estado.periodo}&data=${dataISO(estado.data)}`;
        el('period-subtitle').textContent = 'Carregando...';

        const [resumo, servicos, ranking, mensal] = await Promise.all([
            Painel.chamar('GET', `/financeiro/resumo?${consulta}`),
            Painel.chamar('GET', `/financeiro/servicos?${consulta}`),
            Painel.chamar('GET', `/financeiro/atendimentos-por-profissional?${consulta}`),
            Painel.chamar('GET', `/financeiro/receita-mensal?ano=${estado.data.getFullYear()}`),
        ]);

        const falha = [resumo, servicos, ranking, mensal].find((r) => !r.ok);
        if (falha) {
            mostrarErro(falha);
            return;
        }
        preencherResumo(resumo.dados);
        desenharPizza(servicos.dados.servicos);
        preencherRanking(ranking.dados);
        preencherComparativo(mensal.dados);
    }

    // Anda uma semana, um mês ou um ano a partir da data de referência
    function mover(passo) {
        const d = new Date(estado.data);
        if (estado.periodo === 'semana') d.setDate(d.getDate() + 7 * passo);
        else if (estado.periodo === 'mes') d.setMonth(d.getMonth() + passo, 1);
        else d.setFullYear(d.getFullYear() + passo, 0, 1);
        estado.data = d;
        carregar();
    }

    el('period-buttons').addEventListener('click', (e) => {
        const botao = e.target.closest('[data-periodo]');
        if (!botao) return;
        el('period-buttons').querySelectorAll('.toggle-btn').forEach((b) => b.classList.remove('active'));
        botao.classList.add('active');
        estado.periodo = botao.dataset.periodo;
        carregar();
    });
    el('periodoAnterior').addEventListener('click', () => mover(-1));
    el('periodoSeguinte').addEventListener('click', () => mover(1));
    el('periodoAtual').addEventListener('click', () => { estado.data = new Date(); carregar(); });

    // Os botões de período ganham o nome completo no leitor de tela
    el('period-buttons').querySelectorAll('[data-periodo]').forEach((b) => {
        b.setAttribute('aria-label', `Ver por ${NOMES_PERIODO[b.dataset.periodo].toLowerCase()}`);
    });

    carregar();
})();
