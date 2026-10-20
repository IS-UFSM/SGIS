from django.contrib import admin
from django.urls import include, path

from usuarios import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('trilhas/', include('trilhas.urls')),
    path('', views.home_view, name='home'),
]
