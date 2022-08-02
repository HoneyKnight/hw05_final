from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post

COUNT_POSTS = 10
User = get_user_model()


def paginator(queryset, request):
    paginator = Paginator(queryset, COUNT_POSTS)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


@cache_page(20, key_prefix='index_page')
def index(request):
    posts = Post.objects.select_related('group', 'author')
    page_obj = paginator(posts, request)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related('author')
    page_obj = paginator(posts, request)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.select_related('author')
    page_obj = paginator(posts, request)
    if request.user.is_authenticated:
            is_following = Follow.objects.filter(user=request.user, author=author).exists()
    else:
        is_following = False
    context = {
        'author': author,
        'page_obj': page_obj,
        'following': is_following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    comments = post.comments.all()
    context = {
        'post': post,
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None)
    if form.is_valid():
        form = form.save(commit=False)
        form.author = request.user
        form.save()
        return redirect('posts:profile', request.user.username)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id=post_id)
    if not form.is_valid():
        return render(request, 'posts/create_post.html', {
            'post': post,
            'form': form,
            'is_edit': True,
        })
    form.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    follow_objects = Post.objects.filter(author__following__user=request.user)
    page_obj = paginator(follow_objects, request)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    user = request.user
    author = User.objects.get(username=username)
    is_following = Follow.objects.filter(user=user, author=author)
    if user != author and not is_following.exists():
        Follow.objects.create(user=user, author=author)
    return redirect('posts:profile', author.username)

@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    is_following = Follow.objects.filter(user=request.user, author=author)
    if is_following.exists():
        is_following.delete()
    return redirect('posts:profile', author.username)
