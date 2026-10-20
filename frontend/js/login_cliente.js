function switchTab(tabName) {
    document.getElementById('tab-login').classList.remove('active');
    document.getElementById('tab-signup').classList.remove('active');
    document.getElementById('form-login').classList.remove('active');
    document.getElementById('form-signup').classList.remove('active');

    document.getElementById('tab-' + tabName).classList.add('active');
    document.getElementById('form-' + tabName).classList.add('active');

    const headerDiv = document.getElementById('dynamic-header');
    if (tabName === 'login') {
        headerDiv.innerHTML = '<h1>Entrar</h1><p>Acesse para gerenciar seus agendamentos</p>';
    } else {
        headerDiv.innerHTML = '<h1>Criar Conta</h1><p>Agende horários de forma rápida e fácil</p>';
    }
}