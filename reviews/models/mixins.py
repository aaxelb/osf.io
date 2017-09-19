# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from include import IncludeQuerySet
from blinker import signal
from transitions import Machine

from django.utils import timezone
from django.db import models
from django.db import transaction
from django.utils import timezone

from osf.models.action import Action
from reviews import workflow
from reviews.exceptions import InvalidTriggerError

from website import settings

from osf.models import NotificationDigest
from osf.models import OSFUser


from website import mails
from website.notifications.emails import get_user_subscriptions, get_node_lineage, localize_timestamp
from website.notifications import utils

reviews_email = signal('reviews_email')


class ReviewProviderMixin(models.Model):
    """A reviewed/moderated collection of objects.
    """

    REVIEWABLE_RELATION_NAME = None

    class Meta:
        abstract = True

    reviews_workflow = models.CharField(null=True, blank=True, max_length=15, choices=workflow.Workflows.choices())
    reviews_comments_private = models.NullBooleanField()
    reviews_comments_anonymous = models.NullBooleanField()

    @property
    def is_reviewed(self):
        return self.reviews_workflow is not None

    def get_reviewable_status_counts(self):
        assert self.REVIEWABLE_RELATION_NAME, 'REVIEWABLE_RELATION_NAME must be set to compute status counts'
        qs = getattr(self, self.REVIEWABLE_RELATION_NAME)
        if isinstance(qs, IncludeQuerySet):
            qs = qs.include(None)
        qs = qs.values('reviews_state').annotate(count=models.Count('*'))
        ret = {state.value: 0 for state in workflow.States}
        ret.update({row['reviews_state']: row['count'] for row in qs if row['reviews_state'] in ret})
        return ret

    def add_admin(self, user):
        from reviews.permissions import GroupHelper
        return GroupHelper(self).get_group('admin').user_set.add(user)

    def add_moderator(self, user):
        from reviews.permissions import GroupHelper
        return GroupHelper(self).get_group('moderator').user_set.add(user)


class ReviewableMixin(models.Model):
    """Something that may be included in a reviewed collection and is subject to a reviews workflow.
    """

    __machine = None

    class Meta:
        abstract = True

    # NOTE: reviews_state should rarely/never be modified directly -- use the state transition methods below
    reviews_state = models.CharField(max_length=15, db_index=True, choices=workflow.States.choices(), default=workflow.States.INITIAL.value)

    date_last_transitioned = models.DateTimeField(null=True, blank=True, db_index=True)

    @property
    def in_public_reviews_state(self):
        public_states = workflow.PUBLIC_STATES.get(self.provider.reviews_workflow)
        if not public_states:
            return False
        return self.reviews_state in public_states

    @property
    def _reviews_machine(self):
        if self.__machine is None:
            self.__machine = ReviewsMachine(self, 'reviews_state')
        return self.__machine

    def reviews_submit(self, user):
        """Run the 'submit' state transition and create a corresponding Action.

        Params:
            user: The user triggering this transition.
        """
        return self.__run_transition(workflow.Triggers.SUBMIT.value, user=user)

    def reviews_accept(self, user, comment):
        """Run the 'accept' state transition and create a corresponding Action.

        Params:
            user: The user triggering this transition.
            comment: Text describing why.
        """
        return self.__run_transition(workflow.Triggers.ACCEPT.value, user=user, comment=comment)

    def reviews_reject(self, user, comment):
        """Run the 'reject' state transition and create a corresponding Action.

        Params:
            user: The user triggering this transition.
            comment: Text describing why.
        """
        return self.__run_transition(workflow.Triggers.REJECT.value, user=user, comment=comment)

    def reviews_edit_comment(self, user, comment):
        """Run the 'edit_comment' state transition and create a corresponding Action.

        Params:
            user: The user triggering this transition.
            comment: New comment text.
        """
        return self.__run_transition(workflow.Triggers.EDIT_COMMENT.value, user=user, comment=comment)

    def __run_transition(self, trigger, **kwargs):
        trigger_fn = getattr(self._reviews_machine, trigger)
        with transaction.atomic():
            result = trigger_fn(**kwargs)
            action = self._reviews_machine.action
            if not result or action is None:
                valid_triggers = self._reviews_machine.get_triggers(self.reviews_state)
                raise InvalidTriggerError(trigger, self.reviews_state, valid_triggers)
            return action


class ReviewsMachine(Machine):

    action = None
    from_state = None

    def __init__(self, reviewable, state_attr):
        self.reviewable = reviewable
        self.__state_attr = state_attr

        super(ReviewsMachine, self).__init__(
            states=[s.value for s in workflow.States],
            transitions=workflow.TRANSITIONS,
            initial=self.state,
            send_event=True,
            prepare_event=['initialize_machine'],
            ignore_invalid_triggers=True,
        )

    @property
    def state(self):
        return getattr(self.reviewable, self.__state_attr)

    @state.setter
    def state(self, value):
        setattr(self.reviewable, self.__state_attr, value)

    def initialize_machine(self, ev):
        self.action = None
        self.from_state = ev.state

    def save_action(self, ev):
        user = ev.kwargs.get('user')
        self.action = Action.objects.create(
            target=self.reviewable,
            creator=user,
            trigger=ev.event.name,
            from_state=self.from_state.name,
            to_state=ev.state.name,
            comment=ev.kwargs.get('comment', ''),
        )

    def update_last_transitioned(self, ev):
        now = self.action.date_created if self.action is not None else timezone.now()
        self.reviewable.date_last_transitioned = now

    def save_changes(self, ev):
        now = self.action.date_created if self.action is not None else timezone.now()
        should_publish = self.reviewable.in_public_reviews_state
        if should_publish and not self.reviewable.is_published:
            self.reviewable.is_published = True
            self.reviewable.date_published = now
            # TODO EZID (MOD-70)
        elif not should_publish and self.reviewable.is_published:
            self.reviewable.is_published = False
        self.reviewable.save()

    def resubmission_allowed(self, ev):
        return self.reviewable.provider.reviews_workflow == workflow.Workflows.PRE_MODERATION.value

    def notify_submit(self, ev):
        context = self.get_context()
        context['referrer'] = ev.kwargs.get('user')
        context['template'] ='reviews_submission_confirmation'
        context['is_pre_moderation'] = self.get_info().get('is_pre_moderation')
        reviews_email.send(context=context)

    def notify_accept(self, ev):
        context = self.get_context()
        context['template'] = 'reviews_submission_status',
        context['is_pre_moderation'] = self.get_info().get('is_pre_moderation')
        context['notify_comment'] = self.get_info().get('notify_comment')
        context['is_rejected'] = self.get_info().get('is_rejected')
        reviews_email.send(context=context)

    def notify_reject(self, ev):
        context = self.get_context()
        context['template'] = 'reviews_submission_status',
        context['is_pre_moderation'] = self.get_info().get('is_pre_moderation')
        context['notify_comment'] = self.get_info().get('notify_comment')
        context['is_rejected'] = self.get_info().get('is_rejected')
        reviews_email.send(context=context)

    def notify_edit_comment(self, ev):
        context = self.get_context()
        context['template'] = 'reviews_update_comment'
        reviews_email.send(context=context)

    def get_info(self):
        return dict(
            is_rejected = self.review_log.to_state == workflow.States.REJECTED.value,
            notify_comment = not (self.reviewable.provider.reviews_comments_private and not self.review_log.comment),
            is_pre_moderation = self.reviewable.provider.reviews_workflow == workflow.Workflows.PRE_MODERATION.value
        )

    def get_context(self):
        return dict(
            creator=self.reviewable.node.creator,
            email_recipients=[contributor._id for contributor in self.reviewable.node.contributors],
            settings=settings.DOMAIN,
            node=self.reviewable.node,
            reviewable_title=self.reviewable.node.title,
            reviewable_url=self.reviewable.absolute_url,
            provider=self.reviewable.provider,
            provider_url=self.reviewable.provider.external_url if self.reviewable.provider.external_url is not None else settings.DOMAIN + '/preprints' + self.reviewable.provider._id
        )

    @reviews_email.connect
    def reviews_notification(self, context):
        timestamp = timezone.now()
        event_type = utils.find_subscription_type('global_reviews')
        template = context.get('template') + '.txt.mako'
        for user_id in context.get('email_recipients'):
            user = OSFUser.load(user_id)
            subscriptions = get_user_subscriptions(user, event_type)
            if user == context.get('creator'):
                context['is_creator'] = True
            else:
                context['is_creator'] = False
            for notification_type in subscriptions:
                if (notification_type != 'none' and subscriptions[notification_type] and user_id in subscriptions[notification_type]):
                    node_lineage_ids = get_node_lineage(context.get('node')) if context.get('node') else []
                    context['user'] = user
                    message = mails.render_message(template, **context)
                    digest = NotificationDigest(
                        user=user,
                        timestamp=timestamp,
                        send_type=notification_type,
                        event='global_reviews',
                        message=message,
                        node_lineage=node_lineage_ids
                    )
                    digest.save()