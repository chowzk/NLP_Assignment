// Theme toggle
document.getElementById('toggle-theme').addEventListener('click', function() {
    const body = document.body;
    const sidebar = document.getElementById('sidebar');
    const chatItems = document.querySelectorAll('.list-group-item');
    const toggleButton = this;
    const searchInput = document.querySelector('.form-control');
    const searchIcon = document.querySelector('.input-group-text');
    const dropdownButtons = document.querySelectorAll('.dropdown-toggle');
    const dropdownMenus = document.querySelectorAll('.dropdown-menu');

    if (body.classList.contains('dark-theme')) {
        body.classList.replace('dark-theme', 'light-theme');
        sidebar.classList.replace('dark-theme', 'light-theme');
        chatItems.forEach(item => item.classList.replace('dark-theme', 'light-theme'));
        toggleButton.classList.replace('btn-outline-light', 'btn-outline-dark');
        toggleButton.textContent = '🌞';
        searchInput.classList.remove('bg-dark', 'text-white');
        searchIcon.classList.remove('bg-dark', 'text-white');
        dropdownButtons.forEach(btn => btn.classList.replace('btn-dark', 'btn-light'));
        dropdownMenus.forEach(menu => {
            menu.classList.replace('dropdown-menu-dark', 'dropdown-menu-light');
            menu.style.backgroundColor = '#ffffff';
            menu.querySelectorAll('.dropdown-item').forEach(item => {
                item.style.color = 'black';
                item.addEventListener('mouseover', () => item.style.backgroundColor = '#e9ecef');
                item.addEventListener('mouseout', () => item.style.backgroundColor = '');
            });
        });
    } else {
        body.classList.replace('light-theme', 'dark-theme');
        sidebar.classList.replace('light-theme', 'dark-theme');
        chatItems.forEach(item => item.classList.replace('light-theme', 'dark-theme'));
        toggleButton.classList.replace('btn-outline-dark', 'btn-outline-light');
        toggleButton.textContent = '🌙';
        searchInput.classList.add('bg-dark', 'text-white');
        searchIcon.classList.add('bg-dark', 'text-white');
        dropdownButtons.forEach(btn => btn.classList.replace('btn-light', 'btn-dark'));
        dropdownMenus.forEach(menu => {
            menu.classList.replace('dropdown-menu-light', 'dropdown-menu-dark');
            menu.style.backgroundColor = '#343a40';
            menu.querySelectorAll('.dropdown-item').forEach(item => {
                item.style.color = 'white';
                item.addEventListener('mouseover', () => item.style.backgroundColor = '#495057');
                item.addEventListener('mouseout', () => item.style.backgroundColor = '');
            });
        });
    }
});
