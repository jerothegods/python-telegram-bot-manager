from django.contrib import admin
from .models import *

admin.site.register(User)
admin.site.register(ChatPhoto)
admin.site.register(Chat)
admin.site.register(PhotoSize)
admin.site.register(Location)
admin.site.register(Message)
admin.site.register(Bot)
admin.site.register(State)
admin.site.register(StateInstance)
admin.site.register(Handler)
admin.site.register(HandlerInstance)
admin.site.register(TelegramClientAPI)
