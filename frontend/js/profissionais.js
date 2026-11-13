// Profissionais (RF08): equipe com serviços, horário de trabalho e nível de acesso. Só o gerente.
(() => {
    const usuario = Painel.exigirAcesso();
    if (!usuario) return;

    const { escapar } = Painel;
    const DIAS = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']; // 0 = segunda, como na API

    const modal = document.getElementById('profModal');
    const form = document.getElementById('profForm');
    const tbody = document.querySelector('#tabelaProfissionais tbody');
    const campo = (id) => document.getElementById(id);

    let profissionais = [];
    let servicos = [];
    let editandoId = null;

    // ---------- Tabela ----------

    // Agrupa os dias que têm o mesmo horário: "09:00-18:00 · Seg, Ter, Qua"
    function resumoHorarios(horarios) {
        const grupos = new Map();
        horarios.forEach((h) => {
            const chave = `${h.hora_inicio}-${h.hora_fim}`;
            if (!grupos.has(chave)) grupos.set(chave, []);
            grupos.get(chave).push(DIAS[h.dia_semana]);
        });
        if (!grupos.size) return '<span class="time">Sem horário</span>';
        return [...grupos].map(([horas, dias]) => `
            <span class="time">${horas}</span>
            <p class="days">${dias.join(', ')}</p>`).join('');
    }

    // O repositório devolve os serviços com nome; se vier só o id, buscamos o nome no catálogo
    function nomesServicos(lista) {
        const nomes = lista.map((s) => s.nome || (servicos.find((c) => c.id === s.id) || {}).nome).filter(Boolean);
        return nomes.length ? nomes.join(', ') : 'Nenhum serviço';
    }

    function linha(p) {
        const ehGerente = p.perfil === 'gerente';
        const souEu = p.usuario_id === usuario.id;
        const excluir = souEu
            ? ''
            : `<button type="button" class="btn-icon btn-delete" data-excluir="${p.id}" title="Remover" aria-label="Remover ${escapar(p.nome)}"><i class="ph ph-trash"></i></button>`;
        return `
            <tr>
                <td>
                    <div class="pro-info">
                        <h4>${escapar(p.nome)}${souEu ? ' <small>(você)</small>' : ''}</h4>
                        <p>${escapar(p.email)}</p>
                    </div>
                </td>
                <td><p class="td-services">${escapar(nomesServicos(p.servicos))}</p></td>
                <td><div class="schedule-info">${resumoHorarios(p.horarios)}</div></td>
                <td><span class="badge-access ${ehGerente ? 'badge-gerente' : 'badge-admin'}">${ehGerente ? 'Gerente' : 'Admin'}</span></td>
                <td>
                    <div class="action-btns">
                        <button type="button" class="btn-icon btn-edit" data-editar="${p.id}" title="Editar" aria-label="Editar ${escapar(p.nome)}"><i class="ph ph-pencil-simple"></i></button>
                        ${excluir}
                    </div>
                </td>
            </tr>`;
    }

    function mostrarNaTabela(texto, tipo) {
        tbody.innerHTML = `<tr><td colspan="5"><div class="pn-estado pn-estado-${tipo}">${escapar(texto)}</div></td></tr>`;
    }

    async function carregar() {
        const [respProf, respServ] = await Promise.all([
            Painel.chamar('GET', '/profissionais'),
            Painel.chamar('GET', '/servicos'),
        ]);
        if (!respProf.ok || !respServ.ok) {
            const falha = respProf.ok ? respServ : respProf;
            mostrarNaTabela(Painel.mensagemDeErro(falha, 'Não foi possível carregar a equipe.'), 'erro');
            return;
        }
        profissionais = respProf.dados;
        servicos = respServ.dados;
        desenharServicosDoFormulario();
        if (!profissionais.length) {
            mostrarNaTabela('Nenhum profissional cadastrado.', 'vazio');
            return;
        }
        tbody.innerHTML = profissionais.map(linha).join('');
    }

    // ---------- Formulário ----------

    function desenharServicosDoFormulario() {
        const lista = campo('listaServicos');
        if (!servicos.length) {
            lista.innerHTML = '<p class="form-hint">Cadastre os serviços antes, na tela Serviços.</p>';
            return;
        }
        lista.innerHTML = servicos.map((s) => `
            <label class="checkbox-label"><input type="checkbox" name="servicos" value="${s.id}"> ${escapar(s.nome)}</label>`).join('');
    }

    function marcar(nome, valores) {
        const conjunto = new Set(valores.map(String));
        form.querySelectorAll(`input[name="${nome}"]`).forEach((c) => { c.checked = conjunto.has(c.value); });
    }

    function abrirModal(prof = null) {
        form.reset();
        Painel.limparErrosFormulario(form);
        editandoId = prof ? prof.id : null;
        campo('modalTitle').textContent = prof ? 'Editar profissional' : 'Novo profissional';
        campo('labelSenha').textContent = prof ? 'Nova senha (deixe em branco para manter)' : 'Senha de acesso';
        campo('avisoHorarios').hidden = true;
        campo('profEmail').placeholder = `nome@${usuario.email.split('@')[1]}`;

        if (prof) {
            campo('profNome').value = prof.nome;
            campo('profEmail').value = prof.email;
            campo('profTelefone').value = prof.telefone || '';
            campo('profAcesso').value = prof.perfil;
            marcar('servicos', prof.servicos.map((s) => s.id));
            marcar('dias', prof.horarios.map((h) => h.dia_semana));

            // A tela usa um só horário para todos os dias marcados
            if (prof.horarios.length) {
                campo('profInicio').value = prof.horarios[0].hora_inicio;
                campo('profFim').value = prof.horarios[0].hora_fim;
                const diferentes = new Set(prof.horarios.map((h) => `${h.hora_inicio}-${h.hora_fim}`)).size > 1;
                if (diferentes) {
                    campo('avisoHorarios').textContent =
                        'Os dias tinham horários diferentes. Ao salvar, todos os dias marcados ficam com este horário.';
                    campo('avisoHorarios').hidden = false;
                }
            }
        }
        // O gerente não pode tirar o próprio acesso de gerente (o backend também recusa)
        campo('profAcesso').disabled = Boolean(prof && prof.usuario_id === usuario.id);

        modal.classList.add('show');
        campo('profNome').focus();
    }

    function fecharModal() {
        modal.classList.remove('show');
    }

    function valoresMarcados(nome) {
        return [...form.querySelectorAll(`input[name="${nome}"]:checked`)].map((c) => Number(c.value));
    }

    async function salvar(e) {
        e.preventDefault();
        const inicio = campo('profInicio').value;
        const fim = campo('profFim').value;
        const corpo = {
            nome: campo('profNome').value.trim(),
            email: campo('profEmail').value.trim(),
            telefone: campo('profTelefone').value.trim() || null,
            senha: campo('profSenha').value,
            perfil: campo('profAcesso').value,
            servicos: valoresMarcados('servicos'),
            horarios: valoresMarcados('dias').map((dia) => ({ dia_semana: dia, hora_inicio: inicio, hora_fim: fim })),
        };

        const botao = form.querySelector('button[type="submit"]');
        botao.disabled = true;
        const resposta = editandoId
            ? await Painel.chamar('PUT', `/profissionais/${editandoId}`, corpo)
            : await Painel.chamar('POST', '/profissionais', corpo);
        botao.disabled = false;

        if (!resposta.ok) {
            Painel.mostrarErrosFormulario(form, resposta, {
                nome: 'profNome', email: 'profEmail', telefone: 'profTelefone', senha: 'profSenha',
                perfil: 'profAcesso', horarios: 'profInicio',
            });
            return;
        }
        fecharModal();
        Painel.avisar(editandoId ? 'Profissional atualizado.' : 'Profissional cadastrado. Ele já pode entrar com o e-mail e a senha.');
        carregar();
    }

    async function excluir(prof) {
        const ok = await Painel.confirmar(
            `${prof.nome} perde o acesso ao sistema e deixa de aparecer para agendamento. O histórico de atendimentos continua no Financeiro.`,
            { titulo: 'Remover profissional?', textoBotao: 'Remover' },
        );
        if (!ok) return;

        const resposta = await Painel.chamar('DELETE', `/profissionais/${prof.id}`);
        if (resposta.ok) {
            Painel.avisar('Profissional removido.');
            carregar();
        } else {
            Painel.avisar(Painel.mensagemDeErro(resposta), 'erro');
        }
    }

    // ---------- Eventos ----------

    tbody.addEventListener('click', (e) => {
        const botao = e.target.closest('[data-editar], [data-excluir]');
        if (!botao) return;
        const id = Number(botao.dataset.editar || botao.dataset.excluir);
        const prof = profissionais.find((p) => p.id === id);
        if (!prof) return;
        if (botao.dataset.editar) abrirModal(prof);
        else excluir(prof);
    });

    campo('btnNovo').addEventListener('click', () => abrirModal());
    modal.querySelectorAll('[data-fechar]').forEach((b) => b.addEventListener('click', fecharModal));
    modal.addEventListener('click', (e) => { if (e.target === modal) fecharModal(); });
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape') fecharModal(); });
    form.addEventListener('submit', salvar);

    carregar();
})();
