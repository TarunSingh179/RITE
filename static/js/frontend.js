// static/js/frontend.js
// JS for frontend animations, dark theme toggle, and interactive elements

document.addEventListener('DOMContentLoaded', function() {
    // Initialize animations
    initEntranceAnimations();
    
    // Initialize dark theme toggle
    initDarkThemeToggle();
    
    // Initialize ripple effects
    initRippleEffects();
    
    // Initialize hero icon animation
    initHeroIconAnimation();

    // Initialize global search
    initGlobalSearch();

    // Initialize notifications
    initNotifications();
});

// Initialize entrance animations with staggered delays
function initEntranceAnimations() {
    const animatedSections = document.querySelectorAll('.fade-in-up');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    });
    
    animatedSections.forEach(section => {
        section.style.opacity = '0';
        section.style.transform = 'translateY(30px)';
        section.style.transition = 'opacity 0.8s ease, transform 0.8s ease';
        observer.observe(section);
    });
    
    // Staggered animations for cards
    const staggeredCards = document.querySelectorAll('.staggered-animation');
    staggeredCards.forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
    });
    
    const staggeredObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const parent = entry.target.closest('section');
                if (parent) {
                    const cards = parent.querySelectorAll('.staggered-animation');
                    cards.forEach((card, index) => {
                        setTimeout(() => {
                            card.style.opacity = '1';
                            card.style.transform = 'translateY(0)';
                        }, index * 100);
                    });
                }
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '0px 0px -100px 0px'
    });
    
    // Observe sections containing staggered cards
    document.querySelectorAll('section').forEach(section => {
        staggeredObserver.observe(section);
    });
}

// Initialize dark theme toggle button
function initDarkThemeToggle() {
    // Create theme toggle button
    const toggleBtn = document.createElement('button');
    toggleBtn.innerHTML = '<i class="fas fa-moon"></i>';
    toggleBtn.className = 'theme-toggle';
    toggleBtn.id = 'themeToggle';
    document.body.appendChild(toggleBtn);
    
    // Check for saved theme preference
    const savedTheme = localStorage.getItem('theme');
    const prefersDarkScheme = window.matchMedia('(prefers-color-scheme: dark)');
    
    if (savedTheme === 'dark' || (!savedTheme && prefersDarkScheme.matches)) {
        document.body.classList.add('dark-mode');
        toggleBtn.innerHTML = '<i class="fas fa-sun"></i>';
    }
    
    // Toggle theme on button click
    toggleBtn.addEventListener('click', function() {
        document.body.classList.toggle('dark-mode');
        
        if (document.body.classList.contains('dark-mode')) {
            localStorage.setItem('theme', 'dark');
            this.innerHTML = '<i class="fas fa-sun"></i>';
        } else {
            localStorage.setItem('theme', 'light');
            this.innerHTML = '<i class="fas fa-moon"></i>';
        }
    });
}

// Initialize ripple effects on buttons
function initRippleEffects() {
    document.querySelectorAll('.ripple').forEach(button => {
        button.addEventListener('click', function(e) {
            // Remove any existing ripple elements
            const existingRipple = this.querySelector('.ripple-effect');
            if (existingRipple) {
                existingRipple.remove();
            }
            
            // Create ripple element
            const ripple = document.createElement('span');
            ripple.classList.add('ripple-effect');
            
            // Add ripple element to button
            this.appendChild(ripple);
            
            // Get position and size
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;
            
            // Set ripple styles
            ripple.style.width = ripple.style.height = size + 'px';
            ripple.style.left = x + 'px';
            ripple.style.top = y + 'px';
            
            // Remove ripple after animation completes
            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    });
}

// Animate hero icon
function initHeroIconAnimation() {
    const heroIcon = document.querySelector('.hero-icon');
    if (heroIcon) {
        // Add floating animation
        heroIcon.style.transition = 'transform 3s ease-in-out';
        setInterval(() => {
            heroIcon.style.transform = 'translateY(0px)';
            setTimeout(() => {
                heroIcon.style.transform = 'translateY(-10px)';
            }, 1500);
        }, 3000);
    }
}

// Global search modal logic
function initGlobalSearch() {
    const modalEl = document.getElementById('globalSearchModal');
    const inputEl = document.getElementById('globalSearchInput');
    const resultsEl = document.getElementById('globalSearchResults');
    if (!modalEl || !inputEl || !resultsEl) return;

    // Open with Ctrl/Cmd+K
    window.addEventListener('keydown', function(e) {
        const isMac = navigator.platform.toUpperCase().indexOf('MAC')>=0;
        const cmdOrCtrl = isMac ? e.metaKey : e.ctrlKey;
        if (cmdOrCtrl && e.key.toLowerCase() === 'k') {
            e.preventDefault();
            const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
            modal.show();
            setTimeout(() => inputEl.focus(), 200);
        }
    });

    // Focus input when modal shown
    modalEl.addEventListener('shown.bs.modal', () => {
        inputEl.focus();
        inputEl.select();
    });

    // Debounced search
    let debounceTimer = null;
    inputEl.addEventListener('input', function() {
        const q = this.value.trim();
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            if (!q) {
                resultsEl.innerHTML = '<p class="text-muted mb-0">Start typing to search. Use Ctrl/Cmd+K anytime.</p>';
                return;
            }
            resultsEl.innerHTML = '<div class="text-muted">Searching...</div>';
            fetch(`/search?q=${encodeURIComponent(q)}&limit=5`, { headers: { 'Accept': 'application/json' }})
                .then(r => r.ok ? r.json() : Promise.reject())
                .then(data => renderSearchResults(data, resultsEl))
                .catch(() => {
                    resultsEl.innerHTML = '<div class="text-danger">Search failed. Please try again.</div>';
                });
        }, 250);
    });
}

function renderSearchResults(data, container) {
    const sections = [];
    const mkSection = (title, items, renderItem) => {
        if (!items || items.length === 0) return '';
        const list = items.map(renderItem).join('');
        return `
            <div class="mb-3">
                <h6 class="text-uppercase text-muted mb-2">${title}</h6>
                <ul class="list-group">
                    ${list}
                </ul>
            </div>`;
    };

    sections.push(mkSection('Users', data.users, u => `
        <li class="list-group-item d-flex justify-content-between align-items-center">
            <div>
                <strong>${escapeHtml(u.name || '')}</strong>
                <div class="small text-muted">${escapeHtml(u.email || '')} • ${escapeHtml(u.role || '')}</div>
            </div>
        </li>`));

    sections.push(mkSection('Courses', data.courses, c => `
        <li class="list-group-item">${escapeHtml(c.name || '')}</li>`));

    sections.push(mkSection('Subjects', data.subjects, s => `
        <li class="list-group-item">${escapeHtml(s.name || '')}</li>`));

    sections.push(mkSection('Books', data.books, b => `
        <li class="list-group-item d-flex justify-content-between align-items-center">
            <span>${escapeHtml(b.title || '')}</span>
            <span class="badge bg-secondary">${escapeHtml(b.author || '')}</span>
        </li>`));

    const html = sections.filter(Boolean).join('');
    container.innerHTML = html || '<p class="text-muted mb-0">No results found.</p>';
}

function escapeHtml(str) {
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

// Notifications logic
function initNotifications() {
    const badge = document.getElementById('notificationsBadge');
    const listEl = document.getElementById('notificationsList');
    const btnMarkAll = document.getElementById('markAllNotificationsRead');
    const modalEl = document.getElementById('notificationsModal');
    if (!badge || !listEl || !modalEl) return;

    // Poll unread count every 30s
    function refreshUnread() {
        fetch('/api/notifications/unread_count', { headers: { 'Accept': 'application/json' }})
            .then(r => r.ok ? r.json() : Promise.reject())
            .then(({ unread }) => {
                if (unread > 0) {
                    badge.textContent = unread;
                    badge.classList.remove('d-none');
                } else {
                    badge.classList.add('d-none');
                }
            })
            .catch(() => {});
    }
    refreshUnread();
    setInterval(refreshUnread, 30000);

    // Load list when modal opens
    modalEl.addEventListener('show.bs.modal', () => {
        listEl.innerHTML = '<p class="text-muted mb-0">Loading notifications...</p>';
        fetch('/api/notifications?limit=50', { headers: { 'Accept': 'application/json' }})
            .then(r => r.ok ? r.json() : Promise.reject())
            .then(data => {
                renderNotificationsList(data.items || [], listEl);
            })
            .catch(() => {
                listEl.innerHTML = '<div class="text-danger">Failed to load notifications.</div>';
            });
    });

    // Mark all as read
    if (btnMarkAll) {
        btnMarkAll.addEventListener('click', () => {
            fetch('/api/notifications/mark_all_read', { method: 'POST', headers: { 'Content-Type': 'application/json' }})
                .then(r => r.ok ? r.json() : Promise.reject())
                .then(() => {
                    refreshUnread();
                    // update list checkmarks
                    listEl.querySelectorAll('[data-notif-item]').forEach(li => li.classList.add('opacity-75'));
                });
        });
    }
}

function renderNotificationsList(items, container) {
    if (!items.length) {
        container.innerHTML = '<p class="text-muted mb-0">No notifications.</p>';
        return;
    }
    const html = items.map(n => `
        <div class="list-group" data-notif-item>
            <div class="list-group-item d-flex justify-content-between align-items-start ${n.is_read ? 'opacity-75' : ''}">
                <div class="ms-2 me-auto">
                    <div class="fw-bold">${escapeHtml(n.title || '')}</div>
                    <div class="small text-muted">${escapeHtml(n.type || '')} • ${escapeHtml(n.priority || '')} • ${formatDate(n.created_at)}</div>
                    <div class="mt-1">${escapeHtml(n.message || '')}</div>
                </div>
                ${n.is_read ? '' : '<button class="btn btn-sm btn-outline-primary" data-mark-read="'+n.id+'">Mark read</button>'}
            </div>
        </div>
    `).join('');
    container.innerHTML = html;
    container.querySelectorAll('[data-mark-read]').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const id = e.currentTarget.getAttribute('data-mark-read');
            fetch('/api/notifications/mark_read', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id }) })
                .then(r => r.ok ? r.json() : Promise.reject())
                .then(() => {
                    // Refresh the list quickly
                    fetch('/api/notifications?limit=50')
                        .then(r => r.ok ? r.json() : Promise.reject())
                        .then(data => renderNotificationsList(data.items || [], container));
                    // Update badge
                    fetch('/api/notifications/unread_count')
                        .then(r => r.ok ? r.json() : Promise.reject())
                        .then(({ unread }) => {
                            const badge = document.getElementById('notificationsBadge');
                            if (badge) {
                                if (unread > 0) { badge.textContent = unread; badge.classList.remove('d-none'); }
                                else { badge.classList.add('d-none'); }
                            }
                        });
                });
        });
    });
}

function formatDate(iso) {
    if (!iso) return '';
    try {
        const d = new Date(iso);
        return d.toLocaleString();
    } catch { return ''; }
}
