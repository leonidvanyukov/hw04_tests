from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PostForm
from .models import Group, Post, User
from .utils import count_elements, create_paginator


def index(request):
    post_list = Post.objects.all()
    page_obj = create_paginator(post_list, request.GET.get('page'))
    context = {
        'page_obj': page_obj,
    }

    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    page_obj = create_paginator(post_list, request.GET.get('page'))
    context = {
        'group': group,
        'page_obj': page_obj,
    }

    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    author_posts = author.posts.all()
    page_obj = create_paginator(author_posts, request.GET.get('page'))
    posts_count = count_elements(author_posts)
    context = {
        'author': author,
        'page_obj': page_obj,
        'posts_count': posts_count
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    posts = Post.objects.filter(author__exact=post.author).count()
    context = {
        'post': post,
        'posts_count': posts,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None)
    if not form.is_valid():
        return render(
            request,
            'posts/new_post.html',
            {'form': form, 'is_edit': False}
        )

    post = form.save(commit=False)
    post.author = request.user
    post.save()

    return redirect('posts:profile', request.user.username)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:profile', request.user.username)
    form = PostForm(
        request.POST or None,
        instance=post,
    )
    if not form.is_valid():
        return render(
            request,
            'posts/new_post.html',
            {'post': post, 'form': form, 'is_edit': True},
        )
    form.save()
    return redirect('posts:post_detail', str(post_id))
