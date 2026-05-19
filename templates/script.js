// ============================================================
// Konfigurasi API
// Ganti API_URL dengan endpoint back-end (.pkl model) kamu.
// Jika back-end belum siap, set USE_MOCK = true untuk demo lokal.
// ============================================================
const API_URL = "/api/rekomendasi";
const USE_MOCK = true; // ubah ke false saat back-end sudah live

const $ = (sel) => document.querySelector(sel);
const textarea = $("#skills");
const submitBtn = $("#submitBtn");
const clearBtn = $("#clearBtn");
const resultsSection = $("#resultsSection");
const resultsEl = $("#results");
const resultsCount = $("#resultsCount");
const emptyState = $("#emptyState");

// Chip contoh
document.querySelectorAll(".chip").forEach((chip) => {
  chip.addEventListener("click", () => {
    textarea.value = chip.dataset.example;
    textarea.focus();
  });
});

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
    showError("Gagal mengambil rekomendasi. Periksa koneksi back-end.");
  } finally {
    setLoading(false);
  }
}

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
  resultsCount.textContent = `${data.length} pekerjaan ditemukan`;

  resultsEl.innerHTML = data.map(cardHTML).join("");
}

function cardHTML(job) {
  const score = parseFloat(String(job.match_score).replace("%", "")) || 0;
  const matchClass = score >= 85 ? "" : score >= 65 ? "mid" : "low";
  const skills = String(job.skills_required || "")
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);

  return `
    <article class="job-card">
      <div class="job-top">
        <div>
          <h3 class="job-title">${escapeHtml(job.job_title)}</h3>
          <div class="job-company">🏢 ${escapeHtml(job.company)}</div>
          <div class="job-location">📍 ${escapeHtml(job.location)}</div>
        </div>
        <span class="match ${matchClass}">${escapeHtml(job.match_score)} Match</span>
      </div>
      <div class="skills">
        ${skills.map((s) => `<span class="skill-tag">${escapeHtml(s)}</span>`).join("")}
      </div>
    </article>
  `;
}

function escapeHtml(s) {
  return String(s ?? "")
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}

function showError(msg) {
  removeError();
  const div = document.createElement("div");
  div.className = "error";
  div.id = "errBox";
  div.textContent = msg;
  $(".form-card").appendChild(div);
}
function removeError() { const e = $("#errBox"); if (e) e.remove(); }

// ============================================================
// MOCK back-end — meniru response dari model .pkl
// ============================================================
async function mockRecommend(text) {
  await new Promise((r) => setTimeout(r, 900)); // simulasi latency
  const t = text.toLowerCase();

  const pool = [
    { kw: ["python","machine learning","ml","data","scikit","pandas"], job: {
      job_title: "Data Scientist / Machine Learning Engineer",
      company: "Galaxy Data Corp",
      location: "San Francisco, CA (Remote)",
      skills_required: "python, scikit-learn, sql, machine learning, cloud",
      match_score: "95.2%"
    }},
    { kw: ["python","django","backend","api","postgres"], job: {
      job_title: "Python Backend Developer",
      company: "Innovative Software Ltd",
      location: "New York, NY",
      skills_required: "python, django, postgresql, rest api, docker",
      match_score: "87.1%"
    }},
    { kw: ["react","javascript","frontend","html","css","typescript","tailwind"], job: {
      job_title: "Frontend Engineer (React)",
      company: "BrightUI Studio",
      location: "Austin, TX",
      skills_required: "react, typescript, html, css, tailwind",
      match_score: "92.4%"
    }},
    { kw: ["java","spring","kafka","microservices"], job: {
      job_title: "Java Developer",
      company: "IBM",
      location: "Raleigh, NC",
      skills_required: "java, spring boot, microservices, kafka, sql",
      match_score: "89.0%"
    }},
    { kw: ["network","cisco","router","firewall","ccna"], job: {
      job_title: "Network Engineer",
      company: "Cisco",
      location: "San Jose, CA",
      skills_required: "cisco, routing, switching, firewall, tcp/ip",
      match_score: "90.5%"
    }},
    { kw: ["aws","cloud","azure","gcp","devops","kubernetes","docker"], job: {
      job_title: "Cloud / DevOps Engineer",
      company: "Tech Solutions Inc",
      location: "Seattle, WA (Remote)",
      skills_required: "aws, kubernetes, docker, terraform, ci/cd",
      match_score: "88.7%"
    }},
    { kw: ["sql","database","etl","analyst"], job: {
      job_title: "Data Analyst",
      company: "FinCore Analytics",
      location: "Chicago, IL",
      skills_required: "sql, python, tableau, etl, excel",
      match_score: "83.6%"
    }},
    { kw: ["security","cyber","pentest","siem"], job: {
      job_title: "Cybersecurity Analyst",
      company: "SecureNet",
      location: "Washington, DC",
      skills_required: "siem, soc, incident response, network security",
      match_score: "81.2%"
    }},
  ];

  let matched = pool
    .map((p) => {
      const hits = p.kw.filter((k) => t.includes(k)).length;
      return { ...p.job, _hits: hits };
    })
    .filter((j) => j._hits > 0)
    .sort((a, b) => b._hits - a._hits)
    .slice(0, 6);

  // fallback general
  if (matched.length === 0) {
    matched = [{
      job_title: "Junior Software Developer",
      company: "Tech Solutions Inc",
      location: "Remote",
      skills_required: "general programming, problem solving, git",
      match_score: "62.0%"
    }];
  }

  return matched.map(({ _hits, ...rest }) => rest);
}