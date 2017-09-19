from datetime import timedelta

import pytest
from furl import furl

from osf_tests.factories import (
    AuthUserFactory,
    PreprintFactory,
    PreprintProviderFactory,
)
from reviews.permissions import GroupHelper
from reviews_tests.factories import ReviewLogFactory
from website.util import permissions as osf_permissions


@pytest.mark.django_db
class ReviewLogCommentSettingsMixin(object):

    @pytest.fixture()
    def url(self):
        raise NotImplementedError

    @pytest.fixture()
    def provider(self):
        return PreprintProviderFactory()

    @pytest.fixture()
    def preprint(self, provider):
        return PreprintFactory(provider=provider)

    @pytest.fixture()
    def logs(self, preprint):
        return [ReviewLogFactory(reviewable=preprint) for _ in range(5)]

    @pytest.fixture()
    def provider_admin(self, provider):
        user = AuthUserFactory()
        user.groups.add(GroupHelper(provider).get_group('admin'))
        return user

    @pytest.fixture()
    def provider_moderator(self, provider):
        user = AuthUserFactory()
        user.groups.add(GroupHelper(provider).get_group('moderator'))
        return user

    @pytest.fixture()
    def node_admin(self, preprint):
        user = AuthUserFactory()
        preprint.node.add_contributor(user, permissions=[osf_permissions.READ, osf_permissions.WRITE, osf_permissions.ADMIN])
        return user

    def test_comment_settings(self, app, url, provider, logs, provider_admin, provider_moderator, node_admin):
        expected_ids = set([l._id for l in logs])
        for anonymous in [True, False]:
            for private in [True, False]:
                provider.reviews_comments_anonymous = anonymous
                provider.reviews_comments_private = private
                provider.save()

                # admin always sees comment/creator
                res = app.get(url, auth=provider_admin.auth)
                self.__assert_fields(res, expected_ids, False, False)

                # moderator always sees comment/creator
                res = app.get(url, auth=provider_moderator.auth)
                self.__assert_fields(res, expected_ids, False, False)

                # node admin sees what the settings allow
                res = app.get(url, auth=node_admin.auth)
                self.__assert_fields(res, expected_ids, anonymous, private)

    def __assert_fields(self, res, expected_ids, hidden_creator, hidden_comment):
        data = res.json['data']
        actual_ids = set([l['id'] for l in data])
        if expected_ids != actual_ids:
            raise Exception((expected_ids, actual_ids))
        assert expected_ids == actual_ids

        for log in data:
            if hidden_creator:
                assert 'creator' not in log['relationships']
            else:
                assert 'creator' in log['relationships']
            if hidden_comment:
                assert 'comment' not in log['attributes']
            else:
                assert 'comment' in log['attributes']
