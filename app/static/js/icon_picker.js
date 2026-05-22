document.addEventListener("DOMContentLoaded", function() {
    const customSelects = document.querySelectorAll('select#icon, select#preset-icon, select#preset_id');
    
    customSelects.forEach(select => {
        const isIconPicker = select.id === 'icon' || select.id === 'preset-icon';

        select.style.display = 'none';

        const container = document.createElement('div');
        container.className = 'dropdown w-100 icon-picker-container';
        select.parentNode.insertBefore(container, select.nextSibling);

        const button = document.createElement('button');
        button.className = select.className + ' text-start d-flex align-items-center justify-content-between';
        button.type = 'button';
        button.setAttribute('data-bs-toggle', 'dropdown');
        button.setAttribute('aria-expanded', 'false');

        const menu = document.createElement('ul');
        menu.className = 'dropdown-menu w-100 shadow-sm user-select-none';
        menu.style.maxHeight = '300px';
        menu.style.overflowY = 'auto';
        
        container.appendChild(button);
        container.appendChild(menu);
        
        const updateButton = (val, text) => {
            if (isIconPicker && val) {
                button.innerHTML = `<span class="d-flex align-items-center gap-2"><svg class="bi" width="18" height="18" fill="currentColor"><use href="/static/svg/bootstrap-icons.svg#${val}"></use></svg> ${text}</span>`;
            } else {
                button.innerHTML = `<span>${text}</span>`;
            }
        };

        Array.from(select.options).forEach(option => {
            const li = document.createElement('li');
            const a = document.createElement('a');
            a.className = 'dropdown-item d-flex align-items-center gap-2 user-select-none';
            a.href = '#';
            a.draggable = false;
            a.dataset.value = option.value;
            
            if (isIconPicker && option.value) {
                a.innerHTML = `<svg class="bi" width="18" height="18" fill="currentColor"><use href="/static/svg/bootstrap-icons.svg#${option.value}"></use></svg> ${option.text}`;
            } else {
                a.innerHTML = option.text;
            }
            
            a.addEventListener('click', (e) => {
                e.preventDefault();
                select.value = option.value;
                updateButton(option.value, option.text);
                // Trigger change event for live preview
                select.dispatchEvent(new Event('change'));
            });
            
            a.addEventListener('mousedown', (e) => {
                e.preventDefault();
            });
            
            li.appendChild(a);
            menu.appendChild(li);
        });
        
        // Initial state
        const selectedOption = select.options[select.selectedIndex];
        if (selectedOption) {
            updateButton(selectedOption.value, selectedOption.text);
        }

        select.addEventListener('change', () => {
            const opt = select.options[select.selectedIndex];
            if (opt) {
                updateButton(opt.value, opt.text);
            }
        });
    });
});

