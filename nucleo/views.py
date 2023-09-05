import os,datetime,locale,re
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
from django.core.mail import send_mail
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import *
from django.http import FileResponse, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, View,TemplateView
from .forms import CheckoutForm, UserProfileForm
from django.db.models import Q
from django.template.loader import get_template
import stripe
from django.contrib.auth import get_user_model
from fpdf import FPDF, HTMLMixin
from postalcodes_mexico.postalcodes_mexico import places
from .models import (
    Item,
    Order,
    OrderItem,
    CheckoutAddress,
    Payment,
    CATEGORY,
    MARCA,
    ESTADO_ENVIO
)
import requests
stripe.api_key = settings.STRIPE_KEY
PAYPAL_ID = settings.PAYPAL_ID



class HomeView(ListView):
    model = Item
    template_name = "home.html"
    paginate_by = 9
    queryset = Item.objects.filter(active = True)

    def dispatch(self, request, *args, **kwargs):
        self.category = kwargs.pop('filter', None)
        self.company = self.category
        self.minprice = kwargs.pop('minprice', None)
        self.maxprice = kwargs.pop('maxprice', None)
        return super(HomeView, self).dispatch(request,*args, **kwargs)

    def get_queryset(self):
        qs = super(HomeView, self).get_queryset()
        query_search = self.request.GET.get("q")
        if self.company or self.category:
            qs = qs.filter(Q(company=self.company) | Q(category=self.category))
        elif self.minprice and self.maxprice:
            qs = qs.filter(price__range = (self.minprice,self.maxprice) )
        elif query_search:
            qs = qs.filter(item_name__icontains = query_search )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        discount_items = Item.objects.filter(discount_price__gt=0,active=True)[0:5]
        rand_items = Item.objects.filter(active=True).order_by('?')[:12]
        arrayMasConsultados = []

        if rand_items.count() > 12:
            for index in range(0,11,3):
                arrayAcum = [rand_items[index], rand_items[index+1], rand_items[index+2]]
                arrayMasConsultados.append(arrayAcum)
        else:
            for index in range(0,rand_items.count()):
                arrayMasConsultados.append([rand_items[index]])
        context['discount_items'] = discount_items
        context['categorias'] = CATEGORY
        context['marcas'] = MARCA
        context['mas_vistos'] = arrayMasConsultados

        if self.request.user.is_authenticated:
            order = Order.objects.filter(user=self.request.user,ordered=False).first()
            if order:
                context['order_cart'] = order
            else:
                context['order_cart'] = None
        return context

class ProductView(DetailView):
    model = Item
    template_name = "product.html"

    def get_context_data(self, *args, **kwargs):
        context = super(ProductView,self).get_context_data(*args, **kwargs)
        context['categorias'] = CATEGORY
        return context

class OrderSummaryView(LoginRequiredMixin, View):
    model = Item
    template_name = "order_summary.html"

    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {
                'object' : order,
                'categorias': CATEGORY,
            }
            return render(self.request, 'order_summary.html', context)
        except ObjectDoesNotExist:
            messages.error(self.request, "No hay productos en el carrito")
            return redirect("/")

class CheckoutView(View):

    def get(self, *args, **kwargs):
        zip = None
        if self.request.user.is_authenticated:
            address = CheckoutAddress.objects.filter(user=self.request.user).first()
            if address:
                zip = places(address.zip)
                form = CheckoutForm(
                    initial={
                        'street_address': address.street_address,
                        'apartment_address': address.apartment_address,
                        'settlement_name': address.settlement_name,
                        'zip': address.zip,
                        'phone': address.phone,
                        'rfc': address.rfc,
                    })
            else:
                form = CheckoutForm()
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {'form': form, 'pedido': order, 'settlement_places': zip}
        else:
            form = CheckoutForm()
            context = {'form': form, 'pedido': None, 'settlement_places': None}
        context['categorias'] = CATEGORY
        context['PAYPAL_ID'] = PAYPAL_ID
        return render(self.request, 'checkout.html',context)

    def post(self, *args, **kwargs):
        if self.request.headers.get('X-Requested-With') != 'XMLHttpRequest': # Ajax?
            form = CheckoutForm(self.request.POST or None)

            try:
                order = Order.objects.get(user=self.request.user, ordered=False)
                if form.is_valid():
                    street_address = form.cleaned_data.get('street_address')
                    apartment_address = form.cleaned_data.get('apartment_address')
                    country = form.cleaned_data.get('country')
                    zip = form.cleaned_data.get('zip')
                    save_info = form.cleaned_data.get('save_info')
                    settlement_name = form.cleaned_data.get('settlement_name')
                    phone = form.cleaned_data.get('phone')
                    rfc = form.cleaned_data.get('rfc')
                    payment_option = form.cleaned_data.get('payment_option')

                    if save_info and (self.request.user.checkoutaddress == None):
                        checkout_address = CheckoutAddress(
                            user=self.request.user,
                            street_address=street_address,
                            apartment_address=apartment_address,
                            country=country,
                            zip=zip,
                            settlement_name=settlement_name,
                            phone=phone,
                            rfc=rfc,
                        )
                        checkout_address.save()
                        order.checkout_address = checkout_address
                        order.save()
                    else:
                        address = CheckoutAddress.objects.filter(user=self.request.user).first()
                        address.street_address = form.cleaned_data.get('street_address')
                        address.apartment_address = form.cleaned_data.get('apartment_address')
                        address.zip = form.cleaned_data.get('zip')
                        address.settlement_name = form.cleaned_data.get('settlement_name')
                        address.phone = form.cleaned_data.get('phone')
                        address.rfc = form.cleaned_data.get('rfc')
                        address.save()

                    try:
                        address.save()
                    except Exception as e:
                        messages.error(self.request,f"Error al crear usuario")
                        print("Excepcion create user")
                        return redirect('nucleo:checkout')

                    if payment_option == 'S':
                        return redirect('nucleo:payment', payment_option='stripe')
                    elif payment_option == 'P':
                        return redirect('nucleo:payment', payment_option='paypal')
                    else:
                        messages.warning(self.request, "Metodo de pago no valido")
                        return redirect('nucleo:checkout')
                else:
                    messages.warning(self.request, "Chekout Fallido")
                    address = CheckoutAddress.objects.filter(user=self.request.user).first()
                    zip = None
                    if address != None:
                        zip = places(address.zip)
                    order = Order.objects.get(user=self.request.user, ordered=False)
                    context = {'form': form, 'pedido': order, 'settlement_places': zip,'categorias':CATEGORY}
                    return render(self.request, 'checkout.html', context)
            except ObjectDoesNotExist:
                messages.error(self.request, "No hay una orden activa!")
                return redirect("nucleo:order-summary")
        else:
            if self.request.POST.get('action') == 'getZip':
                zipSettlements = places(self.request.POST.get('zip'))
                cntxAjax = {
                    'status': 'success',
                    'places': zipSettlements,
                }
                return JsonResponse(cntxAjax, safe=True)

class PaymentView(View):

    def get(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        YOUR_DOMAIN = 'http://localhost:8000'
        jsonProductos = []
        for product in order.items.all():
            jsonProductos.append({
                # Provide the exact Price ID (for example, pr_1234) of the product you want to sell
                'price_data': {
                    'currency': 'mxn',
                    'unit_amount':int(product.item.get_final_price_tax() * 100),
                    'product_data': {
                        'name': product.item.item_name
                    }
                },
                'quantity': product.quantity,
            })

        costo_envio = 0
        leyenda_envio = "Envio Gratis"
        if (order.get_total_price() < 2000):
            costo_envio = (500 * 100)
            leyenda_envio = "Envio a todo México"


        shipping = []
        shipping.append({
            "shipping_rate_data": {
                "type": "fixed_amount",
                "fixed_amount": {
                    "amount": costo_envio,
                    "currency": "mxn"
                },
                "display_name": leyenda_envio,
            },
        })

        checkout_session = stripe.checkout.Session.create(
            shipping_options=shipping,
            line_items=jsonProductos,
            mode='payment',
            success_url=YOUR_DOMAIN + '/payment_success/' + str(order.pk) +
            '/{CHECKOUT_SESSION_ID}/' + 'STRIPE',
            cancel_url=YOUR_DOMAIN + '/checkout/',
        )
        context = {
            'order': order,
            'stripe_key':checkout_session.id
        }
        return redirect(checkout_session.url, code=303)

    def post(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        token = self.request.POST.get('stripeToken')
        amount = int(order.get_total_price() * 100)  #cents

        try:
            charge = stripe.Charge.create(
                amount=amount,
                currency="usd",
                source=token
            )

            # create payment
            payment = Payment()
            payment.stripe_id = charge['id']
            payment.user = self.request.user
            payment.amount = order.get_total_price() + order.desglose_orden()['acumulado_iva'] + order.desglose_orden()['acumulado_ieps']
            payment.save()

            # assign payment to order
            order.ordered = True
            order.ordered_date = datetime.date.today()
            order.payment = payment
            order.save()

            messages.success(self.request, "Success make an order")
            return redirect('/')

        except stripe.error.CardError as e:
            body = e.json_body
            err = body.get('error', {})
            messages.error(self.request, f"{err.get('message')}")
            return redirect('/')

        except stripe.error.RateLimitError as e:
            # Too many requests made to the API too quickly
            messages.error(self.request, "To many request error")
            return redirect('/')

        except stripe.error.InvalidRequestError as e:
            # Invalid parameters were supplied to Stripe's API
            messages.error(self.request, "Invalid Parameter")
            return redirect('/')

        except stripe.error.AuthenticationError as e:
            # Authentication with Stripe's API failed
            # (maybe you changed API keys recently)
            messages.error(self.request, "Authentication with stripe failed")
            return redirect('/')

        except stripe.error.APIConnectionError as e:
            # Network communication with Stripe failed
            messages.error(self.request, "Network Error")
            return redirect('/')

        except stripe.error.StripeError as e:
            # Display a very generic error to the user, and maybe send
            # yourself an email
            messages.error(self.request, "Something went wrong")
            return redirect('/')

        except Exception as e:
            # Something else happened, completely unrelated to Stripe
            messages.error(self.request, "Not identified error")
            return redirect('/')

class SuccessPaymentView(LoginRequiredMixin,TemplateView):

    def get(self,request, *args, **kwargs):
        clave_success = kwargs.get('key_order', None)
        stripe_session = kwargs.get('session_id', None)
        metodo_pago = kwargs.get('payment_type', None)
        if clave_success:
            try:
                order = Order.objects.get(pk=clave_success,user=self.request.user)
                payment = Payment.objects.filter(payment_ref_id=stripe_session,user=self.request.user)
                if len(payment) > 0 or order.ordered == True:
                    return render(self.request, "checkout_success.html", {'order':order})

            except:
                return render(self.request,"checkout_success.html",None)

            envioCorreoVenta(request,order)

            # create payment
            payment = Payment()
            payment.payment_ref_id = stripe_session
            payment.user = self.request.user
            payment.amount = order.get_total_price() + order.desglose_orden()['acumulado_iva'] + order.desglose_orden()['acumulado_ieps']
            payment.currency = 'MXN'
            payment.order = order
            payment.payment_type = metodo_pago
            payment.save()

            # assign payment to order
            costo_envio = 0
            if order.get_total_price() < 2000:
                costo_envio = 500

            order.ordered = True
            order.ordered_date = datetime.datetime.now()
            order.entrega_estimada = datetime.datetime.now() + timedelta(days=15)
            order.order_total = order.get_total_price()
            order.costo_envio = costo_envio
            order.estatus_envio = 'E'
            order.ship_to = f"{request.user.checkoutaddress.street_address}, {request.user.checkoutaddress.settlement_name} CP: {request.user.checkoutaddress.zip}, Tel: {request.user.checkoutaddress.phone}"
            for item in order.items.filter(user=self.request.user, ordered=False): #nucleo_orderitem Table
                item.reference_price = item.item.price
                item.discount_price = item.item.discount_price
                item.porcentaje_iva = item.item.porcentaje_iva
                item.porcentaje_ieps = item.item.porcentaje_ieps
                item.ordered = True
                item.save()
            order.save()
            context = {
                'order':order
            }
        return render(self.request, "checkout_success.html",context)

class ProfileUserView(LoginRequiredMixin,View):

    def get(self, *args, **kwargs):
        context = {}
        User = get_user_model()
        user = User.objects.get(pk=self.request.user.pk)
        history = Payment.objects.filter(
            user=self.request.user).order_by('-timestamp')
        context['user'] = user

        address = CheckoutAddress.objects.filter(user=user).first()
        zip = None
        if address:
            if address.zip != '':
                zip = places(address.zip)
            # zip = places(address.zip)
            form = UserProfileForm(
                initial={
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'street_address': address.street_address,
                    'settlement_name': address.settlement_name,
                    'phone': address.phone,
                    'rfc': address.rfc,
                    # 'apartment_address': address.apartment_address,
                    'zip': address.zip,
                })
        else:
            form = UserProfileForm(initial={
                'first_name': user.first_name,
                'last_name': user.last_name,
            })
        context = {
            'form': form,
            'historial': history,
            'settlement_places': zip,
            'categorias': CATEGORY
        }
        return render(self.request, 'account/profile_user.html',context)

    def post(self, *args, **kwargs):
        if self.request.headers.get('X-Requested-With') != 'XMLHttpRequest':
            form = UserProfileForm(self.request.POST or None)
            address_user = CheckoutAddress.objects.get(user=self.request.user)
            try:
                if form.is_valid():
                    User = get_user_model()
                    user = User.objects.get(pk=self.request.user.pk)
                    user.first_name = form.cleaned_data.get('first_name')
                    user.last_name = form.cleaned_data.get('last_name')

                    try:
                        address_user.street_address = form.cleaned_data.get('street_address')
                        address_user.apartment_address = form.cleaned_data.get('apartment_address')
                        address_user.zip = form.cleaned_data.get('zip')
                        address_user.settlement_name = form.cleaned_data.get('settlement_name')
                        address_user.phone = form.cleaned_data.get('phone')
                        address_user.rfc = form.cleaned_data.get('rfc')
                        address_user.save()
                    except CheckoutAddress.DoesNotExist:
                        address_user = CheckoutAddress(
                            user = user,
                            street_address = form.cleaned_data.get('street_address'),
                            apartment_address = form.cleaned_data.get('apartment_address'),
                            country = 'MX',
                            zip = form.cleaned_data.get('zip'),
                        )
                        address_user.save()

                    messages.success(self.request, "Perfil Actualizado!")
                    return redirect('nucleo:profile-user')
                else:
                    zip = None
                    if address_user.zip != '':
                        zip = places(address_user.zip)
                    return render(self.request, 'account/profile_user.html',{'form': form,'settlement_places':zip})

            except ObjectDoesNotExist:
                messages.error(self.request, "Eror al guardar datos de perfil")
                return redirect("nucleo:profile-user")
        else:
            if self.request.POST.get('action') == 'getZip':
                zipSettlements = places(self.request.POST.get('zip'))
                cntxAjax = {
                    'status': 'success',
                    'places': zipSettlements,
                }
                return JsonResponse(cntxAjax, safe=True)

@login_required
def add_to_cart(request, pk,qty = 1):
    item = get_object_or_404(Item, pk = pk )
    if item.get_qty_stock()<=0: # Validar Existencia
        messages.info(request, f"{item} no disponible, pronto volvera a ser resurtido.")
        return JsonResponse({"valid":False,"msj":f"{item} no disponible, pronto volvera a ser resurtido."}, status = 200)
    order_item, created = OrderItem.objects.get_or_create(
        item=item,
        user = request.user,
        ordered = False
    )

    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists() :
        order = order_qs[0]

        if order.items.filter(item__pk = item.pk).exists() :
            if qty == 1:
                order_item.quantity += qty
            else:
                order_item.quantity = qty
            order_item.save()
            return JsonResponse({"valid":True,"msj":f"{item} agregado al carrito"}, status = 200)
        else:
            order.items.add(order_item)
            return JsonResponse({"valid":True,"msj":f"{item} agregado al carrito"}, status = 200)
    else:
        order = Order.objects.create(user=request.user)
        order.items.add(order_item)
        return JsonResponse(
            {
                "valid": True,
                "msj": f"{item} agregado al carrito"
            }, status=200)

@login_required
def remove_from_cart(request, pk):
    item = get_object_or_404(Item, pk=pk )
    order_qs = Order.objects.filter(
        user=request.user,
        ordered=False
    )
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__pk=item.pk).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            order_item.delete()
            messages.info(request, "Item \""+order_item.item.item_name+"\" eliminado del carrito")
            return redirect("nucleo:order-summary")
        else:
            messages.info(request, "Este item no esta en tu carrito")
            return redirect("nucleo:order-summary")
    else:
        #add message doesnt have order
        messages.info(request, "Mo tienes una orden activa")
        return redirect("nucleo:order-summary")

@login_required
def reduce_quantity_item(request, pk):
    item = get_object_or_404(Item, pk=pk )
    order_qs = Order.objects.filter(
        user = request.user,
        ordered = False
    )
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__pk=item.pk).exists() :
            order_item = OrderItem.objects.filter(
                item = item,
                user = request.user,
                ordered = False
            )[0]
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
            else:
                order_item.delete()
            messages.info(request, "Carrito actualizado")
            return redirect("nucleo:order-summary")
        else:
            messages.info(request, "Este item no esta en tu carrito")
            return redirect("nucleo:order-summary")
    else:
        #add message doesnt have order
        messages.info(request, "No tienes una orden activa")
        return redirect("nucleo:order-summary")

def envioCorreoVenta(request,order):
    context = { 'order':order}
    message = get_template('checkout_success.html').render(context)
    send_mail(
        'Recibo de compra',
        'Recibo de compra',
        settings.EMAIL_HOST_USER,
        [],
        html_message=message)

@login_required
def getDetailOrder(request,or_id):

    if request.method == "POST":
        dataOrder = []
        dataOrderDet = []
        payment = Payment.objects.get(user=request.user,pk=or_id)
        order = Order.objects.get(user=request.user, pk=payment.order.pk)
        for orderItem in payment.order.items.all():
            dataOrderDet.append({
                'itemPrice': orderItem.reference_price,
                'itemName': orderItem.item.item_name,
                'itemQty': orderItem.quantity,
                'desglose': orderItem.desglose_item(historico = True)
            })
        dataOrder = {
            'user':(request.user.username if request.user.get_full_name() == "" else request.user.get_full_name()),
            'clave_orden':f'{order.pk:07d}',
            'fecha_orden':(order.start_date).strftime("%d/%m/%Y"),
            'detalle': dataOrderDet,
            'totalPrice': order.get_total_price(),
            'direccionEnvio':order.user.checkoutaddress.street_address,
            'direccionAlterna':order.user.checkoutaddress.apartment_address,
            'estatusOrden': "Sin estatus" if order.estatus_envio == "" else dict(ESTADO_ENVIO).get(order.estatus_envio),
            'tipo_pago':('<i class="fa fa-solid fa-credit-card"></i> TARJETA' if order.payment_set.first().payment_type == 'STRIPE' else '<i class="fa fa-brands fa-paypal"></i>'+order.payment_set.first().payment_type)
        }
        return JsonResponse({"valid":True,"data":dataOrder}, status = 200)

def renderPDF(request,order_key):
    payment_user = None
    if request.user.is_authenticated == False:
        return redirect('nucleo:home')
    try:
        payment_user = Payment.objects.get(user=request.user,pk=order_key)
    except Payment.DoesNotExist as err:
        return redirect('nucleo:profile-user')
    locale.setlocale( locale.LC_ALL, '' )

    pdf = PDF()
    pdf.set_title("Recibo de Compra Open-Ecommerce")
    pdf.payment_data = payment_user
    pdf.add_page()
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(10, 7, "#",1,0,'C')
    pdf.cell(90, 7, "Producto",1,0)
    pdf.cell(20, 7, "Cantidad",1,0)
    pdf.cell(20, 7, "Precio",1,0,'C')
    pdf.cell(25, 7, "Descuento",1,0,'C')
    pdf.cell(25, 7, "Subtotal",1,1,'C')
    pdf.set_font("helvetica", "", 8)
    idx = 1
    y_pos = 0
    total_iva = 0
    total_ieps = 0
    total_final = 0
    for item in payment_user.order.items.all():
        desglose = item.desglose_item(historico = True)
        total_iva += desglose['impuesto_iva']
        total_ieps += desglose['impuesto_ieps']
        total_final += desglose['total_final']
        pdf.cell(10, 7, str(idx) ,1,0,'C')
        pdf.cell(90,7, item.item.item_name,1,0)
        pdf.cell(20, 7, str(item.quantity),1,0,'C')
        pdf.cell(20, 7, str(item.reference_price),1,0,'R')
        pdf.cell(25, 7, str(desglose['descuento']), 1, 0, 'R')
        pdf.cell(25, 7, str(desglose['subtotal']),1,1,'R')
        idx += 1
        y_pos = pdf.get_y()
    pdf.ln()
    y_pos = pdf.get_y()
    pdf.set_xy(150,y_pos)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(25, 7, "IVA:",0,0,'R')
    pdf.cell(28, 7, str(locale.currency(total_iva, grouping=True))+' MXN',0,1,'R')
    pdf.set_xy(150,y_pos+5)
    pdf.cell(25, 7, "IEPS:",0,0,'R')
    pdf.cell(28, 7, str(locale.currency(total_ieps, grouping=True))+' MXN',0,1,'R')
    pdf.set_xy(150,y_pos+10)
    pdf.cell(25, 7, "Total:",0,0,'R')
    pdf.cell(28, 7, str(locale.currency(total_final, grouping=True))+' MXN',0,1,'R')
    pdf.set_font("helvetica", "", 8)
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)))+'\\static\\file\\recibo_pago.pdf'
    pdf.output(path, 'F')

    return FileResponse(open(path, 'rb'), as_attachment=False, content_type='application/pdf')
    # return FileResponse(open(path, 'rb'), as_attachment=True, content_type='application/pdf')
class PDF(FPDF, HTMLMixin):
    payment_data = None

    def header(self):
        orderData = Order.objects.get(pk=self.payment_data.order.pk)
        userName = (orderData.user.username if orderData.user.get_full_name() == "" else orderData.user.get_full_name())
        font_size_header = 10
        emisor_pos = 60
        debug = 0
        metodo_pago = ('TARJETA' if orderData.payment_set.first().payment_type == 'STRIPE' else orderData.payment_set.first().payment_type)
        ## Emisor Info
        linePosY = 10
        self.image('static/img/ecommerce-website-square.jpg', 5, 8, 50, 30, '','', 'Logo')
        self.set_xy(emisor_pos,linePosY)
        self.set_font('helvetica','B',font_size_header)
        self.cell(80,5,"Open-Ecommerce",debug,1,'L',False,'',False,False)
        self.set_xy(emisor_pos,linePosY+5)
        self.set_font('helvetica','',font_size_header)
        self.cell(80, 5, "Av. P.º de la Reforma 439.", debug, 1)
        self.set_xy(emisor_pos,linePosY+10)
        self.cell(80, 5,"Del. Cuauhtémoc, Ciudad de México, CDMX",debug, 1)
        self.set_xy(emisor_pos,linePosY+15)
        self.cell(80,5,"C.P. 06000",debug,1)
        self.set_xy(emisor_pos,linePosY+20)
        self.cell(80,5,"Tel : +01 555 0123",debug,1)
        self.set_xy(emisor_pos,linePosY+25)
        self.cell(80,5,"Fecha actual: "+datetime.datetime.now().strftime("%d/%m/%Y"),debug,1)

        #Client Info
        self.line(0, linePosY + 35, 210, linePosY + 35)
        self.set_xy(5,linePosY+40)
        self.set_font('helvetica','',font_size_header)
        self.cell(100,5,'Cliente: '+userName,debug,0,'L',False,'',False,False)
        self.cell(100,5,"Orden: "+f'{orderData.pk:07d}',debug,1,'L')
        self.set_xy(5, linePosY+45)
        self.set_font('helvetica','',font_size_header)
        self.cell(100, 5, 'Metodo de pago: ' + metodo_pago, debug, 0)
        self.cell(100,5,"Fecha Pedido: "+orderData.ordered_date.strftime("%d/%m/%Y %H:%M:%S"),debug,1)
        self.ln()
        self.set_xy(5,linePosY+50)
        self.cell(200, 5, 'Direccion: ' + str(orderData.user.checkoutaddress), debug, 0)
        if orderData.guia_envio != "":
            self.ln()
            self.set_xy(5,linePosY+55)
            self.cell(200, 5, 'Guia de envio: ' + str(orderData.guia_envio),debug, 0)



        self.set_y(10)
        self.set_x(-60)
        self.set_font('helvetica','B',16)
        self.cell(53,10,"Recibo de Compra",debug,1)
        self.ln()
        self.ln()
        self.ln()
        self.ln()
        self.ln()
        self.ln()
        self.line(0,linePosY+60,210,linePosY+60)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica','B',8)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

def generate_request(url, params={}):
    response = requests.get(url, params=params)

    if response.status_code == 200:
        return response.json()