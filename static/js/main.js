// ===== YBC Tools - Main JavaScript =====
document.addEventListener('DOMContentLoaded', function() {

    // ---- Global Search ----
    const searchInput = document.getElementById('global-search');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const query = this.value.trim().toLowerCase();
            filterTools(query, null);
        });
    }

    // ---- Sidebar Category Filter ----
    const categoryItems = document.querySelectorAll('.category-item');
    categoryItems.forEach(item => {
        item.addEventListener('click', function() {
            // Update active state
            categoryItems.forEach(i => i.classList.remove('active'));
            this.classList.add('active');

            const category = this.dataset.category;
            filterTools(searchInput ? searchInput.value.trim().toLowerCase() : '', category);
        });
    });

    // ---- Sidebar Toggle ----
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebar = document.getElementById('sidebar');
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('collapsed');
            this.textContent = sidebar.classList.contains('collapsed') ? '›' : '‹';
        });
    }

    // ---- Filter Tools ----
    function filterTools(query, category) {
        const cards = document.querySelectorAll('.tool-card');
        const emptyState = document.getElementById('empty-state');
        let visibleCount = 0;

        cards.forEach(card => {
            const name = (card.dataset.name || '').toLowerCase();
            const cardCategory = card.dataset.category || '';

            const matchesSearch = !query || name.includes(query);
            const matchesCategory = !category || category === 'all' || cardCategory === category;

            if (matchesSearch && matchesCategory) {
                card.style.display = '';
                visibleCount++;
            } else {
                card.style.display = 'none';
            }
        });

        if (emptyState) {
            emptyState.style.display = visibleCount === 0 ? '' : 'none';
        }
    }

    // ---- Update page header on category change ----
    categoryItems.forEach(item => {
        item.addEventListener('click', function() {
            const header = document.querySelector('.page-header h1');
            if (header) {
                const catName = this.querySelector('.cat-name');
                header.textContent = catName ? catName.textContent : '全部工具';
            }
        });
    });

});
