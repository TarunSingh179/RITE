// static/js/admin.js
// JS for admin event/fee forms, search/filter, and pagination

document.addEventListener('DOMContentLoaded', function() {
    // Show/hide event form
    var eventBtn = document.getElementById('showEventForm');
    var eventForm = document.getElementById('eventForm');
    if (eventBtn && eventForm) {
        eventBtn.onclick = function() {
            eventForm.style.display = 'block';
        };
    }

    // Show/hide fee form
    var feeBtn = document.getElementById('showFeeForm');
    var feeForm = document.getElementById('feeForm');
    if (feeBtn && feeForm) {
        feeBtn.onclick = function() {
            feeForm.style.display = 'block';
        };
    }

    // Simple validation
    document.querySelectorAll('form').forEach(function(form) {
        form.onsubmit = function(e) {
            var valid = true;
            form.querySelectorAll('input[required], textarea[required]').forEach(function(input) {
                if (!input.value.trim()) {
                    valid = false;
                    input.classList.add('is-invalid');
                } else {
                    input.classList.remove('is-invalid');
                }
            });
            if (!valid) {
                e.preventDefault();
                alert('Please fill all required fields.');
            }
        };
    });

    // Search/filter logic for tables
    document.querySelectorAll('.search-input').forEach(function(input) {
        input.addEventListener('input', function() {
            var value = input.value.toLowerCase();
            var table = document.querySelector(input.dataset.target);
            if (table) {
                table.querySelectorAll('tbody tr').forEach(function(row) {
                    var text = row.textContent.toLowerCase();
                    row.style.display = text.includes(value) ? '' : 'none';
                });
            }
        });
    });

    // Simple pagination logic for tables
    document.querySelectorAll('.paginated-table').forEach(function(table) {
        var rows = Array.from(table.querySelectorAll('tbody tr'));
        var pageSize = 10;
        var currentPage = 1;
        var pager = document.createElement('div');
        pager.className = 'pagination-controls';
        table.parentNode.insertBefore(pager, table.nextSibling);

        function renderPage(page) {
            var start = (page - 1) * pageSize;
            var end = start + pageSize;
            rows.forEach(function(row, i) {
                row.style.display = (i >= start && i < end) ? '' : 'none';
            });
            pager.innerHTML = '';
            for (var p = 1; p <= Math.ceil(rows.length / pageSize); p++) {
                var btn = document.createElement('button');
                btn.textContent = p;
                btn.className = 'btn btn-sm ' + (p === page ? 'btn-primary' : 'btn-outline-primary');
                btn.onclick = (function(p) { return function() { renderPage(p); }; })(p);
                pager.appendChild(btn);
            }
        }
        renderPage(currentPage);
    });
});
