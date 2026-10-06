(function () {
    const API = 'http://127.0.0.1:5000/api';
    const caixa = document.getElementById('container');

    // Abre direto no cadastro quando o link vem de login.html?action=signup
    if (new URLSearchParams(window.location.search).get('action') === 'signup') {
        caixa.classList.add('right-panel-active');
    }

    function criarMensagem(form) {
        const p = document.createElement('p');
        p.style.cssText = 'font-size:14px; min-height:18px; margin:6px 0;';
        form.querySelector('button').before(p);
        return p;
    }

    function mostrar(p, texto, ok) {
        p.textContent = texto;
        p.style.color = ok ? 'green' : 'crimson';
    }

    async function enviar(rota, corpo) {
        const resp = await fetch(`${API}/${rota}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(corpo),
        });
        const dados = await resp.json();
        return { ok: resp.ok, dados };
    }

    // ---------- Cadastro ----------
    const formCadastro = document.querySelector('.sign-up-container form');
    const msgCadastro = criarMensagem(formCadastro);

    formCadastro.addEventListener('submit', async (e) => {
        e.preventDefault();
        const corpo = {
            nome: formCadastro.querySelector('input[type="text"]').value,
            email: formCadastro.querySelector('input[type="email"]').value,
            senha: formCadastro.querySelector('input[type="password"]').value,
        };
        try {
            const { ok, dados } = await enviar('cadastro', corpo);
            if (ok) {
                mostrar(msgCadastro, dados.mensagem, true);
                formCadastro.reset();
                setTimeout(() => caixa.classList.remove('right-panel-active'), 1200);
            } else {
                mostrar(msgCadastro, dados.erro, false);
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
        const corpo = {
            email: formLogin.querySelector('input[type="email"]').value,
            senha: formLogin.querySelector('input[type="password"]').value,
        };
        try {
            const { ok, dados } = await enviar('login', corpo);
            if (ok) {
                localStorage.setItem('usuario', JSON.stringify(dados));
                mostrar(msgLogin, `Bem-vindo, ${dados.nome}!`, true);
                // Quando a tela do dashboard existir:
                // window.location.href = 'dashboard.html';
            } else {
                mostrar(msgLogin, dados.erro, false);
            }
        } catch (erro) {
            mostrar(msgLogin, 'Não foi possível conectar ao servidor.', false);
        }
    });
})();