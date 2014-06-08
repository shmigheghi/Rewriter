from django.conf.urls import patterns, url

from rewriter import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url(r'^rewriter/$', views.runrewriter, name='index'),
)