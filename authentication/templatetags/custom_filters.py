 
from django import template
import json
from django.core.serializers.json import DjangoJSONEncoder

register = template.Library()

@register.filter(name='json')
def json_filter(value):
    return json.dumps(value, cls=DjangoJSONEncoder)