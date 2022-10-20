from django.http import HttpResponse
from rest_framework import generics, permissions as drf_permissions

from framework.auth.oauth_scopes import CoreScopes

from api.base import permissions as base_permissions
from api.base.views import JSONAPIBaseView

from .gather import MetadataGatherer
# from .serializers import MetadataRecordSerializer


class MetadataRecordCreate(JSONAPIBaseView, generics.ListCreateAPIView):
    permission_classes = (
        # TODO: check permissions on guid referent (or error in the serializer?)
        drf_permissions.IsAuthenticatedOrReadOnly,
        base_permissions.TokenHasScope,
    )

    required_read_scopes = [CoreScopes.GUIDS_READ]
    required_write_scopes = [CoreScopes.NULL]

    # serializer_class = MetadataRecordSerializer
    view_category = 'metadata-records'
    view_name = 'metadata-record-list'

    def get_queryset(self):
        raise NotImplementedError


class MetadataRecordDetail(JSONAPIBaseView, generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (
        # TODO: check permissions on guid referent
        drf_permissions.IsAuthenticatedOrReadOnly,
        base_permissions.TokenHasScope,
    )

    required_read_scopes = [CoreScopes.GUIDS_READ]
    required_write_scopes = [CoreScopes.NULL]

    # serializer_class = MetadataRecordSerializer
    view_category = 'metadata-records'
    view_name = 'metadata-record-detail'

    def get_object(self):
        raise NotImplementedError


class GuidMetadataDownload(JSONAPIBaseView):

    view_category = 'metadata-records'
    view_name = 'metadata-record-download'

    def get(self, request, guid_id, **kwargs):
        graph = MetadataGatherer(guid_id).gather()
        return HttpResponse(
            graph.serialize(format='json-ld', auto_compact=True),
            headers={
                'Content-Type': 'application/ld+json',
            },
        )
