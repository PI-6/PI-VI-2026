// Fluxo de agendamento do cliente (RF04): serviço → profissional → data/hora → confirmação.
// Todos os dados vêm da API pelo cliente central (api.js); nada fica fixo no HTML.
(function () {
    const WEEKDAYS = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb'];
    const MONTHS = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho',
        'agosto', 'setembro', 'outubro', 'novembro', 'dezembro'];
    const MONTHS_AHEAD = 2;              // o cliente agenda até 2 meses à frente
    const PENDING_KEY = 'agendamento_pendente';  // serviço escolhido antes de fazer login

    const state = {
        step: 1,
        services: [],
        service: null,       // { id, nome, duracao_minutos, preco }
        professional: null,  // { id, nome }
        date: null,          // 'AAAA-MM-DD'
        time: null,          // 'HH:MM'
        month: firstOfMonth(new Date()),
        sending: false,
    };

    const $ = (id) => document.getElementById(id);

    // ---------- Utilitários ----------

    function firstOfMonth(date) {
        return new Date(date.getFullYear(), date.getMonth(), 1);
    }

    function today() {
        const now = new Date();
        return new Date(now.getFullYear(), now.getMonth(), now.getDate());
    }

    // Data local em AAAA-MM-DD (toISOString usaria UTC e poderia trocar o dia à noite)
    function toIsoDate(date) {
        const m = String(date.getMonth() + 1).padStart(2, '0');
        const d = String(date.getDate()).padStart(2, '0');
        return `${date.getFullYear()}-${m}-${d}`;
    }

    function formatDateLong(iso) {
        const [y, m, d] = iso.split('-').map(Number);
        return `${d} de ${MONTHS[m - 1]} de ${y}`;
    }

    function formatMoney(value) {
        return Number(value).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
    }

    function formatDuration(minutes) {
        const h = Math.floor(minutes / 60);
        const m = minutes % 60;
        if (!h) return `${m} min`;
        return m ? `${h}h${String(m).padStart(2, '0')}` : `${h}h`;
    }

    function el(tag, className, text) {
        const node = document.createElement(tag);
        if (className) node.className = className;
        if (text !== undefined) node.textContent = text;  // textContent: nome vindo da API nunca vira HTML
        return node;
    }

    function showMessage(text, type) {
        const box = $('booking-message');
        box.textContent = text || '';
        box.className = 'booking-message' + (text ? ' visible' : '') + (type ? ` ${type}` : '');
    }

    function emptyState(container, text) {
        container.replaceChildren(el('p', 'empty-state', text));
    }

    // Chama a API e já trata falta de conexão; devolve { ok, status, dados } ou null
    async function call(method, path, body) {
        try {
            return await apiRequest(method, path, body);
        } catch (error) {
            showMessage('Não foi possível conectar ao servidor. Tente novamente em instantes.', 'error');
            return null;
        }
    }

    function goToLogin() {
        sessionStorage.setItem(PENDING_KEY, JSON.stringify({ servico_id: state.service.id }));
        window.location.href = 'login.html?next=salao.html';
    }

    // ---------- Barra de navegação ----------

    function renderNav() {
        const slot = $('nav-session');
        const user = usuarioLogado();
        slot.replaceChildren();
        if (user) {
            slot.append(el('span', 'nav-user', `Olá, ${user.nome.split(' ')[0]}`));
            const logout = el('button', 'btn-nav nav-logout', 'Sair');
            logout.addEventListener('click', () => {
                encerrarSessao();
                window.location.reload();
            });
            slot.append(logout);
        } else {
            const login = el('a', null, 'Login');
            login.href = 'login.html?next=salao.html';
            const signup = el('a', 'btn-nav', 'Criar Conta');
            signup.href = 'login.html?action=signup&next=salao.html';
            slot.append(login, signup);
        }
    }

    // ---------- Etapa 1: serviço ----------

    async function loadServices() {
        emptyState($('service-list'), 'Carregando serviços...');
        const resp = await call('GET', '/servicos');
        if (!resp) return emptyState($('service-list'), 'Serviços indisponíveis no momento.');
        state.services = resp.ok ? resp.dados : [];
        if (!state.services.length) return emptyState($('service-list'), 'Nenhum serviço disponível no momento.');
        renderServices();
    }

    function renderServices() {
        const list = $('service-list');
        list.replaceChildren();
        state.services.forEach((service) => {
            const item = el('div', 'service-item');
            item.dataset.id = service.id;
            item.setAttribute('role', 'button');
            item.tabIndex = 0;
            if (state.service && state.service.id === service.id) item.classList.add('selected');

            const info = el('div', 'service-info');
            info.append(el('h4', null, service.nome), el('p', null, formatDuration(service.duracao_minutos)));
            const price = el('div', 'service-price', formatMoney(service.preco));
            price.append(el('div', 'check-circle'));
            item.append(info, price);

            const choose = () => selectService(service);
            item.addEventListener('click', choose);
            item.addEventListener('keydown', (e) => { if (e.key === 'Enter') choose(); });
            list.append(item);
        });
    }

    function selectService(service) {
        // Trocar o serviço invalida profissional e horário: nem todo profissional faz todo serviço
        if (!state.service || state.service.id !== service.id) {
            state.professional = null;
            state.date = null;
            state.time = null;
        }
        state.service = service;
        renderServices();
        updateView();
    }

    // ---------- Etapa 2: profissional ----------

    async function loadProfessionals() {
        const list = $('professional-list');
        emptyState(list, 'Carregando profissionais...');
        const resp = await call('GET', `/servicos/${state.service.id}/profissionais`);
        if (!resp) return emptyState(list, 'Profissionais indisponíveis no momento.');
        if (!resp.ok) {
            emptyState(list, resp.dados && resp.dados.erro ? resp.dados.erro : 'Não foi possível carregar.');
            return;
        }
        if (!resp.dados.length) return emptyState(list, 'Nenhum profissional realiza este serviço no momento.');

        list.replaceChildren();
        resp.dados.forEach((professional) => {
            const card = el('div', 'select-card');
            card.setAttribute('role', 'button');
            card.tabIndex = 0;
            if (state.professional && state.professional.id === professional.id) card.classList.add('selected');
            const avatar = el('div', 'pro-avatar');
            avatar.append(el('i', 'ph-fill ph-user'));
            card.append(avatar, el('h4', null, professional.nome));

            const choose = () => {
                if (!state.professional || state.professional.id !== professional.id) {
                    state.date = null;
                    state.time = null;
                }
                state.professional = professional;
                list.querySelectorAll('.select-card').forEach((c) => c.classList.remove('selected'));
                card.classList.add('selected');
                updateView();
            };
            card.addEventListener('click', choose);
            card.addEventListener('keydown', (e) => { if (e.key === 'Enter') choose(); });
            list.append(card);
        });
    }

    // ---------- Etapa 3: data e horário ----------

    function renderCalendar() {
        const grid = $('calendar-grid');
        const first = state.month;
        const minMonth = firstOfMonth(today());
        const maxMonth = new Date(minMonth.getFullYear(), minMonth.getMonth() + MONTHS_AHEAD, 1);
        const lastAllowed = new Date(maxMonth.getFullYear(), maxMonth.getMonth() + 1, 0);

        $('month-label').textContent = `${MONTHS[first.getMonth()]} ${first.getFullYear()}`
            .replace(/^./, (c) => c.toUpperCase());
        $('month-prev').disabled = first <= minMonth;
        $('month-next').disabled = first >= maxMonth;

        grid.replaceChildren(...WEEKDAYS.map((name) => el('div', 'calendar-weekday', name)));
        for (let i = 0; i < first.getDay(); i++) grid.append(el('div'));

        const daysInMonth = new Date(first.getFullYear(), first.getMonth() + 1, 0).getDate();
        for (let d = 1; d <= daysInMonth; d++) {
            const day = new Date(first.getFullYear(), first.getMonth(), d);
            const iso = toIsoDate(day);
            const cell = el('div', 'calendar-day', String(d));
            if (day < today() || day > lastAllowed) {
                cell.classList.add('disabled');
            } else {
                cell.dataset.date = iso;
                if (iso === toIsoDate(today())) cell.classList.add('today');
                if (iso === state.date) cell.classList.add('selected');
                cell.addEventListener('click', () => selectDate(iso));
            }
            grid.append(cell);
        }
    }

    function selectDate(iso) {
        state.date = iso;
        state.time = null;
        renderCalendar();
        loadTimes();
        updateView();
    }

    async function loadTimes() {
        const box = $('dynamic-times');
        const grid = $('time-grid');
        box.style.display = 'block';
        emptyState(grid, 'Carregando horários...');

        const path = `/profissionais/${state.professional.id}/disponibilidade`
            + `?data=${state.date}&servico_id=${state.service.id}`;
        const requested = state.date;
        const resp = await call('GET', path);
        if (state.date !== requested) return;  // o cliente já clicou em outro dia
        if (!resp) return emptyState(grid, 'Horários indisponíveis no momento.');
        if (!resp.ok) {
            emptyState(grid, resp.dados && resp.dados.erro ? resp.dados.erro : 'Não foi possível carregar.');
            return;
        }

        const slots = resp.dados.horarios;
        if (!slots.length) {
            emptyState(grid, 'Sem horários neste dia. Escolha outra data.');
            return;
        }
        grid.replaceChildren();
        slots.forEach((slot) => {
            const button = el('div', 'time-slot');
            button.dataset.time = slot.hora;
            if (slot.status === 'ocupado') {
                // X vermelho: horário de outro cliente, não pode ser escolhido (RF04)
                button.classList.add('occupied');
                button.title = 'Indisponível';
                button.setAttribute('aria-disabled', 'true');
                button.append(el('i', 'ph-bold ph-x'), document.createTextNode(` ${slot.hora}`));
            } else {
                button.textContent = slot.hora;
                if (slot.hora === state.time) button.classList.add('selected');
                button.addEventListener('click', () => {
                    state.time = slot.hora;
                    grid.querySelectorAll('.time-slot').forEach((b) => b.classList.remove('selected'));
                    button.classList.add('selected');
                    updateView();
                });
            }
            grid.append(button);
        });
    }

    // ---------- Etapa 4: confirmação ----------

    function fillSummary() {
        $('res-service').textContent = state.service.nome;
        $('res-pro').textContent = state.professional.nome;
        $('res-datetime').textContent = `${formatDateLong(state.date)} às ${state.time}`;
        $('res-total').textContent = formatMoney(state.service.preco);
    }

    async function confirmBooking() {
        state.sending = true;
        updateView();
        showMessage('Confirmando seu agendamento...');

        const resp = await call('POST', '/agendamentos', {
            profissional_id: state.professional.id,
            servico_id: state.service.id,
            data: state.date,
            hora: state.time,
        });
        state.sending = false;
        if (!resp) return updateView();

        if (resp.ok) {
            const done = resp.dados;
            $('done-service').textContent = done.servico.nome;
            $('done-pro').textContent = done.profissional.nome;
            $('done-datetime').textContent = `${formatDateLong(done.data)}, das ${done.hora_inicio} às ${done.hora_fim}`;
            showMessage('');
            state.step = 'done';
        } else if (resp.status === 409) {
            // Outro cliente pegou o horário entre a escolha e a confirmação: volta aos horários atualizados
            showMessage(resp.dados.erro || 'Esse horário não está mais disponível. Escolha outro.', 'error');
            state.time = null;
            state.step = 3;
            loadTimes();
        } else if (resp.status === 403) {
            showMessage('O agendamento pelo site é só para clientes. Entre com uma conta de cliente.', 'error');
        } else {
            showMessage((resp.dados && resp.dados.erro) || 'Não foi possível concluir o agendamento.', 'error');
        }
        updateView();
    }

    // ---------- Navegação entre as etapas ----------

    function next() {
        if (state.step === 1) {
            if (!usuarioLogado()) return goToLogin();  // a partir daqui as rotas exigem login
            state.step = 2;
            loadProfessionals();
        } else if (state.step === 2) {
            state.step = 3;
            state.month = state.date ? firstOfMonth(new Date(`${state.date}T00:00`)) : firstOfMonth(today());
            renderCalendar();
            if (state.date) loadTimes(); else $('dynamic-times').style.display = 'none';
        } else if (state.step === 3) {
            state.step = 4;
            fillSummary();
        } else if (state.step === 4) {
            return confirmBooking();
        } else if (state.step === 'done') {
            Object.assign(state, { step: 1, service: null, professional: null, date: null, time: null });
            renderServices();
        }
        showMessage('');
        updateView();
    }

    function back() {
        if (typeof state.step !== 'number' || state.step <= 1) return;
        state.step -= 1;  // na etapa 4 este é o botão "Alterar"
        showMessage('');
        updateView();
    }

    function updateView() {
        document.querySelectorAll('.step-content').forEach((s) => s.classList.remove('active-step'));
        $(`step-${state.step}`).classList.add('active-step');

        const reached = state.step === 'done' ? 4 : state.step;
        document.querySelectorAll('.step-dot').forEach((dot, i) => dot.classList.toggle('active', i < reached));

        const back = $('btn-back');
        const main = $('btn-main');
        back.style.display = typeof state.step === 'number' && state.step > 1 ? 'block' : 'none';
        back.textContent = state.step === 4 ? 'Alterar' : 'Voltar';

        const labels = { 1: 'Continuar', 2: 'Continuar', 3: 'Revisar', 4: 'Confirmar', done: 'Novo agendamento' };
        main.textContent = state.sending ? 'Enviando...' : labels[state.step];
        main.disabled = state.sending || {
            1: !state.service,
            2: !state.professional,
            3: !state.time,
            4: false,
            done: false,
        }[state.step];

        $('time-display').textContent = state.service ? `Duração: ${formatDuration(state.service.duracao_minutos)}` : '';
        $('total-display').textContent = state.service ? formatMoney(state.service.preco) : formatMoney(0);
    }

    // Volta do login com um serviço já escolhido: retoma na etapa 2
    function resumePending() {
        const saved = sessionStorage.getItem(PENDING_KEY);
        if (!saved || !usuarioLogado()) return;
        sessionStorage.removeItem(PENDING_KEY);
        const pending = JSON.parse(saved);
        const service = state.services.find((s) => s.id === pending.servico_id);
        if (!service) return;
        selectService(service);
        next();
    }

    $('btn-main').addEventListener('click', next);
    $('btn-back').addEventListener('click', back);
    $('month-prev').addEventListener('click', () => {
        state.month = new Date(state.month.getFullYear(), state.month.getMonth() - 1, 1);
        renderCalendar();
    });
    $('month-next').addEventListener('click', () => {
        state.month = new Date(state.month.getFullYear(), state.month.getMonth() + 1, 1);
        renderCalendar();
    });

    renderNav();
    updateView();
    loadServices().then(resumePending);
})();
