// Auto-remove flash após 5s
document.querySelectorAll('.flash').forEach(el => {
  setTimeout(() => el.remove(), 5000);
});

// Confirm antes de actions destrutivas
document.querySelectorAll('[data-confirm]').forEach(btn => {
  btn.addEventListener('click', e => {
    if (!confirm(btn.dataset.confirm)) e.preventDefault();
  });
});

// Avatar initials gerador
document.querySelectorAll('[data-initials]').forEach(el => {
  const name = el.dataset.initials || '??';
  el.textContent = name.split(' ').map(w => w[0]).join('').substring(0, 2).toUpperCase();
  const colors = [
    'linear-gradient(135deg,#00b4d8,#0077b6)',
    'linear-gradient(135deg,#c77dff,#7b2d8b)',
    'linear-gradient(135deg,#74c69d,#1b4332)',
    'linear-gradient(135deg,#f4a261,#e76f51)',
    'linear-gradient(135deg,#ff6b6b,#c0392b)',
  ];
  const idx = name.charCodeAt(0) % colors.length;
  el.style.background = colors[idx];
});

// Banner color gerador
document.querySelectorAll('[data-banner]').forEach(el => {
  const banners = [
    'linear-gradient(135deg,#001a2e,#003a5c)',
    'linear-gradient(135deg,#1a0020,#3c0050)',
    'linear-gradient(135deg,#001a10,#003020)',
    'linear-gradient(135deg,#1a1000,#3c2800)',
    'linear-gradient(135deg,#1a0010,#3c0028)',
  ];
  const name = el.dataset.banner || '';
  const idx = (name.charCodeAt(0) || 0) % banners.length;
  el.style.background = banners[idx];
});
