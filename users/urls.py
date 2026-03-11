from django.urls import path
from .views import SignUpView, CodeVerify, GetNewCode

urlpatterns = [
    path('sign-up/', SignUpView.as_view()),
    path('code-verify', CodeVerify.as_view()),
    path('get-new-code/', GetNewCode.as_view())
]