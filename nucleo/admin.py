from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Item, OrderItem, Order, ItemImage, Payment, CheckoutAddress
from django.utils.html import format_html

class ImageInline(admin.StackedInline):
    model = ItemImage

class PersonAdmin(admin.ModelAdmin):
    inlines = [ImageInline,]

class OderItemAdmin(admin.ModelAdmin):
    list_display = ('pk','user','item','quantity', 'ordered')
class OderAdmin(admin.ModelAdmin):
    list_display = ('pk','user','get_products','ordered_date', 'ordered')

    @admin.display(description='Item Ordered')
    def get_products(self, order):
        return "/ \n".join([p.item.item_name for p in order.items.all()])
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id','payment_ref_id','payment_type','user','amount','currency','timestamp')


class AddressAdmin(admin.StackedInline):
    model = CheckoutAddress
    can_delete = False
    verbose_name_plural = "Direcciones"


# Define a new User admin
class UserAdmin(BaseUserAdmin):
    inlines = (AddressAdmin, )


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(Item,PersonAdmin)
admin.site.register(OrderItem,OderItemAdmin)
admin.site.register(Order,OderAdmin)
admin.site.register(Payment,PaymentAdmin)