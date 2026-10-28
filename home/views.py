from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Post, SalesReport, get_price
import csv
import re
from io import TextIOWrapper

def clean_data(rows):
    issues = []
    initial = len(rows)
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
            # CSV ONLY
            file_data = TextIOWrapper(uploaded_file.file, encoding='utf-8')
            reader = csv.DictReader(file_data)
            rows = list(reader)
            cleaned, issues, initial, returns_count, returns_total, gross_revenue = clean_data(rows)
        except Exception as e:
            issues = [str(e)]
            cleaned = []
            initial = returns_count = 0
            returns_total = gross_revenue = 0.0

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

import csv
import io
from accounts.models import Store
from django.db.models import Q

def parse_csv_file(file):
    # Read CSV like before, keep -50 as return
    text = file.read().decode('utf-8')
    file.seek(0)
    reader = csv.DictReader(io.StringIO(text))
    
    total_sales = 0
    total_returns = 0
    
    for row in reader:
        try:
            # find amount column - check 'amount', 'total', 'price', last column
            amount = None
            for key in ['amount', 'total', 'price', 'Amount', 'TOTAL']:
                if key in row and row[key]:
                    amount = float(row[key])
                    break
            if amount is None:
                # take last value
                last_val = list(row.values())[-1]
                amount = float(last_val)
            
            total_sales += amount
            if amount < 0:  # keeps -50 as return
                total_returns += amount
        except:
            continue
    
    return total_sales, total_returns

def branch_compare(request):
    my_branches = Store.objects.filter(
        Q(owner=request.user) | Q(staff__user=request.user)
    ).distinct()
    
    results = []
    if request.method == 'POST':
        for i in [1,2,3]:
            branch_id = request.POST.get(f'branch{i}_id')
            file = request.FILES.get(f'branch{i}_file')
            if branch_id and file:
                branch = Store.objects.get(id=branch_id)
                sales, returns = parse_csv_file(file)  # only reads, no save
                results.append({
                    'branch_name': branch.name,
                    'sales': sales,
                    'returns': returns
                })

    return render(request, 'home/compare.html', {
        'my_branches': my_branches, 
        'results': results
    })
