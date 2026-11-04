const modal = document.getElementById('estoqueModal');
const form = document.getElementById('estoqueForm');
let linhaAtual = null;

function openModal(btnElement = null) {
    modal.classList.add('show');

    if (btnElement) {
        linhaAtual = btnElement.closest('tr');
        document.getElementById('modalTitle').innerText = 'Editar produto';

        document.getElementById('prodNome').value = linhaAtual.querySelector('h4').innerText;
        document.getElementById('prodDesc').value = linhaAtual.querySelector('.service-info p').innerText;
        document.getElementById('prodEstoque').value = linhaAtual.querySelector('.val-estoque').innerText;
        document.getElementById('prodMinimo').value = linhaAtual.querySelector('.val-minimo').innerText;
        document.getElementById('prodPreco').value = linhaAtual.querySelector('.val-preco').innerText.replace('R$ ', '');
        document.getElementById('prodUnidade').value = linhaAtual.querySelector('.val-unidade').innerText;
    } else {
        linhaAtual = null;
        document.getElementById('modalTitle').innerText = 'Novo produto';
        form.reset();
    }
}

function closeModal() {
    modal.classList.remove('show');
}

function deleteItem(btnElement) {
    if (confirm('Tem certeza que deseja excluir este produto?')) {
        btnElement.closest('tr').remove();
    }
}

form.addEventListener('submit', function (event) {
    event.preventDefault();

    const nome = document.getElementById('prodNome').value;
    const desc = document.getElementById('prodDesc').value;
    const estoque = parseInt(document.getElementById('prodEstoque').value);
    const minimo = parseInt(document.getElementById('prodMinimo').value);
    const preco = document.getElementById('prodPreco').value;
    const unidade = document.getElementById('prodUnidade').value;


    const isAlert = estoque <= minimo;
    const estoqueHTML = isAlert
        ? `<span class="badge-alert"><i class="ph-fill ph-warning"></i> <span class="val-estoque">${estoque}</span> <span class="val-unidade">${unidade}</span></span>`
        : `<span class="td-text"><span class="val-estoque">${estoque}</span> <span class="val-unidade">${unidade}</span></span>`;

    if (linhaAtual) {
        linhaAtual.querySelector('h4').innerText = nome;
        linhaAtual.querySelector('.service-info p').innerText = desc;
        linhaAtual.cells[1].innerHTML = estoqueHTML;
        linhaAtual.cells[2].innerHTML = `<span class="td-text"><span class="val-minimo">${minimo}</span> <span class="val-unidade-min">${unidade}</span></span>`;
        linhaAtual.querySelector('.val-preco').innerText = `R$ ${preco}`;
    } else {
        const tbody = document.querySelector('#tabelaEstoque tbody');
        const novaLinha = document.createElement('tr');

        novaLinha.innerHTML = `
                    <td>
                        <div class="service-info">
                            <h4>${nome}</h4>
                            <p>${desc}</p>
                        </div>
                    </td>
                    <td>${estoqueHTML}</td>
                    <td><span class="td-text"><span class="val-minimo">${minimo}</span> <span class="val-unidade-min">${unidade}</span></span></td>
                    <td><span class="td-text val-preco">R$ ${preco}</span></td>
                    <td>
                        <div class="action-btns">
                            <button class="btn-icon btn-edit" onclick="openModal(this)"><i class="ph ph-pencil-simple"></i></button>
                            <button class="btn-icon btn-delete" onclick="deleteItem(this)"><i class="ph ph-trash"></i></button>
                        </div>
                    </td>
                `;
        tbody.appendChild(novaLinha);
    }

    closeModal();
});