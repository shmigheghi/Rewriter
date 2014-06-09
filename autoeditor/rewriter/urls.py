from django.conf.urls import patterns, url

from rewriter import views

urlpatterns = patterns('',
    url(r'^$', views.runrewriter, name='index'),
)