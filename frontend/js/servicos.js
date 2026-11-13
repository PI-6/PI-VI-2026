// Serviços (RF07): listar, adicionar, editar e excluir serviços. Só o gerente.
(() => {
    const usuario = Painel.exigirAcesso();
    if (!usuario) return;

    const { escapar, formatarMoeda } = Painel;
    const modal = document.getElementById('serviceModal');
    const form = document.getElementById('serviceForm');
    const tbody = document.querySelector('#tabelaServicos tbody');
    const campo = (id) => document.getElementById(id);

    let servicos = [];
    let editandoId = null;

    function linha(s) {
        return `
            <tr>
                <td>
                    <div class="service-info">
                        <h4>${escapar(s.nome)}</h4>
                        <p>${escapar(s.descricao || '')}</p>
                    </div>
                </td>
                <td><span class="service-duration">${s.duracao_minutos} min</span></td>
                <td><span class="service-price">${formatarMoeda(s.preco)}</span></td>
                <td>
                    <div class="action-btns">
                        <button type="button" class="btn-icon btn-edit" data-editar="${s.id}" title="Editar" aria-label="Editar ${escapar(s.nome)}"><i class="ph ph-pencil-simple"></i></button>
                        <button type="button" class="btn-icon btn-delete" data-excluir="${s.id}" title="Excluir" aria-label="Excluir ${escapar(s.nome)}"><i class="ph ph-trash"></i></button>
                    </div>
                </td>
            </tr>`;
    }

    function mostrarNaTabela(texto, tipo) {
        tbody.innerHTML = `<tr><td colspan="4"><div class="pn-estado pn-estado-${tipo}">${escapar(texto)}</div></td></tr>`;
    }

    async function carregar() {
        const resposta = await Painel.chamar('GET', '/servicos');
        if (!resposta.ok) {
            mostrarNaTabela(Painel.mensagemDeErro(resposta, 'Não foi possível carregar os serviços.'), 'erro');
            return;
        }
        servicos = resposta.dados;
        if (!servicos.length) {
            mostrarNaTabela('Nenhum serviço cadastrado. Use "Novo serviço" para começar.', 'vazio');
            return;
        }
        tbody.innerHTML = servicos.map(linha).join('');
    }

    function abrirModal(servico = null) {
        form.reset();
        Painel.limparErrosFormulario(form);
        editandoId = servico ? servico.id : null;
        campo('modalTitle').textContent = servico ? 'Editar serviço' : 'Novo serviço';
        if (servico) {
            campo('servNome').value = servico.nome;
            campo('servDesc').value = servico.descricao || '';
            campo('servDuracao').value = servico.duracao_minutos;
            campo('servPreco').value = String(servico.preco.toFixed(2)).replace('.', ',');
        }
        modal.classList.add('show');
        campo('servNome').focus();
    }

    function fecharModal() {
        modal.classList.remove('show');
    }

    async function salvar(e) {
        e.preventDefault();
        const corpo = {
            nome: campo('servNome').value.trim(),
            descricao: campo('servDesc').value.trim() || null,
            duracao_minutos: Number(campo('servDuracao').value),
            preco: Painel.lerNumero(campo('servPreco').value),
        };

        const botao = form.querySelector('button[type="submit"]');
        botao.disabled = true;
        const resposta = editandoId
            ? await Painel.chamar('PUT', `/servicos/${editandoId}`, corpo)
            : await Painel.chamar('POST', '/servicos', corpo);
        botao.disabled = false;

        if (!resposta.ok) {
            Painel.mostrarErrosFormulario(form, resposta, {
                nome: 'servNome', descricao: 'servDesc', duracao_minutos: 'servDuracao', preco: 'servPreco',
            });
            return;
        }
        fecharModal();
        Painel.avisar(editandoId ? 'Serviço atualizado.' : 'Serviço cadastrado.');
        carregar();
    }

    async function excluir(servico) {
        const ok = await Painel.confirmar(
            `"${servico.nome}" deixa de aparecer para os clientes. Agendamentos já feitos e o histórico do Financeiro continuam.`,
            { titulo: 'Excluir serviço?', textoBotao: 'Excluir' },
        );
        if (!ok) return;

        const resposta = await Painel.chamar('DELETE', `/servicos/${servico.id}`);
        if (resposta.ok) {
            Painel.avisar('Serviço excluído.');
            carregar();
        } else {
            Painel.avisar(Painel.mensagemDeErro(resposta), 'erro');
        }
    }

    tbody.addEventListener('click', (e) => {
        const botao = e.target.closest('[data-editar], [data-excluir]');
        if (!botao) return;
        const id = Number(botao.dataset.editar || botao.dataset.excluir);
        const servico = servicos.find((s) => s.id === id);
        if (!servico) return;
        if (botao.dataset.editar) abrirModal(servico);
        else excluir(servico);
    });

    campo('btnNovo').addEventListener('click', () => abrirModal());
    modal.querySelectorAll('[data-fechar]').forEach((b) => b.addEventListener('click', fecharModal));
    modal.addEventListener('click', (e) => { if (e.target === modal) fecharModal(); });
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape') fecharModal(); });
    form.addEventListener('submit', salvar);

    carregar();
})();
