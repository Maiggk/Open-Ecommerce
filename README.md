# Open-Ecommerce
Sitio Ecommerce realizado en Django 4, con funciones simples y poderosas para pequeños proyectos. Sientete libre de usarlo y experimentar

Python Ecommerce site with some basic-intermedium functionalities to experience with. You can use it as base for more ambitius proyects






## Features

- Catalogo de productos y detalles de articulos
- Pasarela de pago
- Filtrado de datos
- Historial de compra con descarga de ticket
- Perfil de aministracion con los datos de usuario


## Deployment

Para inicializar el proyecto hay que realizar un par de pasos

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

## Environment Variables

Para iniciar correctamente la aplicacion se necesita que se proporcionen las variables de entorno en el archivo `.env` Dentro de la carpeta raiz del proyecto

## Screenshots
### Main
![Main Page](https://1drv.ms/i/s!ApWHidi6zWHjimqibb6lr4zrfSW8?e=E8OnJx)
### Productos
![Productos](https://1drv.ms/i/s!ApWHidi6zWHjimtC9EXlghRumGxb?e=PEmEu2)
### Detalle
![Productos](https://1drv.ms/i/s!ApWHidi6zWHjimjINL4MoEstuGsr?e=8rYeNt)
