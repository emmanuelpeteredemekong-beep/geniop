// home.ts - Geniop Homepage Frontend
interface SaleRow {
  product: string;
  quantity: number;
  price: number;
  valid: boolean;
  error?: string;
}

const fileInput = document.getElementById('csvFile') as HTMLInputElement;
const errorBox = document.getElementById('errorBox') as HTMLDivElement;
const profitBox = document.getElementById('profitBox') as HTMLDivElement;

fileInput?.addEventListener('change', (e: Event) => {
  const target = e.target as HTMLInputElement;
  const file = target.files?.[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = (ev) => {
    const text = ev.target?.result as string;
    const rows = text.split('\n');
    let invalidRows: SaleRow[] = [];
    let totalProfit = 0;

    rows.slice(1).forEach((line, index) => {
      const [product, qtyStr, priceStr] = line.split(',');
      const quantity = parseFloat(qtyStr);
      const price = parseFloat(priceStr);

      if (!product || isNaN(quantity) || isNaN(price) || quantity < 0) {
        invalidRows.push({
          product: product || `Row ${index+2}`,
          quantity,
          price,
          valid: false,
          error: `Invalid data at line ${index+2}`
        });
      } else {
        totalProfit += quantity * price;
      }
    });

    // Show red calling-out box
    if (invalidRows.length > 0) {
      errorBox.style.display = 'block';
      errorBox.innerHTML = `
        <h4>⚠️ ${invalidRows.length} Wrong Rows Found:</h4>
        <ul>${invalidRows.map(r => `<li>${r.product}: ${r.error}</li>`).join('')}</ul>
      `;
    } else {
      errorBox.style.display = 'none';
    }

    profitBox.innerHTML = `<h3>Estimated Profit: ₦${totalProfit.toFixed(2)}</h3>`;
  };
  reader.readAsText(file);
});

console.log('Geniop TS Frontend Loaded ✓');
