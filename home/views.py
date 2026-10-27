from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Post, SalesReport, get_price
import pandas as pd
import re

def clean_data(df):
    issues = []
    initial = len(df)
    
    # 1. Normalize columns
    df.columns = [str(c).lower().strip() for c in df.columns]
    df = df.dropna(how='all')

    returns_count = 0
    returns_total = 0.0
    gross_revenue = 0.0

    # 2. Amount cleaning - keep minus for detection
    if 'amount' in df.columns:
        df['amount'] = df['amount'].astype(str).apply(
            lambda x: re.sub(r'[^0-9.\-]', '', str(x))
        )
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
        
        invalid = df['amount'].isna().sum()
        if invalid > 0:
            issues.append(f"{invalid} rows had invalid amount - removed")
        df = df.dropna(subset=['amount'])

        # Detect negatives - CALL OUT, don't hide
        neg_df = df[df['amount'] < 0]
        returns_count = len(neg_df)
        returns_total = float(neg_df['amount'].sum()) if returns_count > 0 else 0.0
        
        if returns_count > 0:
            issues.append(
                f"{returns_count} negative values found (returns/refunds total {returns_total:,.0f}) - excluded from gross, calculated as net"
            )

        pos_df = df[df['amount'] >= 0]
        gross_revenue = float(pos_df['amount'].sum()) if not pos_df.empty else 0.0
        df = pos_df[pos_df['amount'] > 0]
        
        zero = len(pos_df[pos_df['amount'] == 0])
        if zero > 0:
            issues.append(f"{zero} zero-value sales removed")

    else:
        issues.append("No 'amount' column found - check file header")

    # 3. Expense
    if 'expense' in df.columns:
        df['expense'] = df['expense'].astype(str).apply(
            lambda x: re.sub(r'[^0-9.\-]', '', str(x))
        )
        df['expense'] = pd.to_numeric(df['expense'], errors='coerce').fillna(0)
        neg_exp = len(df[df['expense'] < 0])
        if neg_exp > 0:
            issues.append(f"{neg_exp} negative expenses found - converted to 0")
        df['expense'] = df['expense'].clip(lower=0)
    else:
        df['expense'] = 0

    # 4. Product / Branch
    if 'product' in df.columns:
        df['product'] = df['product'].astype(str).str.strip().str.title()
        df = df[df['product'].str.lower() != 'nan']
    else:
        df['product'] = 'Unknown'

    if 'branch' in df.columns:
        df['branch'] = df['branch'].astype(str).str.strip().str.title()
        df['branch'] = df['branch'].replace('Nan', 'Main').fillna('Main')
    else:
        df['branch'] = 'Main'

    # 5. Date
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        bad = df['date'].isna().sum()
        if bad > 0:
            issues.append(f"{bad} invalid dates removed")
        df = df.dropna(subset=['date'])

    # 6. Duplicates
    dupes = df.duplicated().sum()
    if dupes > 0:
        issues.append(f"{dupes} duplicate rows removed")
    df = df.drop_duplicates()

    final = len(df)
    net_revenue = gross_revenue + returns_total  # returns_total is negative

    df.attrs['issues'] = issues
    df.attrs['initial'] = initial
    df.attrs['final'] = final
    df.attrs['removed'] = initial - final
    df.attrs['returns_count'] = returns_count
    df.attrs['returns_total'] = returns_total
    df.attrs['gross_revenue'] = gross_revenue
    df.attrs['net_revenue'] = net_revenue

    return df

@login_required
def home(request):
    tab = request.GET.get('tab', 'foryou')
    reports = SalesReport.objects.filter(user=request.user).order_by('-uploaded_at')
    posts = Post.objects.all().order_by('-created_at')
    context = {'tab': tab, 'posts': posts, 'reports': reports}

    if tab == 'sales' and reports.exists():
        last_report = reports.first()
        file_path = last_report.file.path

        try:
            if file_path.endswith('.csv'):
                raw_df = pd.read_csv(file_path)
            else:
                raw_df = pd.read_excel(file_path)

            df = clean_data(raw_df)

            # Date filter - FREE
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            if 'date' in df.columns and start_date and end_date:
                df_filtered = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
            else:
                df_filtered = df

            count = len(df_filtered)
            price = get_price(count)

            # 5 FEATURES
            gross = df_filtered.attrs.get('gross_revenue', 0)
            net_revenue = df_filtered.attrs.get('net_revenue', gross)
            returns_total = df_filtered.attrs.get('returns_total', 0)
            returns_count = df_filtered.attrs.get('returns_count', 0)

            total_expense = df_filtered['expense'].sum() if 'expense' in df_filtered.columns else 0
            total_profit = net_revenue - total_expense

            best_product = None
            worst_product = None
            if 'product' in df_filtered.columns and not df_filtered.empty:
                prod = df_filtered.groupby('product')['amount'].sum().sort_values(ascending=False)
                if not prod.empty:
                    best_product = {'product': prod.index[0], 'total': float(prod.iloc[0])}
                    worst_product = {'product': prod.index[-1], 'total': float(prod.iloc[-1])}

            branches = []
            if 'branch' in df_filtered.columns and not df_filtered.empty:
                br = df_filtered.groupby('branch')['amount'].sum().sort_values(ascending=False)
                branches = [{'branch': k, 'total': float(v)} for k, v in br.items()]

            # Insight box
            insight = f"Analyzed {count} valid sales."
            if returns_count > 0:
                insight = f"Net revenue {net_revenue:,.0f} after {returns_count} returns ({returns_total:,.0f}). "
            if total_expense > net_revenue * 0.7 and net_revenue > 0:
                insight += "Expenses high (70%+ of revenue) - review costs."
            elif best_product:
                insight += f"Push {best_product['product']} - best seller."

            context.update({
                'count': count,
                'initial': df.attrs.get('initial', count),
                'removed': df.attrs.get('removed', 0),
                'price': price,
                'label': f"Showing: {count} sales (cleaned from {df.attrs.get('initial', count)}) = N{price} to unlock full report",
                'gross_revenue': gross,
                'net_revenue': net_revenue,
                'total_revenue': net_revenue,
                'returns_count': returns_count,
                'returns_total': returns_total,
                'total_expense': total_expense,
                'total_profit': total_profit,
                'best_product': best_product,
                'worst_product': worst_product,
                'branches': branches,
                'issues': df.attrs.get('issues', []),
                'insight': insight,
                'last_report': last_report,
                'start_date': start_date,
                'end_date': end_date,
            })
        except Exception as e:
            context['error'] = f"Report error: {str(e)}"

    if request.method == 'POST' and 'caption' in request.POST:
        Post.objects.create(
            user=request.user,
            caption=request.POST.get('caption'),
            image=request.FILES.get('image')
        )
        return redirect('home')

    return render(request, 'home.html', context)

@login_required
def upload_report(request):
    if request.method == 'POST':
        file = request.FILES.get('file')
        if file:
            SalesReport.objects.create(user=request.user, file=file)
    return redirect('/home/?tab=sales')

@login_required
def mark_paid(request, id):
    report = SalesReport.objects.filter(id=id, user=request.user).first()
    if report:
        report.is_paid = True
        report.save()
    return redirect('/home/?tab=sales')
