function renderCastDevices(devices) {
    const castSelect = document.getElementById('dispositivoCast');
    castSelect.innerHTML = '';

    const list = Array.isArray(devices) ? devices : [];
    const savedDevice = window.last_cast_device || '';

    if (list.length > 0) {
        list.forEach(function(d) {
            const opt = document.createElement('option');
            opt.value = d;
            opt.textContent = d;
            castSelect.appendChild(opt);
        });
    }

    // Se havia uma TV salva como padrão que ainda não respondeu na varredura rápida, mantém na lista
    if (savedDevice && list.indexOf(savedDevice) === -1) {
        const savedOpt = document.createElement('option');
        savedOpt.value = savedDevice;
        savedOpt.textContent = savedDevice + ' (Padrão salvo)';
        castSelect.appendChild(savedOpt);
    }

    const noneOpt = document.createElement('option');
    noneOpt.value = '';
    noneOpt.textContent = list.length > 0
        ? 'Não transmitir (Apenas monitor virtual)'
        : 'Nenhuma TV encontrada (Apenas monitor virtual)';
    castSelect.appendChild(noneOpt);

    if (savedDevice) {
        castSelect.value = savedDevice;
    } else if (list.length > 0) {
        castSelect.value = list[0];
    } else {
        castSelect.value = '';
    }
}

window.addEventListener('pywebviewready', function() {
    const btnSubmit = document.querySelector('button[type="submit"]');
    const unidadeSelect = document.getElementById('unidade');
    const castSelect = document.getElementById('dispositivoCast');
    const btnRefreshCast = document.getElementById('btnRefreshCast');
    
    btnSubmit.disabled = true;
    unidadeSelect.innerHTML = '<option value="">Carregando unidades...</option>';
    unidadeSelect.disabled = true;

    castSelect.innerHTML = '<option value="">Buscando TVs na rede...</option>';
    castSelect.disabled = true;
    btnRefreshCast.disabled = true;
    
    window.pywebview.api.load_initial_data().then(function(data) {
        if (data && data["usuario"] && data["senha"]) {
            document.getElementById('username').value = data["usuario"];
            document.getElementById('password').value = data["senha"];
            document.getElementById('salvarPadrao').checked = true;

            if (data.unidade) {
                window.last_unit = data.unidade;
            }
            if (data.dispositivo_cast) {
                window.last_cast_device = data.dispositivo_cast;
            }
        }
        
        // Dispara busca de TVs via mDNS (~150ms) em paralelo com o scraping de unidades
        window.pywebview.api.fetch_cast_devices(true).then(function(devices) {
            renderCastDevices(devices);
            castSelect.disabled = false;
            btnRefreshCast.disabled = false;
        }).catch(function(err) {
            console.error("Erro ao buscar TVs:", err);
            renderCastDevices([]);
            castSelect.disabled = false;
            btnRefreshCast.disabled = false;
        });

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

document.getElementById('btnRefreshCast').addEventListener('click', function() {
    const castSelect = document.getElementById('dispositivoCast');
    const btnRefreshCast = document.getElementById('btnRefreshCast');

    if (!window.pywebview || !window.pywebview.api) return;

    window.last_cast_device = castSelect.value || window.last_cast_device;
    castSelect.innerHTML = '<option value="">Escaneando rede...</option>';
    castSelect.disabled = true;
    btnRefreshCast.disabled = true;

    window.pywebview.api.fetch_cast_devices(true).then(function(devices) {
        renderCastDevices(devices);
        castSelect.disabled = false;
        btnRefreshCast.disabled = false;
    }).catch(function(err) {
        console.error("Erro ao atualizar dispositivos Cast:", err);
        renderCastDevices([]);
        castSelect.disabled = false;
        btnRefreshCast.disabled = false;
    });
});

document.getElementById('loginForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const btnSubmit = document.querySelector('button[type="submit"]');
    btnSubmit.disabled = true;
    btnSubmit.innerText = "Autenticando...";
    btnSubmit.style.cursor = "wait";
    
    if (window.pywebview && window.pywebview.api) {
        window.pywebview.api.process_login();
    } else {
        alert("Erro crítico: Sem comunicação com o processo nativo.");
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
