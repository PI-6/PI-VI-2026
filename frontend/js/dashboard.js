const dateElement = document.getElementById('current-date');
const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
const today = new Date();
const formattedDate = today.toLocaleDateString('pt-PT', options);
dateElement.innerText = `${formattedDate} · Visão geral do salão`;