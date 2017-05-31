from django.shortcuts import redirect, render

from .auth import (
        generate_challenge,
        get_service_pubkey,
        verify_response,
        verify_notary,
)
from .models import Post

from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseRedirect
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Permission
from django.utils.html import escape


#### Password auth related

def login(request):
    if request.method == 'GET':
        return render(request, 'bbs/login.html', {})
    elif request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        user = auth.authenticate(username=username, password=password)
        if user is not None:
            auth.login(request, user)
            return redirect('list')
        else:
            return render(request, 'bbs/login.html', {'error': True})

@login_required(login_url='/bbs/login')
def logout(request):
    auth.logout(request)
    return redirect('index')


#### BBS functions

def index(request):
    return render(request, 'bbs/index.html', {})

@login_required(login_url='/bbs/login')
def list(request):
    posts = Post.objects.all()
    return render(request, 'bbs/list.html', {'posts': posts})

def check_post_permission(user, post, use_script):
    if use_script and not user.has_perm('bbs.use_script'):
        return False, 'Normal user cannot write a post that contains\
                       Javascript. Please uncheck the \'Use Javascript\''
    if post and post.author != user:
        return False, 'You are not an owner of the post.\
                       Only author can do it.'
    if post.title == '':
        return False, 'We need a title.'
    return True, ''

@login_required(login_url='/bbs/login')
def write(request):
    if request.method == 'GET':
        return render(request, 'bbs/write.html', {})
    elif request.method == 'POST':
        user = request.user
        title = request.POST.get('title')
        content = request.POST.get('content')
        use_script = 'use_script' in request.POST

        if not use_script:
            title = escape(title)
            content = escape(content)

        post = Post(title=title, content=content, use_script=use_script,
                    author=user)

        can_write, error_msg = check_post_permission(user, post, use_script)
        if can_write:
            post.save()
            return redirect("list")
        else:
            return render(request, 'bbs/error.html', {'error_msg': error_msg})

@login_required(login_url='/bbs/login')
def read(request, post_id):
    try:
        post = Post.objects.get(id=int(post_id))
    except ObjectDoesNotExist:
        error_msg = 'There is no post that id is ' + post_id
        return render(request, 'bbs/error.html', {'error_msg': error_msg})

    resp = render(request, 'bbs/read.html', {'post': post})
    if (request.user.username == 'root'):
        with open('/tmp/flag') as f:
            resp.set_cookie(key='flag', value=f.read())

    return resp

@login_required(login_url='/bbs/login')
def delete(request, post_id):
    try:
        post = Post.objects.get(id=int(post_id))
    except ObjectDoesNotExist:
        error_msg = 'There is no post that id is ' + post_id
        return render(request, 'bbs/error.html', {'error_msg': error_msg})

    can_delete, error_msg = check_post_permission(request.user, post, None)
    if can_delete:
        post.delete()
        return redirect('list')
    else:
        return render(request, 'bbs/error.html', {'error_msg': error_msg})

@login_required(login_url='/bbs/login')
def edit(request, post_id):
    try:
        post = Post.objects.get(id=int(post_id))
    except ObjectDoesNotExist:
        error_msg = 'There is no post that id is ' + post_id
        return render(request, 'bbs/error.html', {'error_msg': error_msg})

    if request.method == 'GET':
        can_edit, error_msg = check_post_permission(request.user, post, None)
        if can_edit:
            return render(request, 'bbs/edit.html', {'post': post})
        else:
            return render(request, 'bbs/error.html', {'error_msg': error_msg})
    elif request.method == 'POST':
        user = request.user
        title = request.POST.get('title')
        content = request.POST.get('content')
        use_script = 'use_script' in request.POST

        if not use_script:
            title = escape(title)
            content = escape(content)

        can_edit, error_msg = check_post_permission(user, post, use_script)
        if can_edit:
            post.title = title
            post.content = content
            post.use_script = use_script
            post.save()
            return redirect("list")
        else:
            return render(request, 'bbs/error.html', {'error_msg': error_msg})


#### PGP auth related

def auth_index(request):
    return render(request, 'bbs/auth_index.html', {})

def auth_chal(request):
    if request.method == 'POST':
        auth_id = request.POST.get('id')
        challenge = generate_challenge(auth_id)
        if challenge is not None:
            nonce, enc_nonce = challenge
            request.session['auth_id'] = auth_id
            request.session['auth_nonce'] = nonce
            service_pubkey = get_service_pubkey()
            context = {
                'auth_id': auth_id,
                'enc_nonce': enc_nonce,
                'service_pubkey': service_pubkey
            }
            return render(request, 'bbs/auth_chal.html', context)
        else:
            return render(request, 'bbs/auth_index.html', {'error':True})
    else:
        error_msg = 'Invalid access'
        return render(request, 'bbs/error.html', {'error_msg': error_msg})

def auth_resp(request):
    if request.method == 'POST':
        auth_resp = request.POST.get('auth_resp')
        auth_nonce = request.session['auth_nonce']
        auth_id = request.session['auth_id']
        if verify_response(auth_nonce, auth_resp):
            print("Auth success for {}".format(auth_id))
            request.session['auth_success'] = True
            return redirect('auth_success')
        else:
            print("Auth failed")
            request.session['auth_success'] = False
            error_msg = 'Authentication Failed, Are you really ' + auth_id + '?'
            return render(request, 'bbs/error.html', {'error_msg': error_msg})
    else:
        error_msg = 'Invalid access'
        return render(request, 'bbs/error.html', {'error_msg': error_msg})

def auth_success(request):
    success = request.session.get('auth_success')
    auth_id = request.session.get('auth_id')
    if success and auth_id:
        if request.method == 'GET':
            return render(request, 'bbs/auth_success.html',
                          {'auth_id': auth_id})
        elif request.method == 'POST':
            password = request.POST.get('password')
            password_check = request.POST.get('password_check')
            if password == password_check:
                try:
                    # Change password if the user already exists.
                    user = User.objects.get(username=auth_id)
                except ObjectDoesNotExist:
                    # Create new user and
                    # Set password if the user does not exists.
                    user = User(username=auth_id)
                user.set_password(password)
                user.save()
                return redirect('login')
            else:
                return render(request,
                              'bbs/auth_success.html',
                              {'auth_id': auth_id, 'error':True})
    else:
        error_msg = 'Invalid access'
        return render(request, 'bbs/error.html', {'error_msg': error_msg})


### Notary related

@login_required(login_url='/bbs/login')
def notarize(request):
    if request.method == 'GET':
        nick = request.GET.get('nick')
        if nick is None:
            nick = ''
        filtering = ['import', 'exec', 'eval', 'pickle', 'os', 'subprocess', 'sys', 'input']
        for f in filtering:
            if f in nick:
                nick = ''
                break
        if nick != '':
            nick = eval(nick)
        return render(request, 'bbs/notarize.html', {'nick' : nick})
    elif request.method == 'POST':
        user = request.user
        auth_id = user.username
        proof = request.POST.get('proof')
        if verify_notary(auth_id, proof):
            # Grant use_script permission
            permission = Permission.objects.get(codename='use_script')
            user.user_permissions.add(permission)
            user.save()
            print("{} is notarized.".format(auth_id))
            return redirect('list')
        else:
            print("{} is not notarized.".format(auth_id))
            return render(request, 'bbs/notarize.html', {'error': True})
