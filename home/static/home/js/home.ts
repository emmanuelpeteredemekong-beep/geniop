const fileInput = document.getElementById('csvFile') as HTMLInputElement;
const errorBox = document.getElementById('errorBox') as HTMLDivElement;

fileInput?.addEventListener('change', (e) => {
  const file = (e.target as HTMLInputElement).files?.[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = (ev) => {
    const text = ev.target?.result as string;
    const rows = text.split('\n').slice(1);
    let bad: string[] = [];
    rows.forEach((line, i) => {
      const parts = line.split(',');
      if (parts.length < 3 || !parts[0]) bad.push(`Row ${i+2} wrong`);
    });
    if (bad.length > 0) {
      errorBox.style.display = 'block';
      errorBox.innerHTML = bad.join('<br>');
    } else {
      errorBox.style.display = 'none';
    }
  };
  reader.readAsText(file);
});
