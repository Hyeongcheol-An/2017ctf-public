from django.conf.urls import url
from . import views

urlpatterns = (
    url(r'^$', views.index, name='index'),
    url(r'^login/', views.login, name='login'),
    url(r'^logout/', views.logout, name='logout'),
    url(r'^list/', views.list, name='list'),
    url(r'^write/', views.write, name='write'),
    url(r'^read/(?P<post_id>\d+)', views.read, name='read'),
    url(r'^delete/(?P<post_id>\d+)', views.delete, name='delete'),
    url(r'^edit/(?P<post_id>\d+)', views.edit, name='edit'),
    url(r'^auth/$', views.auth_index, name='auth_index'),
    url(r'^auth/chal/$', views.auth_chal, name='auth_chal'),
    url(r'^auth/resp/$', views.auth_resp, name='auth_resp'),
    url(r'^auth/success/$', views.auth_success, name='auth_success'),
    url(r'^notarize/$', views.notarize, name='notarize'),
)
