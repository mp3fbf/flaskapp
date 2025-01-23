// Função para alternar entre temas
function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    
    // Atualiza o ícone
    updateThemeIcon(newTheme);
}

// Função para atualizar o ícone do tema
function updateThemeIcon(theme) {
    const icon = document.querySelector('.theme-toggle svg');
    if (theme === 'dark') {
        icon.innerHTML = `<path d="M12 3c.132 0 .263 0 .393 0a7.5 7.5 0 0 0 7.92 12.446a9 9 0 1 1 -8.313 -12.454z"/>`;
    } else {
        icon.innerHTML = `<path d="M12 19a7 7 0 1 0 0-14 7 7 0 0 0 0 14z M12 22.5v-1.5 M12 3v-1.5 M18.5 18.5l1 1 M4.5 4.5l1 1 M21 12h1.5 M1.5 12H3 M18.5 5.5l1-1 M4.5 19.5l1-1"/>`;
    }
}

// Função para inicializar o tema
function initTheme() {
    // Verifica se há um tema salvo
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);
}

// Inicializa o tema quando o DOM estiver carregado
document.addEventListener('DOMContentLoaded', initTheme); 