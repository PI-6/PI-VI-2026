document.addEventListener("DOMContentLoaded", () => {
    const btnTestar = document.getElementById("btnTestarApi");
    const textoResultado = document.getElementById("resultadoApi");

    btnTestar.addEventListener("click", async () => {
        textoResultado.innerText = "Conectando...";
        

        const resposta = await testarConexao();
        

        textoResultado.innerText = resposta.mensagem;
    });
});