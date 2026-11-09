from django.urls import path

from .views import HomeView, PageView, SiteSettingsView

urlpatterns = [
    path("home/", HomeView.as_view(), name="home"),
    path("site-settings/", SiteSettingsView.as_view(), name="site-settings"),
    path("pages/<slug:slug>/", PageView.as_view(), name="page"),
]
