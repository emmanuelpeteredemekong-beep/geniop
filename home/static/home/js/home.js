const fileInput = document.getElementById('csvFile');
const errorBox = document.getElementById('errorBox');
const profitBox = document.getElementById('profitBox');

fileInput?.addEventListener('change', (e) => {
  const file = e.target.files?.[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = (ev) => {
    const text = ev.target.result;
    const rows = text.split('\n').slice(1);
    let bad = [];
    let profit = 0;
    rows.forEach((line, i) => {
      const parts = line.split(',');
      const qty = parseFloat(parts[1]);
      const price = parseFloat(parts[2]);
      if (!parts[0] || isNaN(qty) || isNaN(price)) {
        bad.push(`Row ${i+2}: ${line}`);
      } else {
        profit += qty * price;
      }
    });
    if (bad.length > 0) {
      errorBox.style.display = 'block';
      errorBox.style.background = '#ff4444';
      errorBox.style.color = 'white';
      errorBox.style.padding = '15px';
      errorBox.style.borderRadius = '8px';
      errorBox.innerHTML = `<h4>${bad.length} Wrong Rows:</h4>` + bad.join('<br>');
    } else {
      errorBox.style.display = 'none';
    }
    if (profitBox) profitBox.innerHTML = `<h3>Profit: ₦${profit.toFixed(2)}</h3>`;
  };
  reader.readAsText(file);
});
