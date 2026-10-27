from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Post, SalesReport, get_price
import csv
from openpyxl import load_workbook
import re
from io import TextIOWrapper

def clean_data(rows):
    issues = []
    initial = len(rows)
    
    # 1. Normalize columns + remove empty rows
    normalized = []
    for idx, r in enumerate(rows, start=2):
        if not r:
            continue
        new_r = {}
        for k, v in r.items():
            if k is None:
                continue
            key = str(k).lower().strip().replace(' ', '_')
            if isinstance(v, str):
                v = v.strip()
            new_r[key] = v
        
        if not any(v not in [None, '', ' '] for v in new_r.values()):
            issues.append(f"Row {idx}: Empty row removed")
            continue
        
        new_r['_row_num'] = idx
        normalized.append(new_r)

    # 2. STANDARD amount cleaning - keeps negatives
    cleaned = []
    returns_count = 0
    returns_total = 0.0
    gross_revenue = 0.0
    
    for row in normalized:
        row_num = row.pop('_row_num')
        raw_amount = row.get('amount')

        if raw_amount in [None, '']:
            issues.append(f"Row {row_num}: Missing amount")
            continue

        raw_str = str(raw_amount).strip()
        # Keep minus and dot, remove $ , etc
        cleaned_str = re.sub(r'[^0-9.\-]', '', raw_str)
        
        if cleaned_str in ['', '.', '-', '-.', '.-']:
            issues.append(f"Row {row_num}: Invalid amount '{raw_amount}'")
            continue
        
        try:
            is_negative = cleaned_str.startswith('-')
            cleaned_str = cleaned_str.replace('-', '')
            parts = cleaned_str.split('.')
            if len(parts) > 2:
                cleaned_str = parts[0] + '.' + ''.join(parts[1:])
            
            amt = float(cleaned_str)
            if is_negative:
                amt = -amt
        except:
            issues.append(f"Row {row_num}: Could not parse amount '{raw_amount}'")
            continue

        # DO NOT put 0 for negative - keep it
        if amt < 0:
            returns_count += 1
            returns_total += amt
            issues.append(f"Row {row_num}: Return/Refund detected: {amt}")

        gross_revenue += amt
        row['amount'] = amt
        cleaned.append(row)

    return cleaned, issues, initial, returns_count, returns_total, gross_revenue

@login_required
def home_view(request):
    reports = SalesReport.objects.filter(user=request.user).order_by('-created_at')
    
    if request.method == 'POST' and request.FILES.get('file'):
        uploaded_file = request.FILES['file']
        rows = []

        try:
            if uploaded_file.name.lower().endswith('.csv'):
                file_data = TextIOWrapper(uploaded_file.file, encoding='utf-8')
                reader = csv.DictReader(file_data)
                rows = list(reader)
            else:
                wb = load_workbook(uploaded_file, data_only=True)
                ws = wb.active
                all_rows = list(ws.iter_rows(values_only=True))
                if all_rows:
                    headers = [str(c).lower().strip().replace(' ', '_') if c is not None else '' for c in all_rows[0]]
                    for r in all_rows[1:]:
                        row_dict = {}
                        for i, val in enumerate(r):
                            if i < len(headers) and headers[i]:
                                row_dict[headers[i]] = val
                        rows.append(row_dict)
            
            cleaned, issues, initial, returns_count, returns_total, gross_revenue = clean_data(rows)

        except Exception as e:
            issues = [str(e)]
            cleaned = []
            initial = 0
            returns_count = 0
            returns_total = 0.0
            gross_revenue = 0.0

        context = {
            'reports': reports,
            'cleaned_data': cleaned,
            'issues': issues,
            'initial': initial,
            'returns_count': returns_count,
            'returns_total': returns_total,
            'gross_revenue': gross_revenue,
        }
        return render(request, 'home/index.html', context)

    return render(request, 'home/index.html', {'reports': reports})
