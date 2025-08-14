from django.http import HttpResponse

def home(request):
    return HttpResponse("<h1>This is Backend for Dev Rumble made in Django!</h1>")