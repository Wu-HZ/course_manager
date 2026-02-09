from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import TemplateView
from django.conf import settings
from django.http import HttpResponse
import os

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('core.urls')),
    path('api/scheduler/', include('scheduler.urls')),
]

# 生产模式下服务前端 SPA
if not settings.DEBUG or os.environ.get('SERVE_FRONTEND') == 'true':
    # 前端静态文件由 whitenoise 处理
    # 所有非 API 路由返回 index.html，由前端路由处理
    urlpatterns += [
        re_path(r'^(?!api/|admin/|static/).*$', TemplateView.as_view(template_name='index.html')),
    ]
