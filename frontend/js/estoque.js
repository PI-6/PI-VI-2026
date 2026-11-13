// Estoque (RF09): listar, adicionar e editar produtos, com destaque para estoque baixo. Só o gerente.
// O RF09 não prevê exclusão de produto (a API responde 405 ao DELETE).
(() => {
    const usuario = Painel.exigirAcesso();
    if (!usuario) return;

    const { escapar, formatarMoeda, formatarNumero } = Painel;
    const UNIDADES = { un: 'unidade(s)', ml: 'ml', g: 'g', l: 'litro(s)' };

    const modal = document.getElementById('estoqueModal');
    const form = document.getElementById('estoqueForm');
    const tbody = document.querySelector('#tabelaEstoque tbody');
    const filtro = document.getElementById('soEstoqueBaixo');
    const campo = (id) => document.getElementById(id);

    let produtos = [];
    let editandoId = null;

    function quantidadeComUnidade(valor, unidade) {
        return `${formatarNumero(valor)} ${UNIDADES[unidade] || unidade}`;
    }

    function linha(p) {
        const estoque = p.estoque_baixo
            ? `<span class="badge-alert"><i class="ph-fill ph-warning"></i> ${quantidadeComUnidade(p.quantidade, p.unidade)}</span>`
            : `<span class="td-text">${quantidadeComUnidade(p.quantidade, p.unidade)}</span>`;
        return `
            <tr>
                <td>
                    <div class="service-info">
                        <h4>${escapar(p.nome)}</h4>
                        <p>${escapar(p.descricao || '')}</p>
                    </div>
                </td>
                <td>${estoque}</td>
                <td><span class="td-text">${quantidadeComUnidade(p.quantidade_minima, p.unidade)}</span></td>
                <td><span class="td-text">${formatarMoeda(p.preco_unitario)}</span></td>
                <td>
                    <div class="action-btns">
                        <button type="button" class="btn-icon btn-edit" data-editar="${p.id}" title="Editar" aria-label="Editar ${escapar(p.nome)}"><i class="ph ph-pencil-simple"></i></button>
                    </div>
                </td>
            </tr>`;
    }

    function mostrarNaTabela(texto, tipo) {
        tbody.innerHTML = `<tr><td colspan="5"><div class="pn-estado pn-estado-${tipo}">${escapar(texto)}</div></td></tr>`;
    }

    function atualizarResumo() {
        const baixos = produtos.filter((p) => p.estoque_baixo).length;
        const valorTotal = produtos.reduce((soma, p) => soma + p.quantidade * p.preco_unitario, 0);
        campo('estoqueStats').textContent = `${produtos.length} produto(s) · ${baixos} em estoque baixo`
            + ` · valor total em estoque ${formatarMoeda(valorTotal)}`;
    }

    function desenharTabela() {
        const visiveis = filtro.checked ? produtos.filter((p) => p.estoque_baixo) : produtos;
        if (!visiveis.length) {
            mostrarNaTabela(filtro.checked
                ? 'Nenhum produto em estoque baixo.'
                : 'Nenhum produto cadastrado. Use "Novo produto" para começar.', 'vazio');
            return;
        }
        tbody.innerHTML = visiveis.map(linha).join('');
    }

    async function carregar() {
        const resposta = await Painel.chamar('GET', '/produtos');
        if (!resposta.ok) {
            campo('estoqueStats').textContent = '';
            mostrarNaTabela(Painel.mensagemDeErro(resposta, 'Não foi possível carregar o estoque.'), 'erro');
            return;
        }
        produtos = resposta.dados;
        atualizarResumo();
        desenharTabela();
        Painel.atualizarBadgeEstoque();
    }

    // Número para o campo do formulário, com vírgula: 0.5 -> "0,5"
    const paraCampo = (valor) => String(valor).replace('.', ',');

    function abrirModal(produto = null) {
        form.reset();
        Painel.limparErrosFormulario(form);
        editandoId = produto ? produto.id : null;
        campo('modalTitle').textContent = produto ? 'Editar produto' : 'Novo produto';
        if (produto) {
            campo('prodNome').value = produto.nome;
            campo('prodDesc').value = produto.descricao || '';
            campo('prodEstoque').value = paraCampo(produto.quantidade);
            campo('prodMinimo').value = paraCampo(produto.quantidade_minima);
            campo('prodPreco').value = produto.preco_unitario.toFixed(2).replace('.', ',');
            campo('prodUnidade').value = produto.unidade;
        }
        modal.classList.add('show');
        campo('prodNome').focus();
    }

    function fecharModal() {
        modal.classList.remove('show');
    }

    async function salvar(e) {
        e.preventDefault();
        // Quantidades vão como texto: a API aceita vírgula ("0,5") e valida as casas decimais
        const corpo = {
            nome: campo('prodNome').value.trim(),
            descricao: campo('prodDesc').value.trim() || null,
            quantidade: campo('prodEstoque').value.trim(),
            quantidade_minima: campo('prodMinimo').value.trim(),
            preco_unitario: Painel.lerNumero(campo('prodPreco').value),
            unidade: campo('prodUnidade').value,
        };

        const botao = form.querySelector('button[type="submit"]');
        botao.disabled = true;
        const resposta = editandoId
            ? await Painel.chamar('PUT', `/produtos/${editandoId}`, corpo)
            : await Painel.chamar('POST', '/produtos', corpo);
        botao.disabled = false;

        if (!resposta.ok) {
            Painel.mostrarErrosFormulario(form, resposta, {
                nome: 'prodNome', descricao: 'prodDesc', quantidade: 'prodEstoque',
                quantidade_minima: 'prodMinimo', preco_unitario: 'prodPreco', unidade: 'prodUnidade',
            });
            return;
        }
        fecharModal();
        const salvo = resposta.dados;
        Painel.avisar(salvo.estoque_baixo
            ? `${salvo.nome} salvo. Atenção: está em estoque baixo.`
            : `${salvo.nome} salvo.`);
        carregar();
    }

    tbody.addEventListener('click', (e) => {
        const botao = e.target.closest('[data-editar]');
        if (!botao) return;
        const produto = produtos.find((p) => p.id === Number(botao.dataset.editar));
        if (produto) abrirModal(produto);
    });

    filtro.addEventListener('change', desenharTabela);
    campo('btnNovo').addEventListener('click', () => abrirModal());
    modal.querySelectorAll('[data-fechar]').forEach((b) => b.addEventListener('click', fecharModal));
    modal.addEventListener('click', (e) => { if (e.target === modal) fecharModal(); });
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape') fecharModal(); });
    form.addEventListener('submit', salvar);

    carregar();
})();
