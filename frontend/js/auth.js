(function () {
    const caixa = document.getElementById('container');

    // Abre direto no cadastro quando o link vem de login.html?action=signup
    if (new URLSearchParams(window.location.search).get('action') === 'signup') {
        caixa.classList.add('right-panel-active');
    }

    function criarMensagem(form) {
        const p = document.createElement('p');
        p.className = 'form-mensagem';
        form.querySelector('button').before(p);
        return p;
    }

    function mostrar(p, texto, ok) {
        p.textContent = texto;
        p.style.color = ok ? 'green' : 'crimson';
    }

    // Marca os campos com erro e devolve o texto do primeiro problema
    function marcarErros(form, dados) {
        form.querySelectorAll('input').forEach((input) => input.classList.remove('input-erro'));
        const detalhes = dados.detalhes || {};
        Object.keys(detalhes).forEach((campo) => {
            const input = form.querySelector(`[name="${campo}"]`);
            if (input) input.classList.add('input-erro');
        });
        const campos = Object.keys(detalhes);
        return campos.length ? detalhes[campos[0]] : dados.erro;
    }

    function lerCampos(form) {
        return Object.fromEntries(new FormData(form).entries());
    }

    // ---------- Cadastro ----------
    const formCadastro = document.querySelector('.sign-up-container form');
    const msgCadastro = criarMensagem(formCadastro);

    formCadastro.addEventListener('submit', async (e) => {
        e.preventDefault();
        const corpo = lerCampos(formCadastro);

        if (corpo.senha !== corpo.confirmar_senha) {
            mostrar(msgCadastro, 'As senhas não conferem.', false);
            return;
        }

        try {
            const { ok, dados } = await apiRequest('POST', '/cadastro', corpo);
            if (ok) {
                marcarErros(formCadastro, {});
                mostrar(msgCadastro, dados.mensagem, true);
                formCadastro.reset();
                setTimeout(() => caixa.classList.remove('right-panel-active'), 1200);
            } else {
                mostrar(msgCadastro, marcarErros(formCadastro, dados), false);
            }
        } catch (erro) {
            mostrar(msgCadastro, 'Não foi possível conectar ao servidor.', false);
        }
    });

    // ---------- Login ----------
    const formLogin = document.querySelector('.sign-in-container form');
    const msgLogin = criarMensagem(formLogin);

    formLogin.addEventListener('submit', async (e) => {
        e.preventDefault();
        try {
            const { ok, dados } = await apiRequest('POST', '/login', lerCampos(formLogin));
            if (ok) {
                salvarSessao(dados.token, dados.usuario);
                mostrar(msgLogin, `Bem-vindo, ${dados.usuario.nome}!`, true);
                // Quando as telas existirem, redirecionar pela área:
                // window.location.href = dados.area === 'interna' ? 'dashboard.html' : 'agendamento.html';
            } else {
                mostrar(msgLogin, dados.erro, false);
            }
        } catch (erro) {
            mostrar(msgLogin, 'Não foi possível conectar ao servidor.', false);
        }
    });
})();
