// Agenda (RF06): agendamentos e bloqueios do dia, exclusão de agendamento e bloqueio de horários.
(() => {
    const usuario = Painel.exigirAcesso();
    if (!usuario) return;

    const { escapar, formatarMoeda, dataISO, lerDataISO } = Painel;
    const ehGerente = usuario.perfil === 'gerente';

    const DIAS_SEMANA = ['dom', 'seg', 'ter', 'qua', 'qui', 'sex', 'sáb'];
    const STATUS = {
        agendado: ['confirmado', 'Confirmado'],
        concluido: ['concluido', 'Concluído'],
    };

    const estado = {
        mes: new Date(new Date().getFullYear(), new Date().getMonth(), 1),
        dia: dataISO(),
        profissionais: [],
        meuProfissionalId: null, // cadastro de profissional do usuário logado, se houver
    };

    const el = (id) => document.getElementById(id);

    // A API numera os dias de 0 = segunda a 6 = domingo; o getDay() do JS começa no domingo
    const diaSemanaApi = (data) => (data.getDay() + 6) % 7;

    // O admin só bloqueia a própria agenda; o gerente, a de qualquer profissional
    function podeGerenciar(profissionalId) {
        return ehGerente || profissionalId === estado.meuProfissionalId;
    }

    // ---------- Calendário ----------

    function desenharCalendario() {
        const { mes } = estado;
        el('tituloMes').textContent = mes.toLocaleDateString('pt-BR', { month: 'long', year: 'numeric' });

        const hoje = dataISO();
        const celulas = DIAS_SEMANA.map((d) => `<div class="cal-weekday">${d}</div>`);
        for (let i = 0; i < mes.getDay(); i += 1) celulas.push('<div class="cal-day empty"></div>');

        const ultimoDia = new Date(mes.getFullYear(), mes.getMonth() + 1, 0).getDate();
        for (let d = 1; d <= ultimoDia; d += 1) {
            const iso = dataISO(new Date(mes.getFullYear(), mes.getMonth(), d));
            const classes = ['cal-day'];
            if (iso === estado.dia) classes.push('active');
            if (iso === hoje) classes.push('today');
            celulas.push(`<button type="button" class="${classes.join(' ')}" data-dia="${iso}">${d}</button>`);
        }
        el('calendario').innerHTML = celulas.join('');
    }

    function selecionarDia(iso) {
        estado.dia = iso;
        const data = lerDataISO(iso);
        estado.mes = new Date(data.getFullYear(), data.getMonth(), 1);
        desenharCalendario();
        carregarDia();
    }

    // ---------- Lista do dia ----------

    function cartaoAgendamento(a) {
        const [classe, rotulo] = STATUS[a.status] || ['pendente', a.status];
        const acoes = a.status === 'agendado'
            ? `<div class="app-actions">
                   <button type="button" class="pn-btn pn-btn-perigo" data-excluir="${a.id}">Excluir</button>
               </div>`
            : '';
        return `
            <div class="appointment-card glass-panel">
                <div class="app-time">${a.hora_inicio}<br><small>${a.hora_fim}</small></div>
                <div class="app-details">
                    <h4>${escapar(a.servico.nome)}</h4>
                    <p><i class="ph-fill ph-user"></i> Cliente: ${escapar(a.cliente.nome)}</p>
                    <p><i class="ph-fill ph-scissors"></i> Profissional: ${escapar(a.profissional.nome)}</p>
                </div>
                <div class="app-status">
                    <span class="app-price">${formatarMoeda(a.valor)}</span>
                    <span class="badge ${classe}">${rotulo}</span>
                    ${acoes}
                </div>
            </div>`;
    }

    function cartaoBloqueio(b) {
        const tipo = b.tipo === 'semanal' ? 'Toda semana' : 'Só neste período';
        const acoes = podeGerenciar(b.profissional.id)
            ? `<div class="app-actions">
                   <button type="button" class="pn-btn" data-desbloquear="${b.tipo}:${b.id}">Desbloquear</button>
               </div>`
            : '';
        return `
            <div class="appointment-card bloqueio glass-panel">
                <div class="app-time">${b.hora_inicio}<br><small>${b.hora_fim}</small></div>
                <div class="app-details">
                    <h4>Horário bloqueado${b.motivo ? ` · ${escapar(b.motivo)}` : ''}</h4>
                    <p><i class="ph-fill ph-scissors"></i> Profissional: ${escapar(b.profissional.nome)}</p>
                    <p><i class="ph-fill ph-repeat"></i> ${tipo}</p>
                </div>
                <div class="app-status">
                    <span class="badge bloqueado">Bloqueado</span>
                    ${acoes}
                </div>
            </div>`;
    }

    async function carregarDia() {
        el('display-date').textContent = Painel.dataPorExtenso(estado.dia);
        el('resumoDia').textContent = 'Carregando...';
        const lista = el('listaDia');
        Painel.estado(lista, 'Carregando...');

        const filtro = el('filtroProfissional').value;
        const rota = `/agendamentos?data=${estado.dia}${filtro ? `&profissional_id=${filtro}` : ''}`;
        const resposta = await Painel.chamar('GET', rota);
        if (!resposta.ok) {
            el('resumoDia').textContent = '';
            Painel.estado(lista, Painel.mensagemDeErro(resposta, 'Não foi possível carregar a agenda.'), 'erro');
            return;
        }

        const { agendamentos, bloqueios } = resposta.dados;
        const previsto = agendamentos.reduce((soma, a) => soma + a.valor, 0);
        el('resumoDia').textContent =
            `${agendamentos.length} atendimento(s) · receita prevista ${formatarMoeda(previsto)}`
            + (bloqueios.length ? ` · ${bloqueios.length} bloqueio(s)` : '');

        const itens = [
            ...agendamentos.map((a) => ({ hora: a.hora_inicio, html: cartaoAgendamento(a) })),
            ...bloqueios.map((b) => ({ hora: b.hora_inicio, html: cartaoBloqueio(b) })),
        ].sort((x, y) => x.hora.localeCompare(y.hora));

        if (!itens.length) {
            Painel.estado(lista, 'Nenhum atendimento agendado para este dia.');
            return;
        }
        lista.innerHTML = itens.map((i) => i.html).join('');
    }

    async function excluirAgendamento(id) {
        const ok = await Painel.confirmar(
            'O agendamento será cancelado e o horário volta a ficar livre para outros clientes.',
            { titulo: 'Excluir agendamento?', textoBotao: 'Excluir' },
        );
        if (!ok) return;

        const resposta = await Painel.chamar('DELETE', `/agendamentos/${id}`);
        if (resposta.ok) {
            Painel.avisar('Agendamento excluído. O horário foi liberado.');
            carregarDia();
        } else {
            Painel.avisar(Painel.mensagemDeErro(resposta), 'erro');
        }
    }

    async function desbloquear(chave) {
        const [tipo, id] = chave.split(':');
        const mensagem = tipo === 'semanal'
            ? 'Este bloqueio se repete toda semana. Ao desbloquear, ele deixa de valer em todas as semanas.'
            : 'O horário volta a ficar disponível para agendamento.';
        const ok = await Painel.confirmar(mensagem, { titulo: 'Desbloquear horário?', textoBotao: 'Desbloquear' });
        if (!ok) return;

        const resposta = await Painel.chamar('DELETE', `/bloqueios/${tipo}/${id}`);
        if (resposta.ok) {
            Painel.avisar('Horário desbloqueado.');
            carregarDia();
        } else {
            Painel.avisar(Painel.mensagemDeErro(resposta), 'erro');
        }
    }

    // ---------- Modal de bloqueio ----------

    const modal = el('modalBloqueio');
    const form = el('formBloqueio');

    function tipoBloqueio() {
        return form.querySelector('input[name="tipo"]:checked').value;
    }

    function mostrarCamposDoTipo() {
        const tipo = tipoBloqueio();
        form.querySelectorAll('[data-tipo]').forEach((campo) => {
            campo.hidden = campo.dataset.tipo !== tipo;
        });
    }

    function abrirModal() {
        form.reset();
        Painel.limparErrosFormulario(form);
        const conflitos = form.querySelector('.pn-lista-conflitos');
        if (conflitos) conflitos.remove();

        const select = el('bloqProfissional');
        const permitidos = estado.profissionais.filter((p) => podeGerenciar(p.id));
        select.innerHTML = permitidos.map((p) => `<option value="${p.id}">${escapar(p.nome)}</option>`).join('');
        const filtro = Number(el('filtroProfissional').value);
        if (permitidos.some((p) => p.id === filtro)) select.value = String(filtro);
        select.disabled = permitidos.length === 1;

        el('bloqData').value = estado.dia;
        el('bloqDiaSemana').value = String(diaSemanaApi(lerDataISO(estado.dia)));
        mostrarCamposDoTipo();
        modal.hidden = false;
        el('bloqInicio').focus();
    }

    function fecharModal() {
        modal.hidden = true;
    }

    function corpoDoBloqueio() {
        const corpo = {
            tipo: tipoBloqueio(),
            hora_inicio: el('bloqInicio').value,
            hora_fim: el('bloqFim').value,
            motivo: el('bloqMotivo').value.trim() || null,
        };
        if (corpo.tipo === 'pontual') {
            corpo.data = el('bloqData').value;
        } else {
            corpo.dia_semana = Number(el('bloqDiaSemana').value);
            if (el('bloqValidoAte').value) corpo.valido_ate = el('bloqValidoAte').value;
        }
        return corpo;
    }

    async function salvarBloqueio(e) {
        e.preventDefault();
        const profissionalId = el('bloqProfissional').value;
        const botao = form.querySelector('button[type="submit"]');
        botao.disabled = true;
        const resposta = await Painel.chamar('POST', `/profissionais/${profissionalId}/bloqueios`, corpoDoBloqueio());
        botao.disabled = false;

        if (resposta.ok) {
            fecharModal();
            Painel.avisar('Horário bloqueado.');
            carregarDia();
            return;
        }

        Painel.mostrarErrosFormulario(form, resposta, {
            data: 'bloqData', dia_semana: 'bloqDiaSemana', hora_inicio: 'bloqInicio',
            hora_fim: 'bloqFim', valido_ate: 'bloqValidoAte', motivo: 'bloqMotivo',
        });

        // 409: há clientes agendados no intervalo; listamos para a equipe remarcar antes
        const conflitos = resposta.status === 409 && resposta.dados.detalhes && resposta.dados.detalhes.agendamentos;
        if (conflitos && conflitos.length) {
            const msg = form.querySelector('.pn-form-msg');
            msg.textContent = resposta.dados.erro;
            const lista = document.createElement('ul');
            lista.className = 'pn-lista-conflitos';
            lista.innerHTML = conflitos.map((c) => `<li>${Painel.dataPorExtenso(c.data,
                { day: '2-digit', month: '2-digit', year: 'numeric' })}, ${c.hora_inicio} às ${c.hora_fim}</li>`).join('');
            msg.after(lista);
        }
    }

    // ---------- Profissionais (filtro e modal) ----------

    async function carregarProfissionais() {
        const resposta = await Painel.chamar('GET', '/profissionais');
        if (!resposta.ok) {
            Painel.avisar(Painel.mensagemDeErro(resposta, 'Não foi possível carregar os profissionais.'), 'erro');
            el('btnBloquear').hidden = true;
            return;
        }
        estado.profissionais = resposta.dados;
        const meu = estado.profissionais.find((p) => p.usuario_id === usuario.id);
        estado.meuProfissionalId = meu ? meu.id : null;

        el('filtroProfissional').insertAdjacentHTML('beforeend', estado.profissionais
            .map((p) => `<option value="${p.id}">${escapar(p.nome)}</option>`).join(''));

        // O admin começa vendo a própria agenda (pode trocar para "Todos")
        if (!ehGerente && meu) el('filtroProfissional').value = String(meu.id);

        // Sem nenhuma agenda que possa bloquear, o botão não aparece
        el('btnBloquear').hidden = !estado.profissionais.some((p) => podeGerenciar(p.id));
    }

    // ---------- Eventos ----------

    el('calendario').addEventListener('click', (e) => {
        const dia = e.target.closest('[data-dia]');
        if (dia) selecionarDia(dia.dataset.dia);
    });
    el('mesAnterior').addEventListener('click', () => {
        estado.mes = new Date(estado.mes.getFullYear(), estado.mes.getMonth() - 1, 1);
        desenharCalendario();
    });
    el('mesSeguinte').addEventListener('click', () => {
        estado.mes = new Date(estado.mes.getFullYear(), estado.mes.getMonth() + 1, 1);
        desenharCalendario();
    });
    el('btnHoje').addEventListener('click', () => selecionarDia(dataISO()));
    el('filtroProfissional').addEventListener('change', carregarDia);

    el('listaDia').addEventListener('click', (e) => {
        const excluir = e.target.closest('[data-excluir]');
        if (excluir) excluirAgendamento(Number(excluir.dataset.excluir));
        const desbloq = e.target.closest('[data-desbloquear]');
        if (desbloq) desbloquear(desbloq.dataset.desbloquear);
    });

    el('btnBloquear').addEventListener('click', abrirModal);
    el('cancelarBloqueio').addEventListener('click', fecharModal);
    modal.addEventListener('click', (e) => { if (e.target === modal) fecharModal(); });
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && !modal.hidden) fecharModal(); });
    form.querySelectorAll('input[name="tipo"]').forEach((r) => r.addEventListener('change', mostrarCamposDoTipo));
    form.addEventListener('submit', salvarBloqueio);

    // ---------- Início ----------

    desenharCalendario();
    carregarProfissionais().then(carregarDia);
})();
