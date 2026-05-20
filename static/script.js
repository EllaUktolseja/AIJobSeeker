// ============================================================
// Konfigurasi API
// ============================================================
const API_URL = "/api/rekomendasi";
const USE_MOCK = false; 

const $ = (sel) => document.querySelector(sel);
const textarea = $("#skills");
const submitBtn = $("#submitBtn");
const clearBtn = $("#clearBtn");
const resultsSection = $("#resultsSection");
const resultsEl = $("#results");
const resultsCount = $("#resultsCount");
const emptyState = $("#emptyState");

// Chip contoh cepat
document.querySelectorAll(".chip").forEach((chip) => {
  chip.addEventListener("click", () => {
    textarea.value = chip.dataset.example;
    textarea.focus();
  });
});

// Tombol bersihkan form dan hasil
clearBtn.addEventListener("click", () => {
  textarea.value = "";
  resultsEl.innerHTML = "";
  resultsSection.classList.add("hidden");
  emptyState.classList.remove("hidden");
  textarea.focus();
});

submitBtn.addEventListener("click", handleSubmit);
textarea.addEventListener("keydown", (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key === "Enter") handleSubmit();
});

async function handleSubmit() {
  const user_skills = textarea.value.trim();
  removeError();
  if (!user_skills) {
    showError("Silakan masukkan deskripsi keahlianmu terlebih dahulu.");
    return;
  }

  setLoading(true);
  try {
    const data = USE_MOCK
      ? await mockRecommend(user_skills)
      : await fetchRecommend(user_skills);

    renderResults(data);
  } catch (err) {
    console.error(err);
    showError("Gagal mengambil rekomendasi. Periksa koneksi back-end Flask kamu.");
  } finally {
    setLoading(false);
  }
}

// Mengambil data riil dari route Flask
async function fetchRecommend(user_skills) {
  const res = await fetch(API_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_skills }),
  });
  if (!res.ok) throw new Error("HTTP " + res.status);
  return res.json();
}

function setLoading(loading) {
  submitBtn.disabled = loading;
  submitBtn.querySelector(".btn-text").innerHTML = loading
    ? '<span class="spinner"></span> Menganalisis keahlianmu...'
    : "🚀 Rekomendasikan Pekerjaan";
}

function renderResults(data) {
  if (!Array.isArray(data) || data.length === 0) {
    resultsEl.innerHTML = "";
    resultsSection.classList.add("hidden");
    emptyState.classList.remove("hidden");
    emptyState.querySelector("p").textContent =
      "Tidak ada rekomendasi cocok. Coba tambahkan lebih banyak keahlian.";
    return;
  }

  emptyState.classList.add("hidden");
  resultsSection.classList.remove("hidden");
  resultsCount.textContent = `(${data.length} Pekerjaan Ditemukan)`;

  resultsEl.innerHTML = data.map(cardHTML).join("");
}

// Generator kartu lowongan kerja (Sudah sinkron penuh dengan style.css tema gelap)
function cardHTML(job) {
  const score = parseFloat(String(job.match_score).replace("%", "")) || 0;
  const matchClass = score >= 85 ? "" : score >= 65 ? "mid" : "low";

  // Memecah string skill dari backend ("PYTHON, SQL") menjadi array untuk dijadikan komponen tag bunder
  const skillsArray = job.skills_required ? job.skills_required.split(", ") : [];
  const skillsHTML = skillsArray
    .map((s) => `<span class="skill-tag">${escapeHtml(s)}</span>`)
    .join("");

  return `
    <article class="job-card">
      <div class="job-top">
        <div>
          <h3 class="job-title">${escapeHtml(job.job_title)}</h3>
          <div class="job-company">🏢 ${escapeHtml(job.company)}</div>
          <div class="job-location">📍 ${escapeHtml(job.location)}</div>
        </div>
        <span class="match ${matchClass}">
          ${escapeHtml(job.match_score)} Match
        </span>
      </div>
      <div class="skills" style="margin-top: 12px;">
        ${skillsHTML ? skillsHTML : '<span class="skill-tag">-</span>'}
      </div>
    </article>
  `;
}

// Fungsi pengaman XSS agar teks aneh dari database tidak merusak HTML
function escapeHtml(s) {
  return String(s ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function showError(msg) {
  removeError();
  const div = document.createElement("div");
  div.className = "error";
  div.id = "errBox";
  div.textContent = msg;
  $(".form-card").appendChild(div);
}

function removeError() { 
  const e = $("#errBox"); 
  if (e) e.remove(); 
}

// ============================================================
// MOCK back-end (Hanya berjalan jika USE_MOCK = true)
// ============================================================
async function mockRecommend(text) {
  await new Promise((r) => setTimeout(r, 900));
  return [
    {
      job_title: "Junior Software Developer (Mock)",
      company: "Tech Solutions Inc",
      location: "Remote",
      skills_required: "GENERAL PROGRAMMING, PROBLEM SOLVING, GIT",
      match_score: "75.0%"
    }
  ];
}