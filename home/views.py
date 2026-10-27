from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Post, Follow, SalesReport

@login_required
def home(request):
    tab = request.GET.get('tab', 'foryou')
    
    if tab == 'following':
        following_ids = Follow.objects.filter(follower=request.user).values_list('following_id', flat=True)
        posts = Post.objects.filter(user_id__in=following_ids).order_by('-created_at')
    elif tab == 'sales':
        posts = []
        reports = SalesReport.objects.filter(user=request.user).order_by('-uploaded_at')
        return render(request, 'home.html', {
            'tab': tab,
            'posts': posts,
            'reports': reports
        })
    else:  # foryou
        posts = Post.objects.all().order_by('-created_at')
    
    if request.method == 'POST' and 'caption' in request.POST:
        caption = request.POST.get('caption')
        image = request.FILES.get('image')
        if image:
            Post.objects.create(
                user=request.user,
                caption=caption,
                image=image
            )
            return redirect('home')

    return render(request, 'home.html', {
        'tab': tab,
        'posts': posts
    })

@login_required
def upload_report(request):
    if request.method == 'POST':
        file = request.FILES.get('file')
        sales = request.POST.get('sales', 0)
        expense = request.POST.get('expense', 0)
        if file:
            SalesReport.objects.create(
                user=request.user,
                file=file,
                sales=sales,
                expense=expense
            )
    return redirect('/home/?tab=sales')
