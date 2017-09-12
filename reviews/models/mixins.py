# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from transitions import Machine

from django.db import models
from django.db import transaction
from django.utils import timezone

from reviews import workflow
from reviews.exceptions import InvalidTransitionError
from reviews.models.action import Action


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
    def is_moderated(self):
        return self.reviews_workflow is not None

    def get_reviewable_status_counts(self):
        assert self.REVIEWABLE_RELATION_NAME, 'REVIEWABLE_RELATION_NAME must be set to compute status counts'
        # TODO fix hackery once GUID query set is gone
        qs = models.QuerySet.annotate(getattr(self, self.REVIEWABLE_RELATION_NAME).values('reviews_state'), count=models.Count('*'))
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
        return self.__run_transition(self._reviews_machine.submit, user=user)

    def reviews_accept(self, user, comment):
        """Run the 'accept' state transition and create a corresponding Action.

        Params:
            user: The user triggering this transition.
            comment: Text describing why.
        """
        return self.__run_transition(self._reviews_machine.accept, user=user, comment=comment)

    def reviews_reject(self, user, comment):
        """Run the 'reject' state transition and create a corresponding Action.

        Params:
            user: The user triggering this transition.
            comment: Text describing why.
        """
        return self.__run_transition(self._reviews_machine.reject, user=user, comment=comment)

    def reviews_edit_comment(self, user, comment):
        """Run the 'edit_comment' state transition and create a corresponding Action.

        Params:
            user: The user triggering this transition.
            comment: New comment text.
        """
        return self.__run_transition(self._reviews_machine.edit_comment, user=user, comment=comment)

    def __run_transition(self, trigger_fn, **kwargs):
        with transaction.atomic():
            result = trigger_fn(**kwargs)
            action = self._reviews_machine.action
            if not result or action is None:
                raise InvalidTransitionError()
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
        # TODO foreign key to action? or to creator?
        now = self.action.date_created if self.action is not None else timezone.now()
        self.reviewable.date_last_transitioned = now

    def save_changes(self, ev):
        now = self.action.date_created if self.action is not None else timezone.now()
        should_publish = self.reviewable.in_public_reviews_state
        if should_publish and not self.reviewable.is_published:
            self.reviewable.is_published = True
            self.reviewable.date_published = now
            # TODO EZID
        elif not should_publish and self.reviewable.is_published:
            self.reviewable.is_published = False
        self.reviewable.save()

    def resubmission_allowed(self, ev):
        return self.reviewable.provider.reviews_workflow == workflow.Workflows.PRE_MODERATION.value

    def notify_submit(self, ev):
        # TODO email node admins (MOD-53)
        pass

    def notify_accept(self, ev):
        # TODO email node admins (MOD-53)
        pass

    def notify_reject(self, ev):
        # TODO email node admins (MOD-53)
        pass

    def notify_edit_comment(self, ev):
        # TODO email node admins (MOD-53)
        pass
