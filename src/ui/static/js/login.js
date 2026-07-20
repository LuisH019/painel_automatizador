window.addEventListener('pywebviewready', function() {
    window.pywebview.api.load_initial_data().then(function(data) {
        if (data && data["usuario"] && data["senha"]) {
            document.getElementById('username').value = data["usuario"];
            document.getElementById('password').value = data["senha"];
            document.getElementById('salvarPadrao').checked = true;

            if (dados.unidade) {
                document.getElementById('unidade').value = dados.unidade;
            }
        }
    });
});

document.getElementById('loginForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    // 1. Captura o botão e altera seu estado instantaneamente
    const btnSubmit = document.querySelector('button[type="submit"]');
    btnSubmit.disabled = true;
    btnSubmit.innerText = "Autenticando...";
    btnSubmit.style.cursor = "wait";
    
    const user = document.getElementById('username').value;
    const pass = document.getElementById('password').value;
    const unit = document.getElementById('unidade').value;
    const remember = document.getElementById('salvarPadrao').checked;

    if (window.pywebview && window.pywebview.api) {
        // window.pywebview.api.authenticate(user, pass, unit, remember);
        window.pywebview.api.process_login();
    } else {
        alert("Erro crítico: Sem comunicação com o processo nativo.");
        // Reverte o botão caso dê erro para o operador tentar de novo
        btnSubmit.disabled = false;
        btnSubmit.innerText = "Acessar";
        btnSubmit.style.cursor = "pointer";
    }
});

document.querySelector('.logo').addEventListener('dblclick', function() {
    if (window.pywebview && window.pywebview.api) {
        window.pywebview.api.ask_admin_config();
    }
});