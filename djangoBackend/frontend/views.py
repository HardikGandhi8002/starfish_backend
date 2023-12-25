from django.shortcuts import render
from static import *
# Create your views here.
def frontend(request, path=""):
    return render(
        template_name="index.html",
        request=request,
    )