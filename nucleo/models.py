from distutils.command.upload import upload
from sqlite3 import Timestamp
from django.db import models
from django.conf import settings
from django.db import models
from django.shortcuts import reverse
from django_countries.fields import CountryField
from django.utils.html import mark_safe
from django.templatetags.static import static

MARCA = (
    ('CP', 'Cuidado con el perro'),
    ('MH', 'H&M'),
    ('GS', 'Guess'),
    ('F2', 'Forever 21'),
    ('PB', 'Pull & Bear'),
)

CATEGORY = (
    ('PA', 'Pantalones'),
    ('CAM', 'Camisas'),
    ('CAL', 'Calzado'),
    ('PLA', 'Playeras'),
    ('ACC', 'Accesorios'),
)

LABEL = (
    ('N', 'Nuevo'),
    ('V', 'Mas vendido'),
    ('T', 'Tendencia'),
    ('U', 'Ultimas Existencias'),
)

ESTADO_ENVIO = (
    ('A', 'Activo'),
    ('C', 'Cancelado'),
    ('R', 'Reembolso'),
    ('P', 'Proceso'),
    ('E', 'Enviado')
)


class Item(models.Model) :
    item_name = models.CharField(max_length=100)
    price = models.FloatField()
    discount_price = models.FloatField(blank=True, null=True)
    category = models.CharField(choices=CATEGORY, max_length=3)
    company = models.CharField(choices=MARCA, max_length=2,default='AR')
    label = models.CharField(choices=LABEL, max_length=2)
    description = models.TextField()
    indications = models.TextField(max_length="700",default="",null=True)
    date_created = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    active = models.BooleanField(default=True)
    cve_cat_producto = models.BigIntegerField(null=True,blank=True)
    porcentaje_iva = models.IntegerField(null=True, blank=True, default=0)
    porcentaje_ieps = models.IntegerField(null=True, blank=True, default=0)


    def __str__(self):
        return self.item_name

    def get_absolute_url(self):
        return reverse("nucleo:producto", kwargs={
            "pk" : self.pk

        })

    # def get_add_to_cart_url(self) :
    #     return reverse("nucleo:add-to-cart", kwargs={
    #         "pk" : self.pk
    #     })

    def get_remove_from_cart_url(self) :
        return reverse("nucleo:remove-from-cart", kwargs={
            "pk" : self.pk
        })

    def get_porcentaje_descuento(self):
        if self.discount_price:
            try:
                discount = 100-(int(self.discount_price * 100) / self.price)
                if discount < 0:
                    return 0
                else:
                    return round(discount,1)
            except ZeroDivisionError as zerodiv:
                return 0
        else:
            return 0

    def get_image_product(self):
        if self.itemimage_set.all():
            return "/"+self.itemimage_set.first().image.name
        else:
            return static('img/ropa-default.png')

    def get_final_price(self):
        if self.discount_price:
            return self.discount_price
        else:
            return self.price

    def get_final_price_tax(self):
        if self.discount_price:
            total_ieps = (self.discount_price * (self.porcentaje_ieps / 100))
            total_iva = (self.discount_price * (self.porcentaje_iva / 100))
            return round(self.discount_price + total_iva + total_ieps,2)
        else:
            total_ieps = (self.price * (self.porcentaje_ieps / 100))
            total_iva = (self.price * (self.porcentaje_iva/100))
            return round(self.price + total_iva + total_ieps,2)

    def get_qty_stock(self):#TODO: VERIFICAR EL STOCK EN ALMACEN 
        try:
            return 50 #STOCK ARBITRARIO {CAMBIAR}
        except Exception as e:
            import random
            print(f"DB Error Timeout: {e}")
            return 0

class ItemImage(models.Model):
    altDescription = models.TextField(max_length='100')
    image = models.ImageField(upload_to='static/img/product', null=True)
    item = models.ForeignKey(Item, on_delete=models.CASCADE,null=True, blank=True)

    def __str__(self):
        return f"{self.item.item_name}"
class OrderItem(models.Model) :
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    ordered = models.BooleanField(default=False)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    porcentaje_iva = models.IntegerField(null=True, blank=True, default=0)
    porcentaje_ieps = models.IntegerField(null=True, blank=True, default=0)
    discount_price = models.FloatField(blank=True, null=True, default=0)
    reference_price = models.IntegerField(default=1)


    def __str__(self):
        return f"{self.quantity} of {self.item.item_name}"

    def get_total_item_price(self):
        if self.item.price > 0:
            return self.quantity * self.item.price
        else:
            return 0

    def get_discount_item_price(self):
        try:
            return self.quantity * self.item.discount_price
        except BaseException as noneExist:
            # return self.quantity * self.item.price
            return self.get_total_item_price()

    def get_amount_saved(self):
        return self.get_total_item_price() - self.get_discount_item_price()

    def get_final_price(self):
        if self.item.discount_price and self.item.discount_price > 0:
            return self.get_discount_item_price()
        return self.get_total_item_price()

    def desglose_item(self,historico = False):
        cantidad = self.quantity
        precio = 0
        suma = 0
        descuento = 0
        subtotal = 0
        iva = 0
        ieps = 0
        impuesto_iva = 0
        impuesto_ieps = 0
        impuesto_total = 0
        total_final = 0
        # print("Producto:{}".format(self.item.item_name))
        # print("Cantidad:{}".format(cantidad))

        if historico == False:
            precio = self.item.price
            descuento = self.item.get_porcentaje_descuento()
            iva = self.item.porcentaje_iva
            ieps = self.item.porcentaje_ieps
            # print("Precio:{}".format(precio))
            # print("Descuento:{}".format(descuento))
            # print("Iva:{}".format(iva))
            # print("Ieps:{}".format(ieps))
        else:
            precio = self.reference_price
            # print("Precio:{}".format(precio))

            if self.discount_price and self.discount_price > 0:
                try:
                    discount = 100 - round(((self.discount_price * 100) / self.reference_price),2)
                    if discount < 0:
                        descuento = 0
                    else:
                        descuento = round(discount,2)
                except ZeroDivisionError as zerodiv:
                    descuento = 0
            else:
                descuento = 0
            iva = self.porcentaje_iva
            ieps = self.porcentaje_ieps
            # print("Descuento:{}".format(descuento))
            # print("Iva:{}".format(iva))
            # print("Ieps:{}".format(ieps))

        suma = (cantidad * precio)
        subtotal = (suma - (suma * (descuento / 100)))
        impuesto_iva = (subtotal * (iva / 100))
        impuesto_ieps = (subtotal * (ieps / 100))
        impuesto_total = (impuesto_iva + impuesto_ieps)
        total_final = (subtotal + impuesto_total)
        # print("Suma:{}".format(suma))
        # print("Subtotal:{}".format(subtotal))
        # print("Total ieps:{}".format(impuesto_ieps))
        # print("Total iva:{}".format(impuesto_iva))
        # print("Total impuestos:{}".format(impuesto_total))
        # print("Total final:{}".format(total_final))
        # print("-----------------------------")
        # print("")

        context = {
            "cantidad":cantidad,
            "precio":precio,
            "descuento":descuento,
            "subtotal":subtotal,
            "impuesto_iva":impuesto_iva,
            "impuesto_ieps":impuesto_ieps,
            "total_final":total_final,
        }
        return context

class Order(models.Model) :
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    items = models.ManyToManyField(OrderItem)
    start_date = models.DateTimeField(auto_now_add=True)
    ordered_date = models.DateTimeField(null=True)
    ordered = models.BooleanField(default=False)
    ship_to = models.CharField(max_length=300, blank=True, null=True, default="")
    dispatched = models.BooleanField(default=False)
    guia_envio = models.CharField(max_length=300, blank=True, null=True, default="")
    paqueteria = models.CharField(max_length=100, blank=True, null=True, default="")
    estatus_envio = models.CharField(choices=ESTADO_ENVIO, max_length=50, blank=True, null=True, default="")
    company = models.CharField(choices=MARCA, max_length=2,default='AR')
    entrega_estimada = models.DateField(blank=True, null=True)
    costo_envio = models.FloatField(blank=True, null=True)
    order_total = models.FloatField(blank=True, null=True)

    def __str__(self):
        return self.user.username

    def get_total_price(self):
        total = 0
        for order_item in self.items.all():
            total += order_item.get_final_price()
        return total

    def get_total_items(self):
        total_qry = 0
        for order_item in self.items.all():
            total_qry += order_item.quantity
        return total_qry

    def desglose_orden(self):
        acumulado_iva = 0
        acumulado_ieps = 0
        total_orden = 0

        for producto in self.items.all():
            cantidad = producto.quantity
            precio = producto.item.price
            descuento = producto.item.get_porcentaje_descuento()
            iva = producto.item.porcentaje_iva
            ieps = producto.item.porcentaje_ieps
            suma = (cantidad * precio)
            subtotal = (suma - (suma * (descuento / 100)))
            impuesto_iva = (subtotal * (iva/100))
            impuesto_ieps = (subtotal * (ieps/100))
            impuesto_total = (impuesto_iva + impuesto_ieps)
            total_final = (subtotal + impuesto_total)
            acumulado_iva += impuesto_iva
            acumulado_ieps += impuesto_ieps
            total_orden += total_final
            pass
        context = {
            'acumulado_iva':acumulado_iva,
            'acumulado_ieps':acumulado_ieps,
            'total_orden':total_orden,
        }
        return context
class CheckoutAddress(models.Model):
    # user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    street_address = models.CharField(max_length=100)
    apartment_address = models.CharField(max_length=100,null=True,blank=True)
    settlement_name = models.CharField(max_length=100) #colonia
    country = CountryField(multiple=False)
    zip = models.CharField(max_length=100)
    phone = models.CharField(max_length=50, blank=True, null=True)
    rfc = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"{self.street_address}, {self.settlement_name} CP: {self.zip}, Tel: {self.phone}"

class Payment(models.Model):
    payment_ref_id = models.CharField(max_length=100)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,blank=True,null=True)
    amount = models.FloatField()
    timestamp = models.DateField(auto_now_add=True)
    order = models.ForeignKey(Order,null=True, on_delete=models.SET_NULL)
    payment_type = models.CharField(max_length=30,blank=True,null=True)
    currency = models.CharField(max_length=10,blank=True,null=True)

    def __str__(self):
        return self.payment_type + ' ID:' + self.payment_ref_id
