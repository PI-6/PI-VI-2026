const modal = document.getElementById('serviceModal');
const form = document.getElementById('serviceForm');
let linhaAtual = null;

function openModal(btnElement = null) {
    modal.classList.add('show');

    if (btnElement) {
        linhaAtual = btnElement.closest('tr');
        document.getElementById('modalTitle').innerText = 'Editar Serviço';

        document.getElementById('servNome').value = linhaAtual.querySelector('h4').innerText;
        document.getElementById('servDesc').value = linhaAtual.querySelector('.service-info p').innerText;
        document.getElementById('servDuracao').value = linhaAtual.querySelector('.service-duration').innerText.replace(' min', '');
        document.getElementById('servPreco').value = linhaAtual.querySelector('.service-price').innerText.replace('R$ ', '');
    } else {
        linhaAtual = null;
        document.getElementById('modalTitle').innerText = 'Novo Serviço';
        form.reset();
    }
}

function closeModal() {
    modal.classList.remove('show');
}

function deleteService(btnElement) {
    if (confirm('Tem certeza que deseja excluir este serviço?')) {
        btnElement.closest('tr').remove();
    }
}

form.addEventListener('submit', function (event) {
    event.preventDefault();

    const nome = document.getElementById('servNome').value;
    const desc = document.getElementById('servDesc').value;
    const duracao = document.getElementById('servDuracao').value + ' min';
    const preco = 'R$ ' + document.getElementById('servPreco').value;

    if (linhaAtual) {
        linhaAtual.querySelector('h4').innerText = nome;
        linhaAtual.querySelector('.service-info p').innerText = desc;
        linhaAtual.querySelector('.service-duration').innerText = duracao;
        linhaAtual.querySelector('.service-price').innerText = preco;
    } else {
        const tbody = document.querySelector('#tabelaServicos tbody');
        const novaLinha = document.createElement('tr');

        novaLinha.innerHTML = `
                    <td>
                        <div class="service-info">
                            <h4>${nome}</h4>
                            <p>${desc}</p>
                        </div>
                    </td>
                    <td><span class="service-duration">${duracao}</span></td>
                    <td><span class="service-price">${preco}</span></td>
                    <td>
                        <div class="action-btns">
                            <button class="btn-icon btn-edit" onclick="openModal(this)"><i class="ph ph-pencil-simple"></i></button>
                            <button class="btn-icon btn-delete" onclick="deleteService(this)"><i class="ph ph-trash"></i></button>
                        </div>
                    </td>
                `;
        tbody.appendChild(novaLinha);
    }

    closeModal();
});