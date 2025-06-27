from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import *
import pymongo
from datetime import datetime, timedelta, timezone
from functools import wraps
import uuid
from bson.decimal128 import Decimal128
from bson import ObjectId

# Función auxiliar para obtener el cliente de MongoDB
def get_mongo_client(request):
    """
    Propósito: Establece una conexión con MongoDB utilizando las credenciales almacenadas en la sesión del usuario.
    
    Funcionamiento:
    - Recupera el nombre de usuario y contraseña de la sesión del request.
    - Si alguna de las credenciales no está presente, retorna None.
    - Construye una URI de conexión con formato mongodb+srv:// usando las credenciales.
    - Intenta establecer la conexión con pymongo.MongoClient y verifica su validez con server_info().
    - Retorna el cliente si la conexión es exitosa; de lo contrario, retorna None.

    """
    username = request.session.get('mongo_username')
    password = request.session.get('mongo_password')
    if not username or not password:
        return None
    uri = f"mongodb+srv://{username}:{password}@cluster0.cc5wfzr.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    try:
        client = pymongo.MongoClient(uri)
        client.server_info()  # Verificar la conexión
        return client
    except:
        return None

# Decorador para proteger vistas que requieren autenticación
def mongo_login_required(view_func):
    """
    Propósito: Asegura que las vistas solo sean accesibles por usuarios autenticados con MongoDB.

    Funcionamiento:
    - Verifica si mongo_username y mongo_password están en la sesión.
    - Si faltan, muestra un mensaje de error y redirige al login.
    - Si están presentes, permite la ejecución de la vista decorada.

    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if 'mongo_username' not in request.session or 'mongo_password' not in request.session:
            messages.error(request, 'Por favor, ingrese las credenciales de MongoDB.')
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper

# Vista para manejar el inicio de sesión
def login_view(request):
    """
    Propósito: Permite a los usuarios autenticarse con sus credenciales de MongoDB.

    Funcionamiento:
    - Si el método es POST:
      - Procesa el formulario MongoLoginForm.
      - Si es válido, extrae username y password, los almacena en la sesión.
      - Usa get_mongo_client para verificar las credenciales.
      - Si la conexión falla, muestra un mensaje de error; si es exitosa, redirige a home.
    - Si el método es GET:
      - Renderiza el formulario de login vacío.

    """
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

# Vista principal de la aplicación
@mongo_login_required
def home_view(request):
    """
    Propósito: Muestra la página principal con listas de clientes y pedidos.

    Funcionamiento:
    - Obtiene el cliente de MongoDB con get_mongo_client.
    - Si falla la conexión, redirige al login con un mensaje de error.
    - Accede a la base de datos ecommerce_db.
    - Recupera todos los documentos de las colecciones clientes y pedidos.
    - Renderiza home.html con los datos obtenidos.

    Sentencia MongoDB:
    - db['clientes'].find(): Recupera todos los clientes.
    - db['pedidos'].find(): Recupera todos los pedidos.

    """
    client = get_mongo_client(request)
    if not client:
        messages.error(request, 'Error al conectar a MongoDB.')
        return redirect('login')
    db = client['ecommerce_db']
    clientes = list(db['clientes'].find())
    pedidos = list(db['pedidos'].find())
    return render(request, 'core/home.html', {'clientes': clientes, 'pedidos': pedidos})

# Vista para insertar un nuevo cliente
@mongo_login_required
def insert_cliente(request):
    """
    Propósito: Permite agregar un nuevo cliente a la base de datos.

    Funcionamiento:
    - Obtiene el cliente de MongoDB.
    - Si falla, redirige al login.
    - Si el método es POST:
      - Procesa el formulario ClienteForm.
      - Si es válido, ajusta fecha_registro a solo fecha (sin hora) y lo inserta en clientes.
      - Redirige a home con mensaje de éxito.
    - Si el método es GET:
      - Renderiza el formulario vacío.

    Sentencia MongoDB:
    - db['clientes'].insert_one(cliente_data): Inserta un documento en la colección clientes.

    """
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

# Vista para insertar un nuevo pedido
@mongo_login_required
def insert_pedido(request):
    """
    Propósito: Permite agregar un nuevo pedido con cliente, productos y cantidades.

    Funcionamiento:
    - Obtiene el cliente de MongoDB y las listas de clientes y productos.
    - Prepara productos convirtiendo _id a id_producto.
    - Si el método es POST:
      - Procesa el formulario PedidoForm.
      - Calcula monto_total sumando precio * cantidad de productos seleccionados.
      - Construye el documento del pedido y lo inserta en pedidos.
      - Redirige a home con mensaje de éxito.
    - Si el método es GET:
      - Renderiza el formulario con opciones de clientes y productos.

    Sentencia MongoDB:
    - db['pedidos'].insert_one(pedido): Inserta un pedido con subdocumentos de productos.

    """
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

# Vista para filtrar clientes del último año
@mongo_login_required
def filter_clientes_ultimo_ano(request):
    """
    Propósito: Muestra clientes registrados en el último año.

    Funcionamiento:
    - Calcula la fecha de hace un año (hoy - 365 días).
    - Construye una consulta con $gte para fechas mayores o iguales.
    - Renderiza los clientes filtrados.

    Sentencia MongoDB:
    - db['clientes'].find({'fecha_registro': {'$gte': hace_un_ano}}):
      Filtra clientes cuya fecha_registro sea >= hace_un_ano.

    """
    client = get_mongo_client(request)
    db = client['ecommerce_db']
    hace_un_ano = datetime.now() - timedelta(days=365)
    query = {'fecha_registro': {'$gte': hace_un_ano}}
    clientes_list = list(db['clientes'].find(query))
    return render(request, 'core/filter_clientes.html', {'clientes': clientes_list})

# Vista para filtrar pedidos con monto > 100
@mongo_login_required
def filter_pedidos_monto_100(request):
    """
    Propósito: Muestra pedidos con monto total superior a $100.

    Funcionamiento:
    - Construye una consulta con $gt para montos mayores a 100.
    - Renderiza los pedidos filtrados.

    Sentencia MongoDB:
    - db['pedidos'].find({'monto_total': {'$gt': 100}}):
      Filtra pedidos con monto_total > 100.
    """
    client = get_mongo_client(request)
    db = client['ecommerce_db']
    query = {'monto_total': {'$gt': 100}}
    pedidos_list = list(db['pedidos'].find(query))
    return render(request, 'core/filter_pedidos.html', {'pedidos': pedidos_list})

# Vista para filtrar clientes con email de Gmail
@mongo_login_required
def filter_clientes_gmail(request):
    """
    Propósito: Muestra clientes con email en el dominio gmail.com.

    Funcionamiento:
    - Usa $regex para buscar emails que terminen en @gmail.com (insensible a mayúsculas).
    - Renderiza los clientes filtrados.

    Sentencia MongoDB:
    - db['clientes'].find({'email': {'$regex': '@gmail\\.com$', '$options': 'i'}}):
      Busca emails con dominio exacto @gmail.com.

    """
    client = get_mongo_client(request)
    db = client['ecommerce_db']
    query = {'email': {'$regex': '@gmail\\.com$', '$options': 'i'}}
    clientes_list = list(db['clientes'].find(query))
    return render(request, 'core/filter_clientes.html', {'clientes': clientes_list})

# Vista para filtrar pedidos de 2023
@mongo_login_required
def filter_pedidos_2023(request):
    """
    Propósito: Muestra pedidos realizados en 2023.

    Funcionamiento:
    - Usa $gte y $lt para definir el rango de fechas de 2023.
    - Renderiza los pedidos filtrados.

    Sentencia MongoDB:
    - db['pedidos'].find({'fecha_pedido': {'$gte': datetime(2023, 1, 1), '$lt': datetime(2024, 1, 1)}}):
      Filtra pedidos entre 01/01/2023 y 31/12/2023.

    """
    client = get_mongo_client(request)
    db = client['ecommerce_db']
    query = {'fecha_pedido': {'$gte': datetime(2023, 1, 1), '$lt': datetime(2024, 1, 1)}}
    pedidos_list = list(db['pedidos'].find(query))
    return render(request, 'core/filter_pedidos.html', {'pedidos': pedidos_list})

# Vista para filtrar pedidos con producto ID 101
@mongo_login_required
def filter_pedidos_producto_101(request):
    """
    Propósito: Muestra pedidos que contienen el producto con ID '101'.

    Funcionamiento:
    - Usa notación de punto para buscar en el array productos.
    - Renderiza los pedidos filtrados.

    Sentencia MongoDB:
    - db['pedidos'].find({'productos.producto_id': '101'}):
      Busca en subdocumentos productos donde producto_id sea '101'.

    """
    client = get_mongo_client(request)
    db = client['ecommerce_db']
    query = {'productos.producto_id': '101'}  
    pedidos_list = list(db['pedidos'].find(query))
    return render(request, 'core/filter_pedidos.html', {'pedidos': pedidos_list})

# Vista para filtrar clientes con pedidos > $500 en el último año
@mongo_login_required
def filter_clientes_pedidos_500_ultimo_ano(request):
    """
    Propósito: Muestra clientes con pedidos > $500 en el último año.

    Funcionamiento:
    - Calcula la fecha de hace un año en UTC.
    - Filtra pedidos con monto_total > 500 y fecha_pedido >= hace_un_ano.
    - Extrae cliente_ids como ObjectId y busca clientes con $in.
    - Renderiza los clientes filtrados.

    Sentencia MongoDB:
    - db['pedidos'].find({'monto_total': {'$gt': 500}, 'fecha_pedido': {'$gte': hace_un_ano}}):
      Filtra pedidos por monto y fecha.
    - db  db['clientes'].find({'_id': {'$in': cliente_ids}}):
      Busca clientes por IDs obtenidos.

    """
    client = get_mongo_client(request)
    if not client:
        messages.error(request, 'Error al conectar a MongoDB.')
        return redirect('login')
    
    db = client['ecommerce_db']
    hace_un_ano = datetime.now(timezone.utc) - timedelta(days=365)
    pedidos_filtrados = db['pedidos'].find({
        'monto_total': {'$gt': 500},
        'fecha_pedido': {'$gte': hace_un_ano}
    })
    pedidos_list = list(pedidos_filtrados)
    cliente_ids = [ObjectId(p['cliente_id']) for p in pedidos_list]
    clientes_list = list(db['clientes'].find({'_id': {'$in': cliente_ids}}))
    return render(request, 'core/filter_clientes.html', {'clientes': clientes_list})

# Vista para insertar un nuevo producto
@mongo_login_required
def insert_producto(request):
    """
    Propósito: Permite agregar un producto con un ID único.

    Funcionamiento:
    - Si el método es POST:
      - Procesa el formulario ProductoForm.
      - Verifica si id_producto ya existe.
      - Si no existe, usa id_producto como _id y convierte precio a Decimal128.
      - Inserta el producto y redirige a home.
    - Si el método es GET:
      - Renderiza el formulario.

    Sentencia MongoDB:
    - db['productos'].find_one({'_id': id_producto}): Verifica existencia.
    - db['productos'].insert_one(producto_data): Inserta el producto.

    """
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