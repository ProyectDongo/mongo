# core/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import *
import pymongo
from datetime import datetime, timedelta, timezone
from functools import wraps
import uuid
from bson.decimal128 import Decimal128
from bson import ObjectId



# Función para obtener el cliente de MongoDB 
def get_mongo_client(request):
    username = request.session.get('mongo_username')
    password = request.session.get('mongo_password')
    if not username or not password:
        return None
    uri = f"mongodb+srv://{username}:{password}@cluster0.cc5wfzr.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    try:
        client = pymongo.MongoClient(uri)
        client.server_info()  
        return client
    except:
        return None




# Decorador para proteger vistas 
def mongo_login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if 'mongo_username' not in request.session or 'mongo_password' not in request.session:
            messages.error(request, 'Por favor, ingrese las credenciales de MongoDB.')
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper





# Vista de login 
def login_view(request):
    if request.method == 'POST':
        form = MongoLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            request.session['mongo_username'] = username
            request.session['mongo_password'] = password
            client = get_mongo_client(request)
            if client:
                messages.success(request, 'Conexión exitosa a MongoDB.')
                return redirect('home')
            else:
                messages.error(request, 'Credenciales inválidas.')
    else:
        form = MongoLoginForm()
    return render(request, 'core/login.html', {'form': form})






# Vista home 
@mongo_login_required
def home_view(request):
    client = get_mongo_client(request)
    if not client:
        messages.error(request, 'Error al conectar a MongoDB.')
        return redirect('login')
    db = client['ecommerce_db']
    clientes = list(db['clientes'].find())
    pedidos = list(db['pedidos'].find())
    return render(request, 'core/home.html', {'clientes': clientes, 'pedidos': pedidos})






# Vista para insertar cliente 
@mongo_login_required
def insert_cliente(request):
    client = get_mongo_client(request)
    if not client:
        messages.error(request, 'Error al conectar a MongoDB.')
        return redirect('login')
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            db = client['ecommerce_db']
            cliente_data = form.cleaned_data
            cliente_data['fecha_registro'] = datetime.combine(cliente_data['fecha_registro'], datetime.min.time())
            db['clientes'].insert_one(cliente_data)
            messages.success(request, 'Cliente insertado correctamente.')
            return redirect('home')
    else:
        form = ClienteForm()
    return render(request, 'core/insert_cliente.html', {'form': form})







# Vista para insertar pedido 
@mongo_login_required
def insert_pedido(request):
    client = get_mongo_client(request)
    if not client:
        messages.error(request, 'Error al conectar a MongoDB.')
        return redirect('login')
    db = client['ecommerce_db']
    clientes = list(db['clientes'].find())
    productos = list(db['productos'].find())
    for prod in productos:
        prod['id_producto'] = str(prod['_id'])
        del prod['_id']
    
    if request.method == 'POST':
        form = PedidoForm(request.POST, clientes=clientes, productos=productos)
        if form.is_valid():
            pedido_data = form.cleaned_data
            productos_seleccionados = []
            monto_total = 0.0
            for prod_id in pedido_data['productos']:
                prod = next(p for p in productos if p['id_producto'] == prod_id)
                cantidad_key = f'cantidad_{prod_id}'
                cantidad = int(request.POST.get(cantidad_key, 1))
                if cantidad < 1:
                    cantidad = 1
                precio = float(prod['precio'].to_decimal())  # Convertir Decimal128 a float
                productos_seleccionados.append({
                    'producto_id': prod_id,
                    'nombre': prod['nombre'],
                    'precio': precio,
                    'cantidad': cantidad
                })
                monto_total += precio * cantidad
            pedido = {
                'cliente_id': pedido_data['cliente'],
                'fecha_pedido': datetime.combine(pedido_data['fecha_pedido'], datetime.min.time()),
                'monto_total': monto_total,
                'productos': productos_seleccionados
            }
            db['pedidos'].insert_one(pedido)
            messages.success(request, 'Pedido insertado correctamente.')
            return redirect('home')
        else:
            messages.error(request, 'Error en el formulario. Por favor, revisa los datos.')
    else:
        form = PedidoForm(clientes=clientes, productos=productos)
    return render(request, 'core/insert_pedido.html', {'form': form, 'productos': productos})




# Filtros según requerimientos 
@mongo_login_required
def filter_clientes_ultimo_ano(request):
    client = get_mongo_client(request)
    db = client['ecommerce_db']
    hace_un_ano = datetime.now() - timedelta(days=365)
    query = {'fecha_registro': {'$gte': hace_un_ano}}
    clientes_list = list(db['clientes'].find(query))
    return render(request, 'core/filter_clientes.html', {'clientes': clientes_list})




@mongo_login_required
def filter_pedidos_monto_100(request):
    client = get_mongo_client(request)
    db = client['ecommerce_db']
    query = {'monto_total': {'$gt': 100}}
    pedidos_list = list(db['pedidos'].find(query))
    return render(request, 'core/filter_pedidos.html', {'pedidos': pedidos_list})




@mongo_login_required
def filter_clientes_gmail(request):
    client = get_mongo_client(request)
    db = client['ecommerce_db']
    query = {'email': {'$regex': '@gmail\\.com$', '$options': 'i'}}
    clientes_list = list(db['clientes'].find(query))
    return render(request, 'core/filter_clientes.html', {'clientes': clientes_list})




@mongo_login_required
def filter_pedidos_2023(request):
    client = get_mongo_client(request)
    db = client['ecommerce_db']
    query = {'fecha_pedido': {'$gte': datetime(2023, 1, 1), '$lt': datetime(2024, 1, 1)}}
    pedidos_list = list(db['pedidos'].find(query))
    return render(request, 'core/filter_pedidos.html', {'pedidos': pedidos_list})




@mongo_login_required
def filter_pedidos_producto_101(request):
    client = get_mongo_client(request)
    db = client['ecommerce_db']
    query = {'productos.producto_id': '101'}  
    pedidos_list = list(db['pedidos'].find(query))
    return render(request, 'core/filter_pedidos.html', {'pedidos': pedidos_list})



@mongo_login_required
def filter_clientes_pedidos_500_ultimo_ano(request):
    client = get_mongo_client(request)
    if not client:
        messages.error(request, 'Error al conectar a MongoDB.')
        return redirect('login')
    
    db = client['ecommerce_db']
    
    # Calcular la fecha de hace un año en UTC
    hace_un_ano = datetime.now(timezone.utc) - timedelta(days=365)
    
    # Filtrar pedidos
    pedidos_filtrados = db['pedidos'].find({
        'monto_total': {'$gt': 500},
        'fecha_pedido': {'$gte': hace_un_ano}
    })
    
    # Convertir a lista para depuración
    pedidos_list = list(pedidos_filtrados)
    print("Pedidos filtrados:", pedidos_list)
    
    # Extraer cliente_ids y convertirlos a ObjectId
    cliente_ids = [ObjectId(p['cliente_id']) for p in pedidos_list]
    print("Cliente IDs (ObjectId):", cliente_ids)
    
    # Buscar clientes con ObjectId
    clientes_list = list(db['clientes'].find({'_id': {'$in': cliente_ids}}))
    print("Clientes recuperados:", clientes_list)  # Añadir para depuración
    
    # Renderizar la plantilla
    return render(request, 'core/filter_clientes.html', {'clientes': clientes_list})


@mongo_login_required
def insert_producto(request):
    client = get_mongo_client(request)
    if not client:
        messages.error(request, 'Error al conectar a MongoDB.')
        return redirect('login')
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            db = client['ecommerce_db']
            producto_data = form.cleaned_data
            id_producto = producto_data['id_producto']
            # Verificar si el ID ya existe
            if db['productos'].find_one({'_id': id_producto}):
                messages.error(request, 'El ID ya existe. Por favor, elija otro.')
                return render(request, 'core/insert_producto.html', {'form': form})
            else:
                producto_data['_id'] = id_producto  
                del producto_data['id_producto']    
                producto_data['precio'] = Decimal128(str(producto_data['precio']))
                db['productos'].insert_one(producto_data)
                messages.success(request, 'Producto insertado correctamente.')
                return redirect('home')
    else:
        form = ProductoForm()
    return render(request, 'core/insert_producto.html', {'form': form})