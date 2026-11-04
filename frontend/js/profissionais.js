const modal = document.getElementById('profModal');
const form = document.getElementById('profForm');
let linhaAtual = null;

function openModal(btnElement = null) {
    modal.classList.add('show');
    form.reset();

    if (btnElement) {
        linhaAtual = btnElement.closest('tr');
        document.getElementById('modalTitle').innerText = 'Editar profissional';

        document.getElementById('profNome').value = linhaAtual.querySelector('.val-nome').innerText;
        document.getElementById('profEmail').value = linhaAtual.querySelector('.val-email').innerText;
        document.getElementById('profEspec').value = linhaAtual.querySelector('.val-espec') ? linhaAtual.querySelector('.val-espec').innerText : '';

        let acesso = linhaAtual.querySelector('.val-acesso').innerText;
        document.getElementById('profAcesso').value = acesso;

        const horasStr = linhaAtual.querySelector('.val-horas').innerText;
        if (horasStr.includes('-')) {
            const partesHora = horasStr.split('-');
            document.getElementById('profInicio').value = partesHora[0].trim();
            document.getElementById('profFim').value = partesHora[1].trim();
        }

        const diasStr = linhaAtual.querySelector('.val-dias').innerText;
        document.querySelectorAll('input[name="dias"]').forEach(checkbox => {
            if (diasStr.includes(checkbox.value)) checkbox.checked = true;
        });

        const servicosStr = linhaAtual.querySelector('.val-servicos').innerText;
        document.querySelectorAll('input[name="servicos"]').forEach(checkbox => {
            if (servicosStr.includes(checkbox.value)) checkbox.checked = true;
        });

    } else {
        linhaAtual = null;
        document.getElementById('modalTitle').innerText = 'Novo profissional';
    }
}

function closeModal() {
    modal.classList.remove('show');
}

function deleteItem(btnElement) {
    if (confirm('Tem certeza que deseja remover este profissional?')) {
        btnElement.closest('tr').remove();
    }
}

form.addEventListener('submit', function (event) {
    event.preventDefault();

    const nome = document.getElementById('profNome').value;
    const email = document.getElementById('profEmail').value;
    const espec = document.getElementById('profEspec').value;

    const inicio = document.getElementById('profInicio').value;
    const fim = document.getElementById('profFim').value;
    const horas = `${inicio}-${fim}`;

    const diasArray = [];
    document.querySelectorAll('input[name="dias"]:checked').forEach(el => diasArray.push(el.value));
    const dias = diasArray.join(', ');

    const servicosArray = [];
    document.querySelectorAll('input[name="servicos"]:checked').forEach(el => servicosArray.push(el.value));
    const servicos = servicosArray.join(', ') || 'Nenhum serviço selecionado';

    const acesso = document.getElementById('profAcesso').value;
    const badgeClass = acesso === 'Gerente' ? 'badge-gerente' : 'badge-admin';
    const acessoDisplay = acesso === 'Admin' ? 'Admin' : 'Gerente';
    const acessoHTML = `<span class="badge-access ${badgeClass} val-acesso">${acessoDisplay}</span>`;

    if (linhaAtual) {
        linhaAtual.querySelector('.val-nome').innerText = nome;
        linhaAtual.querySelector('.val-email').innerText = email;
        if (linhaAtual.querySelector('.val-espec')) linhaAtual.querySelector('.val-espec').innerText = espec;
        linhaAtual.querySelector('.val-servicos').innerText = servicos;
        linhaAtual.querySelector('.val-horas').innerText = horas;
        linhaAtual.querySelector('.val-dias').innerText = dias;
        linhaAtual.cells[3].innerHTML = acessoHTML;
    } else {
        const tbody = document.querySelector('#tabelaProfissionais tbody');
        const novaLinha = document.createElement('tr');

        novaLinha.innerHTML = `
                    <td>
                        <div class="pro-info">
                            <h4 class="val-nome">${nome}</h4>
                            <p class="val-email">${email}</p>
                            <span class="val-espec" style="display:none;">${espec}</span>
                        </div>
                    </td>
                    <td><p class="td-services val-servicos">${servicos}</p></td>
                    <td>
                        <div class="schedule-info">
                            <span class="time val-horas">${horas}</span>
                            <p class="days val-dias">${dias}</p>
                        </div>
                    </td>
                    <td>${acessoHTML}</td>
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