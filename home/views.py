from django.shortcuts import render  # Render templates
from django.contrib.auth.decorators import login_required  # Login required
from .models import Post, QuickSalesReport, get_price  # Post, Report, price helper - matches urls.py need get_price
import csv  # CSV parsing
import re  # Regex for cleaning amounts
import io  # IO for file reading
from io import TextIOWrapper  # Wrapper for uploaded file
from django.db.models import Q  # Q for OR query: owner OR staff
from accounts.models import Store  # Store from accounts: has owner and staff

# Function to clean and validate rows from CSV
def clean_data(rows):
    issues = []  # List to store errors
    initial = len(rows)  # Initial count of rows
    normalized = []  # Cleaned rows
    # Loop through rows with index starting at 2 (header is 1)
    for idx, r in enumerate(rows, start=2):
        if not r:  # If row is empty
            continue  # Skip it
        new_r = {}  # New cleaned row
        # Loop through key, value in row
        for k, v in r.items():
            if k is None:  # If key is None
                continue  # Skip
            key = str(k).lower().strip().replace(' ', '_')  # Normalize key: lower, strip, underscore
            if isinstance(v, str):  # If value is string
                v = v.strip()  # Remove spaces
            new_r[key] = v  # Add to new row
        # Check if row is completely empty
        if not any(v not in [None, '', ' '] for v in new_r.values()):
            issues.append(f"Row {idx}: Empty row")  # Error
            continue  # Skip
        new_r['_row_num'] = idx  # Keep original row number for error tracking
        normalized.append(new_r)  # Add to normalized

    cleaned = []  # Final cleaned list
    returns_count = 0  # Count of returns (negative amounts)
    returns_total = 0.0  # Total of returns
    gross_revenue = 0.0  # Total gross

    # Loop through normalized rows
    for row in normalized:
        row_num = row.pop('_row_num')  # Get row number
        raw_amount = row.get('amount')  # Get amount field
        if raw_amount in [None, '']:  # If amount missing
            issues.append(f"Row {row_num}: Missing amount")  # Error
            continue  # Skip
        raw_str = str(raw_amount).strip()  # Strip spaces
        cleaned_str = re.sub(r'[^0-9.\-]', '', raw_str)  # Keep only numbers, dot, minus
        if cleaned_str in ['', '.', '-', '-.', '.-']:  # If invalid after cleaning
            issues.append(f"Row {row_num}: Invalid amount {raw_amount}")  # Error
            continue  # Skip
        try:
            is_negative = cleaned_str.startswith('-')  # Check negative
            cleaned_str = cleaned_str.replace('-', '')  # Remove minus for parsing
            parts = cleaned_str.split('.')  # Split by dot
            if len(parts) > 2:  # If more than one dot
                cleaned_str = parts[0] + '.' + ''.join(parts[1:])  # Keep first dot only
            amt = float(cleaned_str)  # Convert to float
            if is_negative:  # If was negative
                amt = -amt  # Make negative
        except:
            issues.append(f"Row {row_num}: Cannot parse {raw_amount}")  # Error
            continue  # Skip

        if amt < 0:  # If amount is negative: return
            returns_count += 1  # Increase return count
            returns_total += amt  # Add to return total (negative)
            issues.append(f"Row {row_num}: Return {amt}")  # Log return

        gross_revenue += amt  # Add to gross
        row['amount'] = amt  # Update row with cleaned amount
        cleaned.append(row)  # Add to cleaned

    # Return cleaned data and stats
    return cleaned, issues, initial, returns_count, returns_total, gross_revenue

# Parse CSV file for branch compare (CSV only, simple)
def parse_csv_file(file):
    # Read file as text
    text = file.read().decode('utf-8')  # Decode uploaded file
    file.seek(0)  # Reset file pointer for possible reuse
    reader = csv.DictReader(io.StringIO(text))  # CSV DictReader from text

    total_sales = 0  # Total sales
    total_returns = 0  # Total returns
    total_rows = 0  # Row count

    # Loop through each row
    for row in reader:
        try:
            amount = None  # Amount to find
            # Check common amount column names
            for key in ['amount', 'total', 'sales', 'value']:
                if key in row and row[key]:
                    amount = float(row[key])
                    break
            if amount is None:  # If no amount column found, use last column
                last_val = list(row.values())[-1]
                amount = float(last_val)  # Try convert last value

            total_sales += amount  # Add to total sales
            total_rows += 1  # Increase row count
            if amount < 0:  # If negative, it is return
                total_returns += amount  # Add to returns

        except:
            continue  # Skip bad rows

    # Return totals
    return total_sales, total_returns, total_rows
# Home view - main page with report upload - matches urls.py path('', views.home_view)

# Must be logged in
def home_view(request):
    reports = QuickSalesReport.objects.filter(user=request.user).order_by('-id')  # User reports
    if request.method == 'POST' and request.FILES.get('file'):  # If file uploaded
        uploaded_file = request.FILES['file']  # Get uploaded file
        rows = []  # Empty rows list
        try:
            file_data = TextIOWrapper(uploaded_file.file, encoding='utf-8')  # Wrap file
            reader = csv.DictReader(file_data)  # Read CSV
            rows = list(reader)  # Convert to list
            cleaned, issues, initial, returns_count, returns_total, gross_revenue = clean_data(rows)  # Clean data
        except Exception as e:  # If error
            issues = [str(e)]  # Error as issue
            cleaned = []  # No cleaned data
            initial = returns_count = 0  # Zero counts
            returns_total = gross_revenue = 0.0  # Zero totals

        # Use get_price from models.py for pricing based on initial rows
        price = get_price(initial)  # Calculate price

        # Save result only, file not saved (space protection)
        QuickSalesReport.objects.create(
            user=request.user,  # Current user
            total_sales=gross_revenue,  # Save gross revenue
            total_expense=abs(returns_total),  # Expense is absolute of returns
            profit=gross_revenue + returns_total,  # Profit = gross + returns (returns negative)
            profit_margin=0,  # Will calculate later
            record_count=initial,  # Number of records
            price_charged=price,  # Price from get_price
        )

        context = {  # Data for template
            'reports': reports,  # User reports
            'cleaned_data': cleaned,  # Cleaned rows
            'issues': issues,  # Issues list
            'initial': initial,  # Initial count
            'returns_count': returns_count,  # Returns count
            'returns_total': returns_total,  # Returns total
            'gross_revenue': gross_revenue,  # Gross revenue
            'price': price,  # Calculated price
        }
        return render(request, 'home/index.html', context)  # Render index with context

    return render(request, 'home/index.html', {'reports': reports})  # GET: render index with reports only

# Branch compare view - professional: 10 max per compare, unlimited total - matches urls.py path('compare/', views.branch_compare)
@login_required  # Must be logged in
def branch_compare(request):
    my_branches = Store.objects.filter(  # Get user branches
        Q(owner=request.user) | Q(staff__user=request.user)  # Owner OR staff: unlimited total branches
    ).distinct()  # Remove duplicates

    results = []  # List of results
    branch_rows = {}  # Dict of row counts
    error_msg = None  # Error message holder

    if request.method == 'POST':  # If form submitted
        # Count how many branch files uploaded: professional limit 10
        uploaded_count = 0  # Counter
        for branch in my_branches:  # Loop all branches
            if request.FILES.get(f'branch_{branch.id}_file'):  # If file exists for this branch id
                uploaded_count += 1  # Increase count

        if uploaded_count > 10:  # If over 10
            error_msg = f"Max 10 branches per compare (professional standard). You uploaded {uploaded_count}."  # Error
        elif uploaded_count == 0:  # If none
            error_msg = "Upload at least 1 branch file."  # Error
        else:
            # Process each branch file
            for branch in my_branches:  # Loop branches
                file = request.FILES.get(f'branch_{branch.id}_file')  # Get file by id: branch_<id>_file
                if file:  # If file exists
                    if file.size > 5 * 1024 * 1024:  # Space protection: 5MB max per file
                        error_msg = f"{branch.name} file too big (max 5MB)."  # Error
                        break  # Stop
                    try:
                        sales, returns, row_count = parse_csv_file(file)  # Parse CSV
                        results.append({  # Add result
                            'branch_name': branch.name,  # Branch name
                            'sales': sales,  # Sales total
                            'returns': returns  # Returns total
                        })
                        branch_rows[branch.name] = row_count  # Save row count
                    except Exception as e:  # If parse fails
                        error_msg = f"Error reading {branch.name}: {e}"  # Error
                        break  # Stop

            if branch_rows and not error_msg:  # If have data and no error
                max_rows = max(branch_rows.values())  # Max rows among files
                price = get_price(max_rows)  # Use get_price from models.py
                # Render compare.html: matches new professional template
                return render(request, 'home/compare.html', {  # Compare page, NOT index
                    'my_branches': my_branches,  # All branches
                    'results': results,  # Compared results
                    'branch_rows': branch_rows,  # Row counts
                    'max_rows': max_rows,  # Max rows for pricing
                    'price': price,  # Price
                    'total_branches': my_branches.count(),  # Total: unlimited
                })

    # GET or error: show form again
    return render(request, 'home/compare.html', {  # Render compare.html always
        'my_branches': my_branches,  # Branches
        'results': results,  # Results (empty on GET)
        'error_msg': error_msg,  # Error if any
        'total_branches': my_branches.count(),  # Total branches
    })
    
def terms_view(request):
    return render(request, 'home/terms.html')

def privacy_view(request):
    return render(request, 'home/privacy.html')
