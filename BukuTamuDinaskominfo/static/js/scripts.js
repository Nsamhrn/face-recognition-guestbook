// Select all flash messages
const flashMessages = document.querySelectorAll('.alert');
flashMessages.forEach(flash => {
    // Set timeout to hide after 3 seconds (3000ms)
    setTimeout(() => {
        flash.classList.add('fade'); // Add fade-out effect
        setTimeout(() => flash.remove(), 500); // Remove from DOM after fade effect
    }, 3000);
});
// Bagian Delete Button
const deleteButtons = document.querySelectorAll('.delete-button');
const confirmDeleteButton = document.getElementById('confirmDeleteButton');

deleteButtons.forEach(button => {
    button.addEventListener('click', function (e) {
        e.preventDefault();
        const tamuId = this.getAttribute('data-id');
        confirmDeleteButton.setAttribute('data-id', tamuId);

        // Tampilkan modal
        const modal = new bootstrap.Modal(document.getElementById('confirmDeleteModal'));
        modal.show();
    });
});

confirmDeleteButton.addEventListener('click', function (e) {
    e.preventDefault();
    const tamuId = this.getAttribute('data-id');
    const deleteUrl = `/delete/${tamuId}`;

    fetch(deleteUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
    })
    .then(response => {
        if (response.ok) {
            alert('Data berhasil dihapus!');
            location.reload(); // Reload halaman setelah penghapusan berhasil
        } else {
            alert('Gagal menghapus data.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
});


// Bagian Filter Otomatis
const filterForm = document.getElementById('filterForm');
if (filterForm) {
    filterForm.addEventListener('submit', function (e) {

        const fullDate = document.getElementById('full_date');
        const yearMonth = document.getElementById('year_month');
        const year = document.getElementById('year');
        
        // Kosongkan input lain jika salah satu diisi
        if (fullDate && fullDate.value) {
            if (yearMonth) yearMonth.value = '';
            if (year) year.value = '';
        } else if (yearMonth && yearMonth.value) {
            if (fullDate) fullDate.value = '';
            if (year) year.value = '';
        } else if (year && year.value) {
            if (fullDate) fullDate.value = '';
            if (yearMonth) yearMonth.value = '';
        }
    });
}

// Fungsi untuk memuat gambar sebagai base64
async function loadImage(src) {
    try {
        const response = await fetch(src, { cache: "reload" });
        if (!response.ok) throw new Error("Gagal mengambil gambar");
        
        const blob = await response.blob();
        const reader = new FileReader();

        return new Promise((resolve, reject) => {
            reader.onloadend = () => resolve(reader.result);
            reader.onerror = reject;
            reader.readAsDataURL(blob);
        });
    } catch (error) {
        console.error("Error loading image:", error);
        throw new Error("Gagal memuat gambar");
    }
}

// Event listener tombol Download PDF
document.getElementById('downloadPdf').addEventListener('click', async () => {
    const button = document.getElementById('downloadPdf');
    button.disabled = true;
    button.innerText = "Mendownload...";

    try {
        const { jsPDF } = window.jspdf;
        const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });

        // Ambil filter_title dari tombol
        const filterTitle = button.getAttribute('data-filter-title') || "Semua Data";

        // Load gambar logo
        const logoPath = 'static/images/Logo.png';
        const imageData = await loadImage(logoPath);
        doc.addImage(imageData, 'PNG', 15, 10, 20, 20);

        // Ukuran halaman PDF
        const pageWidth = doc.internal.pageSize.getWidth(); // Ambil lebar halaman
        const centerX = pageWidth / 2; // Posisi tengah halaman

        // Kop surat
        doc.setFont('times', 'bold');
        doc.setFontSize(12);
        doc.text('PEMERINTAH DAERAH KABUPATEN KUNINGAN', centerX, 15, {align: "center"});
        doc.setFontSize(14);
        doc.text('DINAS KOMUNIKASI DAN INFORMATIKA', centerX, 20, {align: "center"});
        doc.setFont('times', 'normal');
        doc.setFontSize(10);
        doc.text('Jalan Aruji Kartawinata No.15 Telp.(0232)871142 Fax.(0232)871142', centerX, 25, {align: "center"});
        doc.text('KUNINGAN', centerX, 30, {align: "center"});

        doc.setLineWidth(0.5);
        doc.line(10, 40, 200, 40);

        doc.setFont('times', 'bold');
        doc.setFontSize(14);
        doc.text('Laporan Pencatatan Tamu ', centerX, 50, {align: "center"});
        doc.text(filterTitle, centerX, 55, { align: "center" });
       

        // Ambil elemen tabel
        const table = document.querySelector('.table');
        if (!table) throw new Error("Tabel tidak ditemukan");

        // Ambil header tabel tanpa kolom "Aksi"
        const headers = Array.from(table.querySelectorAll('thead tr th'))
            .filter((_, index) => index !== 6) 
            .map(th => th.innerText);

        // Ambil data baris tanpa kolom "Aksi"
        const body = Array.from(table.querySelectorAll('tbody tr')).map(tr =>
            Array.from(tr.querySelectorAll('td'))
                .filter((_, index) => index !== 6) 
                .map(td => td.innerText)
        );

        // Konversi tabel ke PDF
        doc.autoTable({
            head: [headers],
            body: body,
            theme: 'striped',
            startY: 60,
            styles: { fontSize: 10 },
            headStyles: { fillColor: [40, 44, 52], textColor: [255, 255, 255], fontSize: 10 },
            columnStyles: {
                0: { cellWidth: 10 },
                1: { cellWidth: 35 },
                2: { cellWidth: 45 },
                3: { cellWidth: 25 },
                4: { cellWidth: 15 },
                5: { cellWidth: 45 },  
            },
        });

        // Simpan PDF
        // doc.save('DaftarTamu.pdf');
        doc.save(`DaftarTamu_${filterTitle.replace(/\s+/g, "_")}.pdf`);

    } catch (error) {
        alert(error.message);
    } finally {
        button.disabled = false;
        button.innerText = "Download PDF";
    }
});



// Fungsi Download Excel
document.getElementById('downloadExcel').addEventListener('click', () => {
    const table = document.querySelector('.table');

    // Konversi tabel HTML ke format sheetJS
    const worksheet = XLSX.utils.table_to_sheet(table);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, 'Daftar Tamu');

    // Unduh Excel
    XLSX.writeFile(workbook, 'DaftarTamu.xlsx');
});

// control jumlah baris
document.getElementById('rowsPerPage').addEventListener('change', function () {
    const rows = document.querySelectorAll('.table tbody tr');
    const value = this.value;

    rows.forEach((row, index) => {
        if (value === 'all') {
            // Tampilkan semua baris
            row.style.display = '';
        } else {
            // Tampilkan sesuai jumlah baris yang dipilih
            row.style.display = index < value ? '' : 'none';
        }
    });
});

// Inisialisasi dengan nilai default (misalnya 5 baris)
document.getElementById('rowsPerPage').dispatchEvent(new Event('change'));

// pagination
const rowsPerPageSelect = document.getElementById('rowsPerPage');
const paginationDiv = document.getElementById('pagination');
const rows = document.querySelectorAll('.table tbody tr');

function paginate(rows, rowsPerPage, page) {
    rows.forEach((row, index) => {
        const start = (page - 1) * rowsPerPage;
        const end = start + rowsPerPage;
        row.style.display = index >= start && index < end ? '' : 'none';
    });
}

function setupPagination(rows, rowsPerPage) {
    paginationDiv.innerHTML = '';
    const pageCount = Math.ceil(rows.length / rowsPerPage);

    // Generate tombol pagination
    for (let i = 1; i <= pageCount; i++) {
        const button = document.createElement('button');
        button.textContent = i;
        button.className = 'btn btn-primary btn-sm me-1';
        button.addEventListener('click', () => {
            paginate(rows, rowsPerPage, i);
            document.querySelectorAll('#pagination button').forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
        });
        paginationDiv.appendChild(button);
    }

    // Set halaman pertama sebagai default
    if (pageCount > 0) {
        paginationDiv.querySelector('button').click();
    }
}

rowsPerPageSelect.addEventListener('change', function () {
    const value = this.value === 'all' ? rows.length : parseInt(this.value, 10);
    if (this.value === 'all') {
        paginationDiv.innerHTML = ''; // Hapus pagination jika "Semua" dipilih
        rows.forEach(row => row.style.display = '');
    } else {
        setupPagination(rows, value);
    }
});

// Inisialisasi
rowsPerPageSelect.dispatchEvent(new Event('change'));