function copiarUrl(btn) {
    var input = btn.parentElement.querySelector('input[type="text"]');
    if (input) {
        input.select();
        input.setSelectionRange(0, 99999);
        document.execCommand('copy');
        btn.textContent = 'Copiado!';
        btn.style.background = '#28a745';
        setTimeout(function(){
            btn.textContent = 'Copiar URL';
            btn.style.background = '';
        }, 1200);
    }
}
