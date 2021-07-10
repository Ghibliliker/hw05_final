from django.shortcuts import get_object_or_404, render, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required

from .models import Comment, Follow, Group, Post, User
from .forms import PostForm, CommentForm


def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'index.html', {'page': page, })


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'group.html', {'group': group, 'page': page, })


def profile(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    post_list = author.posts.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    following = user.is_authenticated and Follow.objects.filter(
        user=user, author=author
    ).exists()
    return render(
        request,
        'profile.html',
        {'author': author, 'page': page, 'following': following, }
    )


def post_view(request, username, post_id):
    post = get_object_or_404(
        Post.objects.select_related('author'),
        id=post_id, author__username=username
    )
    form = CommentForm(instance=None)
    comments = Comment.objects.filter(post_id=post_id)
    return render(request, 'post.html', {
        'form': form,
        'post': post,
        'comments': comments,
    })


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('index')
    return render(request, 'new.html', {'form': form})


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(
        Post.objects.select_related('author'),
        id=post_id, author__username=username
    )
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
        return redirect('post_view', username=username, post_id=post_id)
    return redirect('post_view', username=username, post_id=post_id)


@login_required
def post_edit(request, username, post_id):
    if request.user.username != username:
        return redirect('post_view', username=username, post_id=post_id)
    post = get_object_or_404(
        Post.objects.select_related('author'),
        id=post_id,
        author__username=username
    )
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('post_view', username=username, post_id=post_id)
    return render(request, 'new.html', {'form': form, 'post': post, })


@login_required
def follow_index(request):
    user = request.user
    post_list = Post.objects.filter(author__following__user=user)
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'follow.html', {'page': page, })


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    if author != user:
        Follow.objects.get_or_create(author=author, user=user)
    return redirect('profile', username=username)


@login_required
def profile_unfollow(request, username):
    user = request.user
    Follow.objects.filter(author__username=username, user=user).delete()
    return redirect('profile', username=username)


def page_not_found(request, exception):
    return render(
        request,
        'misc/404.html',
        {'path': request.path},
        status=404
    )


def server_error(request):
    return render(request, 'misc/500.html', status=500)
