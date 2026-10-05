window.addEventListener('pywebviewready', function() {
    const btnSubmit = document.querySelector('button[type="submit"]');
    const unidadeSelect = document.getElementById('unidade');
    
    btnSubmit.disabled = true;
    unidadeSelect.innerHTML = '<option value="">Carregando unidades...</option>';
    unidadeSelect.disabled = true;
    
    // Garantir a execução em ordem usando chaining
    window.pywebview.api.load_initial_data().then(function(data) {
        if (data && data["usuario"] && data["senha"]) {
            document.getElementById('username').value = data["usuario"];
            document.getElementById('password').value = data["senha"];
            document.getElementById('salvarPadrao').checked = true;

            if (data.unidade) {
                window.last_unit = data.unidade;
            }
        }
        
        return window.pywebview.api.fetch_units();
    }).then(function(unidades) {
        unidadeSelect.innerHTML = '';
        if (unidades && unidades.length > 0) {
            unidades.forEach(function(u) {
                const opt = document.createElement('option');
                opt.value = u;
                opt.textContent = u;
                unidadeSelect.appendChild(opt);
            });
            unidadeSelect.disabled = false;
            btnSubmit.disabled = false;
            
            if (window.last_unit) {
                unidadeSelect.value = window.last_unit;
            }
        } else {
            unidadeSelect.innerHTML = '<option value="">Erro ao carregar unidades</option>';
        }
    }).catch(function(err) {
        console.error("Erro na API Python:", err);
        unidadeSelect.innerHTML = '<option value="">Falha na comunicação</option>';
        unidadeSelect.disabled = false;
        btnSubmit.disabled = false;
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