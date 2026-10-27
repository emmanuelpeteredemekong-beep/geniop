from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Post, SalesReport, get_price
import pandas as pd
from django.db.models import Sum
import os

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
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)

            # Normalize columns lower
            df.columns = [c.lower() for c in df.columns]

            # DATE FILTER - FREE
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            if 'date' in df.columns and start_date and end_date:
                df['date'] = pd.to_datetime(df['date'])
                df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]

            count = len(df)
            price = get_price(count)

            # 5 FEATURES - CALCULATE ONLY, NO SAVE
            total_revenue = df['amount'].sum() if 'amount' in df.columns else 0
            total_expense = df['expense'].sum() if 'expense' in df.columns else 0
            total_profit = total_revenue - total_expense

            best_product = None
            worst_product = None
            branches = []
            if 'product' in df.columns and 'amount' in df.columns:
                prod = df.groupby('product')['amount'].sum().sort_values(ascending=False)
                if not prod.empty:
                    best_product = {'product': prod.index[0], 'total': prod.iloc[0]}
                    worst_product = {'product': prod.index[-1], 'total': prod.iloc[-1]}

            if 'branch' in df.columns and 'amount' in df.columns:
                br = df.groupby('branch')['amount'].sum().sort_values(ascending=False)
                branches = [{'branch': k, 'total': v} for k, v in br.items()]

            # Insight Box
            insight = f"Analyzed {count} sales records."
            if total_expense > total_revenue * 0.7:
                insight = "Expenses too high (70% of revenue) - review your costs!"
            elif best_product:
                insight = f"Advice: Push more {best_product['product']} - your best seller!"

            context.update({
                'count': count,
                'price': price,
                'label': f"Showing: {count} sales = ₦{price} to unlock full report",
                'total_revenue': total_revenue,
                'total_profit': total_profit,
                'total_expense': total_expense,
                'best_product': best_product,
                'worst_product': worst_product,
                'branches': branches,
                'insight': insight,
                'last_report': last_report,
                'start_date': start_date,
                'end_date': end_date,
            })
        except Exception as e:
            context['error'] = str(e)

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
