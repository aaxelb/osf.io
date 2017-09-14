from django.conf.urls import url

from . import views
from reviews.views import PreprintReviewLogList

urlpatterns = [
    url(r'^$', views.PreprintList.as_view(), name=views.PreprintList.view_name),
    url(r'^(?P<preprint_id>\w+)/$', views.PreprintDetail.as_view(), name=views.PreprintDetail.view_name),
    url(r'^(?P<preprint_id>\w+)/citation/$', views.PreprintCitationDetail.as_view(), name=views.PreprintCitationDetail.view_name),
    url(r'^(?P<preprint_id>\w+)/citation/(?P<style_id>[-\w]+)/$', views.PreprintCitationStyleDetail.as_view(), name=views.PreprintCitationStyleDetail.view_name),
    url(r'^(?P<preprint_id>\w+)/identifiers/$', views.PreprintIdentifierList.as_view(), name=views.PreprintIdentifierList.view_name),
    url(r'^(?P<preprint_id>\w+)/review_logs/$', PreprintReviewLogList.as_view(), name=PreprintReviewLogList.view_name),
]
