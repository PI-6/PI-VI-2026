function selectDay(element) {
    if (element.classList.contains('empty')) return;
    document.querySelectorAll('.cal-day').forEach(day => {
        day.classList.remove('active');
    });

    element.classList.add('active');

    const diaNum = element.innerText.padStart(2, '0');
    document.getElementById('display-date').innerText = `dia ${diaNum} de novembro de 2026`;
}