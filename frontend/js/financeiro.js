Chart.defaults.color = '#9BA4B5';
Chart.defaults.font.family = "'Poppins', sans-serif";

const financeData = {
    semana: {
        subtitle: 'Esta Semana',
        receita: 'R$ 1.850,00',
        atendimentos: '18',
        ticket: 'R$ 102,77',
        chartLabels: ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom'],
        chartValues: [350, 420, 280, 0, 500, 300, 0],
        maxScale: 1000,
        step: 250
    },
    mes: {
        subtitle: 'Novembro 2026',
        receita: 'R$ 3.400,00',
        atendimentos: '28',
        ticket: 'R$ 121,42',
        chartLabels: ['Semana 1', 'Semana 2', 'Semana 3', 'Semana 4'],
        chartValues: [800, 1100, 950, 550],
        maxScale: 2000,
        step: 500
    },
    ano: {
        subtitle: 'Ano 2026',
        receita: 'R$ 8.525,00',
        atendimentos: '71',
        ticket: 'R$ 120,07',
        chartLabels: ['jan.', 'fev.', 'mar.', 'abr.', 'mai.', 'jun.', 'jul.', 'ago.', 'set.', 'out.', 'nov.', 'dez.'],
        chartValues: [0, 0, 0, 0, 0, 0, 0, 0, 8000, 500, 0, 0],
        maxScale: 10000,
        step: 2500
    }
};

let barChart;
const ctxBar = document.getElementById('barChart').getContext('2d');

function initBarChart() {
    barChart = new Chart(ctxBar, {
        type: 'bar',
        data: {
            labels: financeData.ano.chartLabels,
            datasets: [{
                label: 'Receita (R$)',
                data: financeData.ano.chartValues,
                backgroundColor: '#D4AF37',
                borderRadius: 4,
                barPercentage: 0.6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: { backgroundColor: 'rgba(0,0,0,0.8)', titleColor: '#F8F8F8', bodyColor: '#D4AF37', padding: 12, cornerRadius: 8, displayColors: false }
            },
            scales: {
                y: { beginAtZero: true, max: 10000, ticks: { stepSize: 2500 }, grid: { color: 'rgba(255,255,255,0.05)', drawBorder: false } },
                x: { grid: { display: false, drawBorder: false } }
            }
        }
    });
}
initBarChart();

function changePeriod(periodKey, btnElement) {
    document.querySelectorAll('.toggle-btn').forEach(btn => btn.classList.remove('active'));
    btnElement.classList.add('active');

    const data = financeData[periodKey];
    document.getElementById('period-subtitle').innerText = data.subtitle;
    document.getElementById('val-receita').innerText = data.receita;
    document.getElementById('val-atend').innerText = data.atendimentos;
    document.getElementById('val-ticket').innerText = data.ticket;


    barChart.data.labels = data.chartLabels;
    barChart.data.datasets[0].data = data.chartValues;
    barChart.options.scales.y.max = data.maxScale;
    barChart.options.scales.y.ticks.stepSize = data.step;
    barChart.update();
}

const ctxDonut = document.getElementById('donutChart').getContext('2d');
new Chart(ctxDonut, {
    type: 'doughnut',
    data: {
        labels: ['Coloração', 'Corte de Cabelo', 'Pedicure', 'Limpeza de Pele', 'Escova', 'Design', 'Manicure', 'Hidratação'],
        datasets: [{
            data: [25, 20, 10, 15, 10, 8, 7, 5],
            backgroundColor: ['#D4AF37', '#8b5cf6', '#3b82f6', '#F3E5AB', 'rgba(212, 175, 55, 0.6)', 'rgba(139, 92, 246, 0.6)', 'rgba(59, 130, 246, 0.6)', '#475569'],
            borderWidth: 2, borderColor: '#020203'
        }]
    },
    options: { responsive: true, maintainAspectRatio: false, cutout: '65%', plugins: { legend: { position: 'bottom', labels: { padding: 20, usePointStyle: true, font: { size: 11 } } } } }
});