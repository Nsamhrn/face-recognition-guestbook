const video = document.getElementById('video');
const formTamu = document.getElementById('formTamu');
const imageInput = document.getElementById('imageInput');
const messageElement = document.getElementById('message');

let isFaceRecognized = false; // Flag untuk menghentikan deteksi setelah wajah dikenali

// Akses kamera
navigator.mediaDevices.getUserMedia({ video: true })
    .then(stream => {
        video.srcObject = stream;

        // Tunggu hingga video siap, lalu mulai deteksi wajah berkala
        video.addEventListener('loadeddata', () => {
            setInterval(() => {
                if (!isFaceRecognized) {
                    captureAndDetectFace();
                }
            }, 3000); // Deteksi wajah setiap 3 detik jika belum dikenali
        });
    })
    .catch(err => {
        alert('Tidak dapat mengakses kamera: ' + err.message);
    });

// Fungsi untuk mengambil gambar dari kamera dan mengirimkannya ke backend
function captureAndDetectFace() {
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    // Konversi gambar ke Base64
    const imageData = canvas.toDataURL('image/jpeg');
    imageInput.value = imageData; // Masukkan Base64 ke input hidden

    // Kirimkan gambar ke backend untuk deteksi wajah
    fetch('/detect_face', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ image: imageData }),
    })
    .then(response => response.json())
    .then(data => {
        messageElement.style.display = 'block';

        if (data.success) {
            // Jika wajah dikenali, isi form otomatis dan hentikan deteksi
            document.getElementById('nama').value = data.nama;
            document.getElementById('alamat').value = data.alamat;
            document.getElementById('email').value = data.email;
            document.getElementById('nomor_hp').value = data.nomor_hp;
            document.getElementById('nama_instansi').value = data.nama_instansi;

            messageElement.textContent = 'Wajah dikenali! Form telah diisi.';
            messageElement.className = 'message-box message-success';

            isFaceRecognized = true; // Hentikan deteksi setelah wajah dikenali
        } else {
            messageElement.textContent = 'Wajah tidak dikenali.';
            messageElement.className = 'message-box message-error';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        messageElement.textContent = 'Terjadi kesalahan saat mendeteksi wajah.';
        messageElement.className = 'message-box message-error';
    });
}

// Tangkap gambar sebelum form dikirim
formTamu.addEventListener('submit', (e) => {
    e.preventDefault(); // Mencegah submit otomatis sementara

    let isValid = true;
    const inputs = formTamu.querySelectorAll('input[required], textarea[required]');

    // Reset pesan error
    document.getElementById('flashMessage').innerHTML = '';

    // Cek apakah semua field wajib sudah diisi
    inputs.forEach(input => {
        if (!input.value.trim()) {
            isValid = false;
            input.classList.add('is-invalid'); // Tambahkan efek merah
        } else {
            input.classList.remove('is-invalid');
        }
    });

    if (!isValid) {
        document.getElementById('flashMessage').innerHTML =
            `<div class="alert alert-danger">Harap isi semua field yang wajib!</div>`;
        return; // Cegah submit jika ada field kosong
    }

    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    const imageData = canvas.toDataURL('image/jpeg');
    imageInput.value = imageData; // Masukkan Base64 ke input hidden

    if (!imageInput.value) {
        alert('Gagal mengambil gambar! Pastikan kamera berfungsi.');
        return;
    }

    formTamu.submit();
});

// Validasi Form Bootstrap
(function () {
    'use strict';
    const forms = document.querySelectorAll('.needs-validation');

    Array.from(forms).forEach(function (form) {
        form.addEventListener('submit', function (event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });

    // Sembunyikan flash message ketika mulai mengetik
    const inputs = document.querySelectorAll('input, textarea, select');
    inputs.forEach(input => {
        input.addEventListener('input', () => {
            const flashMessage = document.querySelector('.alert');
            if (flashMessage) {
                flashMessage.remove();
            }
        });
    });
})();