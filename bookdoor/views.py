from django.shortcuts import render
from django.shortcuts import redirect
from django.views.generic import TemplateView

class BookDoorView(TemplateView):
  
  def __init__(self,):
    self.params={
      'form':'',
    }

  def get(self,request):
    return render(request,'bookdoor/index.html', self.params)

  def post(self,request):
    return render(request, 'bookdoor/index.html',self.params)