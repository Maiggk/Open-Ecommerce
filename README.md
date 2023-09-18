# Open-Ecommerce
Sitio Ecommerce realizado en Django 4, con funciones simples y poderosas para pequeños proyectos. Sientete libre de usarlo y experimentar

Python Ecommerce site with some basic-intermedium functionalities to experience with. You can use it as base for more ambitius proyects






## Features

- Catalogo de productos y detalles de articulos
- Pasarela de pago
- Filtrado de datos
- Historial de compra con descarga de ticket
- Perfil de aministracion con los datos de usuario


## Environment Variables

Para iniciar correctamente la aplicacion se necesita que se proporcionen las variables de entorno en el archivo `.env` Dentro de la carpeta raiz del proyecto

## Deployment

Para inicializar el proyecto hay que realizar un par de pasos

0.- Instalacion de dependencias
```bash
  > pip install -r requirements.txt
```

1.- Crear la base de datos

```bash
  > py manage.py makemigrations
  > py manage.py migrate
```
2.- Creacion de cuenta de administrador

```bash
  > py manage.py createsuperuser
```
3.- Correr la aplicacion
```bash
  > py manage.py runserver
```
opcionalmente inicia en el puerto/ip que desees
```bash
  > py manage.py runserver 192.168.0.10:70000
```

## Screenshots
### Main
![Main Page](https://i.postimg.cc/D0XwhLJv/main-page.png)
### Productos
![Productos](https://i.postimg.cc/SKgsfybh/productos.png)
### Detalle
![Productos](https://i.postimg.cc/1tT3bJz7/producto-detalle.png)
