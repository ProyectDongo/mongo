"""
URL configuration for mongo project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""


from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('home/', views.home_view, name='home'),
    path('insert_cliente/', views.insert_cliente, name='insert_cliente'),
    path('insert_producto/', views.insert_producto, name='insert_producto'),
    path('insert_pedido/', views.insert_pedido, name='insert_pedido'),
    path('filter_clientes_ultimo_ano/', views.filter_clientes_ultimo_ano, name='filter_clientes_ultimo_ano'),
    path('filter_pedidos_monto_100/', views.filter_pedidos_monto_100, name='filter_pedidos_monto_100'),
    path('filter_clientes_gmail/', views.filter_clientes_gmail, name='filter_clientes_gmail'),
    path('filter_pedidos_2023/', views.filter_pedidos_2023, name='filter_pedidos_2023'),
    path('filter_pedidos_producto_101/', views.filter_pedidos_producto_101, name='filter_pedidos_producto_101'),
    path('filter_clientes_pedidos_500_ultimo_ano/', views.filter_clientes_pedidos_500_ultimo_ano, name='filter_clientes_pedidos_500_ultimo_ano'),
]
