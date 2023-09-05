from django import template

register = template.Library()

@register.filter
def get_qty_stock(item, args):
    _params = args.split(',')
    print("Params:", f"{item} -  {args} - {_params}")
    try:
        return 50
    except Exception as e:
        import random
        return 0