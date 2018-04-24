from django.http.response import HttpResponse
from django.shortcuts import render

# Create your views here.
from django.views.generic import View


class IndexView(View):
    """进入首页"""
    def get(self, request):

        return render(request, 'index.html')