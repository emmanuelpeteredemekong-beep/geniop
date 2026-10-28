from django.shortcuts import render  # Render templates to browser
# from django.contrib.auth.decorators import login_required  # REMOVED for Phase 2 No Login
from .models import get_price  # Price helper - from your models.py
import csv  # For CSV reading/writing
import re  # For cleaning amount with regex
import os  # For file delete - os.unlink
import tempfile  # For temporary file - spec requires cleanup
from io import TextIOWrapper  # Wrapper for uploaded file reading
from django.http import HttpResponse  # For download response
import pandas as pd  # For future excel support

# YOUR clean_data function - with comments
def clean_data(rows):  # Function to clean CSV rows
    issues = []  # List to store errors and warnings
    initial = len(rows)  # Initial count of rows uploaded
    normalized = []  # List for normalized keys
    # Loop through rows, idx start at 2 because header is row 1
    for idx, r in enumerate(rows, start=2):  # Enumerate rows
        if not r:  # If row is empty dict or None
            continue  # Skip empty row
        new_r = {}  # New cleaned row dict
        # Loop through key, value in row
        for k, v in r.items():  # Items in row
            if k is None:  # If key is None (extra commas)
                continue  # Skip it
            key = str(k).lower().strip().replace(' ', '_')  # Normalize key: lower case, strip spaces, space to underscore
            if isinstance(v, str):  # If value is string
                v = v.strip()  # Remove leading/trailing spaces
            new_r[key] = v  # Add to new cleaned row
        # Check if row is completely empty after cleaning
        if not any(v not in [None, '', ' '] for v in new_r.values()):  # If all values empty
            issues.append(f"Row {idx}: Empty row")  # Add to issues
            continue  # Skip this row
        new_r['_row_num'] = idx  # Keep original row number for error tracking
        normalized.append(new_r)  # Add to normalized list

    cleaned = []  # Final cleaned list for display
    returns_count = 0  # Count of returns (negative amounts)
    returns_total = 0.0  # Total sum of returns (negative)
    gross_revenue = 0.0  # Total gross revenue (all amounts)

    # Loop through normalized rows to parse amount
    for row in normalized:  # For each normalized row
        row_num = row.pop('_row_num')  # Get and remove row number
        raw_amount = row.get('amount')  # Get amount field from row
        if raw_amount in [None, '']:  # If amount missing or empty
            issues.append(f"Row {row_num}: Missing amount")  # Add error
            continue  # Skip row
        raw_str = str(raw_amount).strip()  # Convert to string and strip
        cleaned_str = re.sub(r'[^0-9.\-]', '', raw_str)  # Keep only numbers, dot, minus - remove currency symbols
        if cleaned_str in ['', '.', '-', '-.', '.-']:  # If invalid after cleaning
            issues.append(f"Row {row_num}: Invalid amount {raw_amount}")  # Add error
            continue  # Skip row
        try:  # Try to parse amount
            is_negative = cleaned_str.startswith('-')  # Check if negative (return)
            cleaned_str = cleaned_str.replace('-', '')  # Remove minus for parsing
            parts = cleaned_str.split('.')  # Split by dot
            if len(parts) > 2:  # If more than one dot (e.g., 1.000.00)
                cleaned_str = parts[0] + '.' + ''.join(parts[1:])  # Keep first dot only
            amt = float(cleaned_str)  # Convert to float
            if is_negative:  # If was negative
                amt = -amt  # Make it negative again
        except:  # If parsing fails
            issues.append(f"Row {row_num}: Cannot parse {raw_amount}")  # Add error
            continue  # Skip row

        if amt < 0:  # If amount is negative: it is a return
            returns_count += 1  # Increase return count
            returns_total += amt  # Add to return total (negative value)
            issues.append(f"Row {row_num}: Return {amt}")  # Log return as issue/info

        gross_revenue += amt  # Add to gross revenue
        row['amount'] = amt  # Update row with cleaned float amount
        cleaned.append(row)  # Add to final cleaned list

    # Return all results
    return cleaned, issues, initial, returns_count, returns_total, gross_revenue  # Return tuple

# Home view - main page - Phase 2 NO LOGIN - matches urls.py path('', views.home_view)
def home_view(request):  # Main home view
    # In-memory feed for Phase 2 - no DB - for "What's happening in your market?"
    if not hasattr(home_view, 'posts'):  # If posts attribute not exist
        home_view.posts = []  # Create empty posts list

    context = {  # Base context for template
        'posts': home_view.posts,  # Pass posts to template - basic Home Feed
    }

    if request.method == 'POST':  # If form submitted
        # Case 1: Market post - "What's happening in your market?" post box
        if 'market_post' in request.POST:  # If market post form
            text = request.POST.get('market_post','').strip()  # Get text and strip
            if text:  # If not empty
                home_view.posts.insert(0, {'text': text})  # Add to top of feed - newest first

        # Case 2: Report upload - Quick Sales Report card
        elif request.FILES.get('file'):  # If file uploaded - matches <input name="file">
            uploaded_file = request.FILES['file']  # Get uploaded file object
            rows = []  # Empty rows list
            tmp_path = None  # Temp file path holder
            try:  # Try to process file
                # Save to temp file only - spec: clean up temporary files
                with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp:  # Create temp file
                    for chunk in uploaded_file.chunks():  # Loop chunks - for large files
                        tmp.write(chunk)  # Write chunk to temp
                    tmp_path = tmp.name  # Save temp path

                # Read temp file as CSV - using TextIOWrapper style
                with open(tmp_path, 'r', encoding='utf-8', errors='ignore') as f:  # Open temp file
                    reader = csv.DictReader(f)  # CSV DictReader - first row is header
                    rows = list(reader)  # Convert to list

                os.unlink(tmp_path)  # DELETE TEMP FILE IMMEDIATELY - spec: avoid permanent storage
                tmp_path = None  # Clear path after delete

                # Clean data using your function
                cleaned, issues, initial, returns_count, returns_total, gross_revenue = clean_data(rows)  # Clean rows
                price = get_price(initial)  # Get price based on initial count - your pricing helper

                # DO NOT SAVE TO DB - keep in session only - spec: Keep uploaded reports out of permanent database
                request.session['last_report'] = {  # Save to session - not to QuickSalesReport model
                    'initial': initial,  # Initial row count
                    'returns_count': returns_count,  # Returns count
                    'returns_total': returns_total,  # Returns total (negative)
                    'gross_revenue': gross_revenue,  # Gross revenue
                    'price': price,  # Price charged
                    'profit': gross_revenue + returns_total,  # Profit = gross + returns (returns negative)
                    'cleaned_count': len(cleaned)  # Cleaned count
                }

                # Prepare context for template - report upload card, sales/expense/profit calculations
                context.update({  # Update context
                    'cleaned_data': cleaned[:50],  # First 50 cleaned rows for display
                    'issues': issues,  # Issues list
                    'initial': initial,  # Initial count
                    'returns_count': returns_count,  # Returns count
                    'returns_total': returns_total,  # Returns total
                    'gross_revenue': gross_revenue,  # Gross revenue - sales
                    'price': price,  # Price
                    'profit': gross_revenue + returns_total,  # Profit - for display
                })

            except Exception as e:  # If error during processing
                if tmp_path:  # If temp file exists
                    try:  # Try cleanup
                        os.unlink(tmp_path)  # Delete temp file even on error - space protection
                    except:  # Ignore cleanup error
                        pass
                context['issues'] = [str(e)]  # Show error as issue

    # Add last report from session - for page refresh
    if 'last_report' in request.session:  # If report in session
        context['last_report'] = request.session['last_report']  # Pass to template
        context['download_ready'] = True  # Enable download button - downloadable results

    return render(request, 'home/index.html', context)  # Render home/index.html - Build Home layout and navigation

# Download view - downloadable results - Phase 2 spec
def download_report_view(request):  # Download CSV results
    data = request.session.get('last_report')  # Get from session - not from DB
    if not data:  # If no report
        return HttpResponse("No report", status=404)  # Return 404
    response = HttpResponse(content_type='text/csv')  # Create CSV response
    response['Content-Disposition'] = 'attachment; filename="quick_sales.csv"'  # Download header
    writer = csv.writer(response)  # CSV writer
    writer.writerow(['Metric','Value'])  # Header row
    for k,v in data.items():  # Loop metrics
        writer.writerow([k,v])  # Write row
    return response  # Return downloadable file

# Terms view - static page
def terms_view(request):  # Terms page
    return render(request, 'home/terms.html')  # Render terms template

# Privacy view - static page
def privacy_view(request):  # Privacy page
    return render(request, 'home/privacy.html')  # Render privacy template

# Branch compare - for Phase 2, disabled or no login version - professional: 10 max per compare
def branch_compare(request):  # Branch compare view - matches urls.py path('compare/', views.branch_compare)
    # For Phase 2 No Login, we return simple info - Phase 3 will add real compare with login
    return render(request, 'home/compare.html', {'info': 'Branch compare needs login - coming in Phase 3'})  # Render compare placeholder# Compare page, NOT index
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
