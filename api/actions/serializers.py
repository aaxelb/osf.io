# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import generics
from rest_framework import serializers as ser

from api.base import utils
from api.base.exceptions import Conflict
from api.base.exceptions import JSONAPIAttributeException
from api.base.serializers import JSONAPISerializer
from api.base.serializers import LinksField
from api.base.serializers import RelationshipField
from api.base.serializers import HideIfProviderCommentsAnonymous
from api.base.serializers import HideIfProviderCommentsPrivate

from osf.models import PreprintService

from reviews.exceptions import InvalidTriggerError
from reviews.workflow import Triggers
from reviews.workflow import States


class TargetRelationshipField(RelationshipField):
    def get_object(self, preprint_id):
        return PreprintService.objects.get(guids___id=preprint_id)

    def to_internal_value(self, data):
        preprint = self.get_object(data)
        return {'target': preprint}


class ActionSerializer(JSONAPISerializer):
    filterable_fields = frozenset([
        'id',
        'trigger',
        'from_state',
        'to_state',
        'date_created',
        'date_modified',
        'provider',
        'target',
    ])

    id = ser.CharField(source='_id', read_only=True)

    trigger = ser.ChoiceField(choices=Triggers.choices())

    comment = HideIfProviderCommentsPrivate(ser.CharField(max_length=65535, required=False))

    from_state = ser.ChoiceField(choices=States.choices(), read_only=True)
    to_state = ser.ChoiceField(choices=States.choices(), read_only=True)

    date_created = ser.DateTimeField(read_only=True)
    date_modified = ser.DateTimeField(read_only=True)

    provider = RelationshipField(
        read_only=True,
        related_view='preprint_providers:preprint_provider-detail',
        related_view_kwargs={'provider_id': '<target.provider._id>'},
        filter_key='target__provider___id',
    )

    target = TargetRelationshipField(
        read_only=False,
        required=True,
        related_view='preprints:preprint-detail',
        related_view_kwargs={'preprint_id': '<target._id>'},
        filter_key='target__guids___id',
    )

    creator = HideIfProviderCommentsAnonymous(RelationshipField(
        read_only=True,
        related_view='users:user-detail',
        related_view_kwargs={'user_id': '<creator._id>'},
        filter_key='creator__guids___id',
        always_embed=True,
    ))

    links = LinksField(
        {
            'self': 'get_action_url',
        }
    )

    def get_absolute_url(self, obj):
        return self.get_action_url(obj)

    def get_action_url(self, obj):
        return utils.absolute_reverse('actions:action-detail', kwargs={'action_id': obj._id, 'version': self.context['request'].parser_context['kwargs']['version']})

    def create(self, validated_data):
        trigger = validated_data.pop('trigger')
        user = validated_data.pop('user')
        target = validated_data.pop('target')
        comment = validated_data.pop('comment', '')
        try:
            if trigger == Triggers.ACCEPT.value:
                return target.reviews_accept(user, comment)
            if trigger == Triggers.REJECT.value:
                return target.reviews_reject(user, comment)
            if trigger == Triggers.EDIT_COMMENT.value:
                return target.reviews_edit_comment(user, comment)
            if trigger == Triggers.SUBMIT.value:
                return target.reviews_submit(user)
        except InvalidTriggerError as e:
            # Invalid transition from the current state
            raise Conflict(e.message)
        else:
            raise JSONAPIAttributeException(attribute='trigger', detail='Invalid trigger.')

    class Meta:
        type_ = 'actions'
