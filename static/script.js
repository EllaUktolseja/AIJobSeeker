document.addEventListener('DOMContentLoaded', () => {
    const skillsInput = document.getElementById('skills');
    const submitBtn = document.getElementById('submitBtn');
    const clearBtn = document.getElementById('clearBtn');
    const resultsSection = document.getElementById('resultsSection');
    const resultsContainer = document.getElementById('results');
    const resultsCount = document.getElementById('resultsCount');
    const emptyState = document.getElementById('emptyState');

    // 1. Fungsi klik tombol contoh cepat (chips)
    document.querySelectorAll('.chip').forEach(chip => {
        chip.addEventListener('click', () => {
            skillsInput.value = chip.getAttribute('data-example');
        });
    });

    // 2. Fungsi Tombol Bersihkan
    clearBtn.addEventListener('click', () => {
        skillsInput.value = '';
        resultsSection.classList.add('hidden');
        emptyState.classList.remove('hidden');
    });

    // 3. Fungsi Utama Pencarian Rekomendasi (Saat Tombol Diklik)
    submitBtn.addEventListener('click', async () => {
        const skillsText = skillsInput.value.trim();

        if (!skillsText) {
            alert('Mohon tuliskan deskripsi keahlianmu terlebih dahulu!');
            return;
        }

        // Tampilan Mode Loading
        submitBtn.disabled = true;
        submitBtn.innerHTML = '⚡ Sedang dihitung AI...';
        resultsContainer.innerHTML = '';

        try {
            // Mengirim request ke endpoint API Flask
            const response = await fetch('/api/rekomendasi', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_skills: skillsText })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Gagal merespon API');
            }

            const jobs = await response.json();

            // Sembunyikan empty state dan munculkan section hasil
            emptyState.classList.add('hidden');
            resultsSection.classList.remove('hidden');
            resultsCount.textContent = `(${jobs.length} Pekerjaan Ditemukan)`;

            // Render Job Cards ke HTML
            jobs.forEach(job => {
                const card = document.createElement('div');
                card.className = 'job-card'; // Memakai class dari style.css Anda
                card.innerHTML = `
                    <div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 15px; border-left: 5px solid #28a745; position: relative;">
                        <span style="position: absolute; top: 20px; right: 20px; background: #e2f0d9; color: #385723; padding: 4px 12px; border-radius: 20px; font-weight: bold; font-size: 13px;">
                            ${job.match_score} Match
                        </span>
                        <h3 style="margin: 0 0 8px 0; color: #333; font-size: 18px; padding-right: 90px;">${job.job_title}</h3>
                        <p style="margin: 0 0 12px 0; font-size: 14px; color: #666;">
                            🏢 <b>${job.company}</b> &nbsp;•&nbsp; 📍 <i>${job.location}</i>
                        </p>
                        <div style="font-size: 13px; color: #555; background: #f8f9fa; padding: 12px; border-radius: 6px; line-height: 1.4;">
                            <strong style="color: #444;">Skills Needed:</strong> ${job.skills_required}
                        </div>
                    </div>
                `;
                resultsContainer.appendChild(card);
            });

        } catch (error) {
            // Menampilkan error asli di console log F12 untuk inspect element
            console.error('Detail Error Aplikasi:', error);
            alert(`Terjadi kesalahan koneksi ke server AI.\nPesan: ${error.message}`);
            emptyState.classList.remove('hidden');
            resultsSection.classList.add('hidden');
        } finally {
            // Kembalikan tombol ke keadaan semula
            submitBtn.disabled = false;
            submitBtn.innerHTML = '🚀 Rekomendasikan Pekerjaan';
        }
    });
});
