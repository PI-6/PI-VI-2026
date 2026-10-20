let currentStep = 1;
let totalValue = 0;
let totalTime = 0;
let servicesCount = 0;

let proSelected = false;
let timeSelected = false;
let chosenDateText = "";

function toggleService(element) {
    const price = parseFloat(element.getAttribute('data-price'));
    const time = parseInt(element.getAttribute('data-time'));
    element.classList.toggle('selected');

    if (element.classList.contains('selected')) {
        totalValue += price; totalTime += time; servicesCount++;
    } else {
        totalValue -= price; totalTime -= time; servicesCount--;
    }

    document.getElementById('total-display').innerText = `R$ ${totalValue.toFixed(2).replace('.', ',')}`;
    document.getElementById('time-display').innerText = `Duração: ${totalTime} min`;
    document.getElementById('btn-main').disabled = totalValue === 0;
}

function selectDate(element, dateText) {
    if (element.classList.contains('disabled')) return;

    document.querySelectorAll('.calendar-day').forEach(el => el.classList.remove('selected'));
    element.classList.add('selected');
    chosenDateText = dateText;

    document.getElementById('dynamic-times').style.display = 'block';
    timeSelected = false;
    document.querySelectorAll('.time-slot').forEach(el => el.classList.remove('selected'));
    updateView();
}

function selectSingle(element, type) {
    if (element.classList.contains('occupied')) return;

    const container = element.parentElement;
    Array.from(container.children).forEach(child => child.classList.remove('selected'));
    element.classList.add('selected');

    if (type === 'pro') { proSelected = true; }
    else if (type === 'time') { timeSelected = true; }

    updateView();
}

function handleNext() {
    if (currentStep < 3) {
        currentStep++; updateView();
    } else if (currentStep === 3) {
        currentStep = 4;

        const profName = document.querySelector('.select-card.selected h4').innerText;
        const chosenTime = document.querySelector('.time-slot.selected').innerText.replace(/[xX]/g, '').trim();

        document.getElementById('res-service').innerText = `${servicesCount} serviço(s)`;
        document.getElementById('res-pro').innerText = profName;
        document.getElementById('res-datetime').innerText = `${chosenDateText} às ${chosenTime}`;
        document.getElementById('res-total').innerText = `R$ ${totalValue.toFixed(2).replace('.', ',')}`;

        updateView();
    } else if (currentStep === 4) {
        alert("Agendamento enviado para o banco de dados");
        window.location.reload();
    }
}

function handlePrev() { if (currentStep > 1) { currentStep--; updateView(); } }

function updateView() {
    document.querySelectorAll('.step-content').forEach(step => step.classList.remove('active-step'));
    document.getElementById('step-' + currentStep).classList.add('active-step');

    document.querySelectorAll('.step-dot').forEach((dot, index) => {
        if (index + 1 <= currentStep) dot.classList.add('active'); else dot.classList.remove('active');
    });

    const btnBack = document.getElementById('btn-back');
    const btnMain = document.getElementById('btn-main');

    if (currentStep === 1) {
        btnBack.style.display = 'none';
        btnMain.innerText = 'Continuar';
        btnMain.disabled = totalValue === 0;
    } else if (currentStep === 2) {
        btnBack.style.display = 'block'; btnBack.innerText = 'Voltar';
        btnMain.innerText = 'Continuar';
        btnMain.disabled = !proSelected;
    } else if (currentStep === 3) {
        btnBack.style.display = 'block'; btnBack.innerText = 'Voltar';
        btnMain.innerText = 'Revisar';
        btnMain.disabled = !timeSelected;
    } else if (currentStep === 4) {
        btnBack.style.display = 'block'; btnBack.innerText = 'Alterar';
        btnMain.innerText = 'Confirmar';
        btnMain.disabled = false;
    }
}