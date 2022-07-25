from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import AuthenticationForm, CreationForm, PasswordResetForm


class SignUp(CreateView):
    form_class = CreationForm
    success_url = reverse_lazy('users:login')
    template_name = 'users/signup.html'


class Login(CreateView):
    form_class = AuthenticationForm
    success_url = reverse_lazy('posts:home')
    template_name = 'users/login.html'


class PasswordReset(CreateView):
    form_class = PasswordResetForm
    success_url = reverse_lazy('posts:home')
    template_name = 'users/password_reset_form.html'
