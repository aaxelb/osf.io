import mock
import pytest
from django.contrib.auth.models import Group

from framework.auth import Auth
from django.contrib.auth.models import AnonymousUser
from framework.exceptions import PermissionsError
from osf.models import OSFGroup, Node, OSFUser, OSFGroupLog, NodeLog
from osf.utils.permissions import MANAGER, MEMBER
from .factories import (
    NodeFactory,
    ProjectFactory,
    AuthUserFactory,
    OSFGroupFactory
)

pytestmark = pytest.mark.django_db

@pytest.fixture()
def manager():
    return AuthUserFactory()

@pytest.fixture()
def member():
    return AuthUserFactory()

@pytest.fixture()
def user_two():
    return AuthUserFactory()

@pytest.fixture()
def user_three():
    return AuthUserFactory()

@pytest.fixture()
def auth(manager):
    return Auth(manager)

@pytest.fixture()
def project(manager):
    return ProjectFactory(creator=manager)

@pytest.fixture()
def osf_group(manager, member):
    osf_group = OSFGroupFactory(creator=manager)
    osf_group.make_member(member)
    return osf_group

class TestOSFGroup:

    def test_osf_group_creation(self, manager, member, user_two, fake):
        osf_group = OSFGroup.objects.create(name=fake.bs(), creator=manager)
        # OSFGroup creator given manage permissions
        assert osf_group.has_permission(manager, 'manage') is True
        assert osf_group.has_permission(user_two, 'manage') is False

        assert manager in osf_group.managers
        assert manager in osf_group.members
        assert manager not in osf_group.members_only

    @mock.patch('website.osf_groups.views.mails.send_mail')
    def test_make_manager(self, mock_send_mail, manager, member, user_two, user_three, osf_group):
        # no permissions
        with pytest.raises(PermissionsError):
            osf_group.make_manager(user_two, Auth(user_three))

        # member only
        with pytest.raises(PermissionsError):
            osf_group.make_manager(user_two, Auth(member))

        # manage permissions
        osf_group.make_manager(user_two, Auth(manager))
        assert osf_group.has_permission(user_two, 'manage') is True
        assert user_two in osf_group.managers
        assert user_two in osf_group.members
        assert mock_send_mail.call_count == 1

        # upgrade to manager
        osf_group.make_manager(member, Auth(manager))
        assert osf_group.has_permission(member, 'manage') is True
        assert member in osf_group.managers
        assert member in osf_group.members
        # upgrading an existing member does not re-send an email
        assert mock_send_mail.call_count == 1

    @mock.patch('website.osf_groups.views.mails.send_mail')
    def test_make_member(self, mock_send_mail, manager, member, user_two, user_three, osf_group):
        # no permissions
        with pytest.raises(PermissionsError):
            osf_group.make_member(user_two, Auth(user_three))

        # member only
        with pytest.raises(PermissionsError):
            osf_group.make_member(user_two, Auth(member))

        # manage permissions
        osf_group.make_member(user_two, Auth(manager))
        assert osf_group.has_permission(user_two, 'manage') is False
        assert user_two not in osf_group.managers
        assert user_two in osf_group.members
        assert mock_send_mail.call_count == 1

        # downgrade to member, sole manager
        with pytest.raises(ValueError):
            osf_group.make_member(manager, Auth(manager))

        # downgrade to member
        osf_group.make_manager(user_two, Auth(manager))
        assert user_two in osf_group.managers
        assert user_two in osf_group.members
        osf_group.make_member(user_two, Auth(manager))
        assert user_two not in osf_group.managers
        assert user_two in osf_group.members
        assert mock_send_mail.call_count == 1

    @mock.patch('website.osf_groups.views.mails.send_mail')
    def test_add_unregistered_member(self, mock_send_mail, manager, member, osf_group, user_two):
        test_fullname = 'Test User'
        test_email = 'test_member@cos.io'
        test_manager_email = 'test_manager@cos.io'

        # Email already exists
        with pytest.raises(ValueError):
            osf_group.add_unregistered_member(test_fullname, user_two.username, auth=Auth(manager))

        # Test need manager perms to add
        with pytest.raises(PermissionsError):
            osf_group.add_unregistered_member(test_fullname, test_email, auth=Auth(member))

        # Add member
        osf_group.add_unregistered_member(test_fullname, test_email, auth=Auth(manager))
        assert mock_send_mail.call_count == 1
        unreg_user = OSFUser.objects.get(username=test_email)
        assert unreg_user in osf_group.members
        assert unreg_user not in osf_group.managers
        # Unreg user hasn't claimed account, so they have no permissions, even though they belong to member group
        assert osf_group.has_permission(unreg_user, 'member') is False
        assert osf_group._id in unreg_user.unclaimed_records

        # Attempt to add unreg user as a member
        with pytest.raises(ValueError):
            osf_group.add_unregistered_member(test_fullname, test_email, auth=Auth(manager))

        # Add unregistered manager
        osf_group.add_unregistered_member(test_fullname, test_manager_email, auth=Auth(manager), role='manager')
        assert mock_send_mail.call_count == 2
        unreg_manager = OSFUser.objects.get(username=test_manager_email)
        assert unreg_manager in osf_group.members
        assert unreg_manager in osf_group.managers
        # Unreg manager hasn't claimed account, so they have no permissions, even though they belong to member group
        assert osf_group.has_permission(unreg_manager, 'member') is False
        assert osf_group._id in unreg_manager.unclaimed_records

    def test_remove_member(self, manager, member, user_three, osf_group):
        new_member = AuthUserFactory()
        osf_group.make_member(new_member)
        assert new_member not in osf_group.managers
        assert new_member in osf_group.members

        # no permissions
        with pytest.raises(PermissionsError):
            osf_group.remove_member(new_member, Auth(user_three))

        # member only
        with pytest.raises(PermissionsError):
            osf_group.remove_member(new_member, Auth(member))

        # manage permissions
        osf_group.remove_member(new_member, Auth(manager))
        assert new_member not in osf_group.managers
        assert new_member not in osf_group.members

        # Remove self - member can remove themselves
        osf_group.remove_member(member, Auth(member))
        assert member not in osf_group.managers
        assert member not in osf_group.members

    def test_remove_manager(self, manager, member, user_three, osf_group):
        new_manager = AuthUserFactory()
        osf_group.make_manager(new_manager)
        # no permissions
        with pytest.raises(PermissionsError):
            osf_group.remove_member(new_manager, Auth(user_three))

        # member only
        with pytest.raises(PermissionsError):
            osf_group.remove_member(new_manager, Auth(member))

        # manage permissions
        osf_group.remove_member(new_manager, Auth(manager))
        assert new_manager not in osf_group.managers
        assert new_manager not in osf_group.members

        # can't remove last manager
        with pytest.raises(ValueError):
            osf_group.remove_member(manager, Auth(manager))
        assert manager in osf_group.managers
        assert manager in osf_group.members

    def test_rename_osf_group(self, manager, member, user_two, osf_group):
        new_name = 'Platform Team'
        # no permissions
        with pytest.raises(PermissionsError):
            osf_group.set_group_name(new_name, Auth(user_two))

        # member only
        with pytest.raises(PermissionsError):
            osf_group.set_group_name(new_name, Auth(member))

        # manage permissions
        osf_group.set_group_name(new_name, Auth(manager))
        osf_group.save()

        assert osf_group.name == new_name

    def test_remove_group(self, manager, member, osf_group):
        osf_group_name = osf_group.name
        manager_group_name = osf_group.manager_group.name
        member_group_name = osf_group.member_group.name

        osf_group.remove_group(Auth(manager))
        assert not OSFGroup.objects.filter(name=osf_group_name).exists()
        assert not Group.objects.filter(name=manager_group_name).exists()
        assert not Group.objects.filter(name=member_group_name).exists()

        assert manager_group_name not in manager.groups.values_list('name', flat=True)

    def test_remove_group_node_perms(self, manager, member, osf_group, project):
        project.add_osf_group(osf_group, 'admin')
        assert project.has_permission(member, 'admin') is True

        osf_group.remove_group(Auth(manager))

        assert project.has_permission(member, 'admin') is False

    def test_add_osf_group_to_node_already_connected(self, manager, member, osf_group, project):
        project.add_osf_group(osf_group, 'admin')
        assert project.has_permission(member, 'admin') is True

        project.add_osf_group(osf_group, 'write')
        assert project.has_permission(member, 'admin') is False
        assert project.has_permission(member, 'write') is True

    def test_user_groups_property(self, manager, member, osf_group):
        assert osf_group in manager.osf_groups
        assert osf_group in member.osf_groups

        other_group = OSFGroupFactory()

        assert other_group not in manager.osf_groups
        assert other_group not in member.osf_groups

    def test_osf_group_nodes(self, manager, member, project, osf_group):
        nodes = osf_group.nodes
        assert len(nodes) == 0
        project.add_osf_group(osf_group, 'read')
        assert project in osf_group.nodes

        project_two = ProjectFactory(creator=manager)
        project_two.add_osf_group(osf_group, 'write')
        assert len(osf_group.nodes) == 2
        assert project_two in osf_group.nodes

    def test_user_group_roles(self, manager, member, user_three, osf_group):
        assert manager.group_role(osf_group) == MANAGER
        assert member.group_role(osf_group) == MEMBER
        assert user_three.group_role(osf_group) is None

    def test_add_osf_group_to_node(self, manager, member, user_two, osf_group, project):
        # noncontributor
        with pytest.raises(PermissionsError):
            project.add_osf_group(osf_group, 'write', auth=Auth(member))

        # Non-admin on project
        project.add_contributor(user_two, 'write')
        project.save()
        with pytest.raises(PermissionsError):
            project.add_osf_group(osf_group, 'write', auth=Auth(user_two))

        project.add_osf_group(osf_group, 'read', auth=Auth(manager))
        # Manager was already a node admin
        assert project.has_permission(manager, 'admin') is True
        assert project.has_permission(manager, 'write') is True
        assert project.has_permission(manager, 'read') is True

        assert project.has_permission(member, 'admin') is False
        assert project.has_permission(member, 'write') is False
        assert project.has_permission(member, 'read') is True

        project.update_osf_group(osf_group, 'write', auth=Auth(manager))
        assert project.has_permission(member, 'admin') is False
        assert project.has_permission(member, 'write') is True
        assert project.has_permission(member, 'read') is True

        project.update_osf_group(osf_group, 'admin', auth=Auth(manager))
        assert project.has_permission(member, 'admin') is True
        assert project.has_permission(member, 'write') is True
        assert project.has_permission(member, 'read') is True

        # project admin cannot add a group they are not a manager of
        other_group = OSFGroupFactory()
        with pytest.raises(PermissionsError):
            project.add_osf_group(other_group, 'admin', auth=Auth(project.creator))

    def test_add_osf_group_to_node_default_permission(self, manager, member, osf_group, project):
        project.add_osf_group(osf_group, auth=Auth(manager))

        assert project.has_permission(manager, 'admin') is True
        assert project.has_permission(manager, 'write') is True
        assert project.has_permission(manager, 'read') is True

        # osf_group given write permissions by default
        assert project.has_permission(member, 'admin') is False
        assert project.has_permission(member, 'write') is True
        assert project.has_permission(member, 'read') is True

    def test_update_osf_group_node(self, manager, member, user_two, user_three, osf_group, project):
        project.add_osf_group(osf_group, 'admin')

        assert project.has_permission(member, 'admin') is True
        assert project.has_permission(member, 'write') is True
        assert project.has_permission(member, 'read') is True

        project.update_osf_group(osf_group, 'read')
        assert project.has_permission(member, 'admin') is False
        assert project.has_permission(member, 'write') is False
        assert project.has_permission(member, 'read') is True

        project.update_osf_group(osf_group, 'write')
        assert project.has_permission(member, 'admin') is False
        assert project.has_permission(member, 'write') is True
        assert project.has_permission(member, 'read') is True

        project.update_osf_group(osf_group, 'admin')
        assert project.has_permission(member, 'admin') is True
        assert project.has_permission(member, 'write') is True
        assert project.has_permission(member, 'read') is True

        # Project admin who does not belong to the manager group can update group permissions
        project.add_contributor(user_two, 'admin', save=True)
        project.update_osf_group(osf_group, 'read', auth=Auth(user_two))
        assert project.has_permission(member, 'admin') is False
        assert project.has_permission(member, 'write') is False
        assert project.has_permission(member, 'read') is True

        # Project write contributor cannot update group permissions
        project.add_contributor(user_three, 'write', save=True)
        with pytest.raises(PermissionsError):
            project.update_osf_group(osf_group, 'admin', auth=Auth(user_three))
        assert project.has_permission(member, 'admin') is False

    def test_replace_contributor(self, manager, member, osf_group):
        user = osf_group.add_unregistered_member('test_user', 'test@cos.io', auth=Auth(manager))
        assert user in osf_group.members
        assert user not in osf_group.managers
        assert (
            osf_group._id in
            user.unclaimed_records.keys()
        )
        osf_group.replace_contributor(user, member)
        assert user not in osf_group.members
        assert user not in osf_group.managers

        # test unclaimed_records is removed
        assert (
            osf_group._id not in
            user.unclaimed_records.keys()
        )

    def test_remove_osf_group_from_node(self, manager, member, user_two, osf_group, project):
        # noncontributor
        with pytest.raises(PermissionsError):
            project.remove_osf_group(osf_group, auth=Auth(member))

        project.add_osf_group(osf_group, 'admin', auth=Auth(manager))
        assert project.has_permission(member, 'admin') is True
        assert project.has_permission(member, 'write') is True
        assert project.has_permission(member, 'read') is True

        project.remove_osf_group(osf_group, auth=Auth(manager))
        assert project.has_permission(member, 'admin') is False
        assert project.has_permission(member, 'write') is False
        assert project.has_permission(member, 'read') is False

        # Project admin who does not belong to the manager group can remove the group
        project.add_osf_group(osf_group, 'admin', auth=Auth(manager))
        project.add_contributor(user_two, 'admin')
        project.save()
        project.remove_osf_group(osf_group, auth=Auth(user_two))
        assert project.has_permission(member, 'admin') is False
        assert project.has_permission(member, 'write') is False
        assert project.has_permission(member, 'read') is False

        # Manager who is not an admin can remove the group
        user_three = AuthUserFactory()
        osf_group.make_manager(user_three)
        project.add_osf_group(osf_group, 'write')
        assert project.has_permission(user_three, 'admin') is False
        assert project.has_permission(user_three, 'write') is True
        assert project.has_permission(user_three, 'read') is True
        project.remove_osf_group(osf_group, auth=Auth(user_three))
        assert project.has_permission(user_three, 'admin') is False
        assert project.has_permission(user_three, 'write') is False
        assert project.has_permission(user_three, 'read') is False

    def test_node_groups_property(self, manager, member, osf_group, project):
        project.add_osf_group(osf_group, 'admin', auth=Auth(manager))
        project.save()
        assert osf_group in project.osf_groups
        assert len(project.osf_groups) == 1

        group_two = OSFGroupFactory(creator=manager)
        project.add_osf_group(group_two, 'admin', auth=Auth(manager))
        project.save()
        assert group_two in project.osf_groups
        assert len(project.osf_groups) == 2

    def test_get_osf_groups_with_perms_property(self, manager, member, osf_group, project):
        second_group = OSFGroupFactory(creator=manager)
        third_group = OSFGroupFactory(creator=manager)
        fourth_group = OSFGroupFactory(creator=manager)
        OSFGroupFactory(creator=manager)

        project.add_osf_group(osf_group, 'admin')
        project.add_osf_group(second_group, 'write')
        project.add_osf_group(third_group, 'write')
        project.add_osf_group(fourth_group, 'read')

        read_groups = project.get_osf_groups_with_perms('read')
        assert len(read_groups) == 4

        write_groups = project.get_osf_groups_with_perms('write')
        assert len(write_groups) == 3

        admin_groups = project.get_osf_groups_with_perms('admin')
        assert len(admin_groups) == 1

        with pytest.raises(ValueError):
            project.get_osf_groups_with_perms('crazy')

    def test_belongs_to_osfgroup_property(self, manager, member, user_two, osf_group):
        assert osf_group.belongs_to_osfgroup(manager) is True
        assert osf_group.belongs_to_osfgroup(member) is True
        assert osf_group.belongs_to_osfgroup(user_two) is False

    def test_node_object_can_view_osfgroups(self, manager, member, project, osf_group):
        project.add_contributor(member, 'admin', save=True)  # Member is explicit admin contributor on project
        child = NodeFactory(parent=project, creator=manager)  # Member is implicit admin on child
        grandchild = NodeFactory(parent=child, creator=manager)  # Member is implicit admin on grandchild

        project_two = ProjectFactory(creator=manager)
        project_two.add_osf_group(osf_group, 'admin')  # Member has admin permissions to project_two through osf_group
        child_two = NodeFactory(parent=project_two, creator=manager)  # Member has implicit admin on child_two through osf_group
        grandchild_two = NodeFactory(parent=child_two, creator=manager)  # Member has implicit admin perms on grandchild_two through osf_group
        can_view = Node.objects.can_view(member)
        assert len(can_view) == 6
        assert set(list(can_view.values_list('id', flat=True))) == set((project.id,
                                                                        child.id,
                                                                        grandchild.id,
                                                                        project_two.id,
                                                                        child_two.id,
                                                                        grandchild_two.id))

        grandchild_two.is_deleted = True
        grandchild_two.save()
        can_view = Node.objects.can_view(member)
        assert len(can_view) == 5
        assert grandchild_two not in can_view

    def test_parent_admin_users_osf_groups(self, manager, member, project, osf_group):
        child = NodeFactory(parent=project, creator=manager)
        project.add_osf_group(osf_group, 'admin')
        # Manager has explict admin to child, member has implicit admin.
        # Manager should be in admin_contributors, member should be in parent_admin_contributors

        assert manager in child.admin_users
        assert member not in child.admin_users

        assert manager not in child.parent_admin_users
        assert member in child.parent_admin_users

    def test_get_users_with_perm_osf_groups(self, project, manager, member, osf_group):
        # Explicitly added as a contributor
        read_users = project.get_users_with_perm('read')
        write_users = project.get_users_with_perm('write')
        admin_users = project.get_users_with_perm('admin')
        assert len(project.get_users_with_perm('read')) == 1
        assert len(project.get_users_with_perm('write')) == 1
        assert len(project.get_users_with_perm('admin')) == 1
        assert manager in read_users
        assert manager in write_users
        assert manager in admin_users

        # Added through osf groups
        project.add_osf_group(osf_group, 'write')
        read_users = project.get_users_with_perm('read')
        write_users = project.get_users_with_perm('write')
        admin_users = project.get_users_with_perm('admin')
        assert len(project.get_users_with_perm('read')) == 2
        assert len(project.get_users_with_perm('write')) == 2
        assert len(project.get_users_with_perm('admin')) == 1
        assert member in read_users
        assert member in write_users
        assert member not in admin_users

    def test_osf_group_node_can_view(self, project, manager, member, osf_group):
        assert project.can_view(Auth(member)) is False
        project.add_osf_group(osf_group, 'read')
        assert project.can_view(Auth(member)) is True
        assert project.can_edit(Auth(member)) is False

        project.remove_osf_group(osf_group)
        project.add_osf_group(osf_group, 'write')
        assert project.can_view(Auth(member)) is True
        assert project.can_edit(Auth(member)) is True

        child = ProjectFactory(parent=project)
        project.remove_osf_group(osf_group)
        project.add_osf_group(osf_group, 'admin')
        # implicit OSF Group admin
        assert child.can_view(Auth(member)) is True
        assert child.can_edit(Auth(member)) is False

        grandchild = ProjectFactory(parent=child)
        assert grandchild.can_view(Auth(member)) is True
        assert grandchild.can_edit(Auth(member)) is False

    def test_node_has_permission(self, project, manager, member, osf_group):
        assert project.can_view(Auth(member)) is False
        project.add_osf_group(osf_group, 'read')
        assert project.has_permission(member, 'read') is True
        assert project.has_permission(member, 'write') is False

        project.remove_osf_group(osf_group)
        project.add_osf_group(osf_group, 'write')
        assert project.has_permission(member, 'read') is True
        assert project.has_permission(member, 'write') is True
        assert project.has_permission(member, 'admin') is False

        child = ProjectFactory(parent=project)
        project.remove_osf_group(osf_group)
        project.add_osf_group(osf_group, 'admin')
        # implicit OSF Group admin
        assert child.has_permission(member, 'admin') is False
        assert child.has_permission(member, 'read') is True

        grandchild = ProjectFactory(parent=child)
        assert grandchild.has_permission(member, 'write') is False
        assert grandchild.has_permission(member, 'read') is True

    def test_node_get_permissions_override(self, project, manager, member, osf_group):
        project.add_osf_group(osf_group, 'write')
        assert set(project.get_permissions(member)) == set(['write_node', 'read_node'])

        project.remove_osf_group(osf_group)
        project.add_osf_group(osf_group, 'read')
        assert set(project.get_permissions(member)) == set(['read_node'])

        anon = AnonymousUser()
        assert project.get_permissions(anon) == []

    def test_is_contributor(self, project, manager, member, osf_group):
        assert project.is_contributor(manager) is True
        assert project.is_contributor(member) is False
        project.add_osf_group(osf_group, 'read', auth=Auth(project.creator))
        assert project.is_contributor(member) is False
        assert project.is_contributor_or_group_member(member) is True

        project.remove_osf_group(osf_group, auth=Auth(manager))
        assert project.is_contributor_or_group_member(member) is False
        project.add_contributor(member, 'read')
        assert project.is_contributor(member) is True
        assert project.is_contributor_or_group_member(member) is True

    def test_is_contributor_or_group_member(self, project, manager, member, osf_group):
        project.add_osf_group(osf_group, 'admin', auth=Auth(project.creator))
        assert project.is_contributor_or_group_member(member) is True

        project.remove_osf_group(osf_group, auth=Auth(manager))
        assert project.is_contributor_or_group_member(member) is False
        project.add_osf_group(osf_group, 'write', auth=Auth(project.creator))
        assert project.is_contributor_or_group_member(member) is True

        project.remove_osf_group(osf_group, auth=Auth(manager))
        assert project.is_contributor_or_group_member(member) is False
        project.add_osf_group(osf_group, 'read', auth=Auth(project.creator))
        assert project.is_contributor_or_group_member(member) is True

        project.remove_osf_group(osf_group, auth=Auth(manager))

    @pytest.mark.enable_quickfiles_creation
    def test_merge_users_transfers_group_membership(self, member, manager, osf_group):
        # merge member
        other_user = AuthUserFactory()
        other_user.merge_user(member)
        other_user.save()
        assert osf_group.is_member(other_user)

        # merge manager
        other_other_user = AuthUserFactory()
        other_other_user.merge_user(manager)
        other_other_user.save()
        assert osf_group.is_member(other_other_user)
        assert osf_group.has_permission(other_other_user, 'manage')

    def test_osf_group_is_admin_parent(self, project, manager, member, osf_group, user_two, user_three):
        child = NodeFactory(parent=project, creator=manager)
        assert project.is_admin_parent(manager) is True
        assert project.is_admin_parent(member) is False

        project.add_contributor(user_two, 'write', save=True)
        assert project.is_admin_parent(user_two) is False

        assert child.is_admin_parent(manager) is True
        child.add_contributor(user_two, 'admin', save=True)
        assert child.is_admin_parent(user_two) is True

        assert child.is_admin_parent(user_three) is False
        osf_group.make_member(user_three)
        project.add_osf_group(osf_group, 'write')
        assert child.is_admin_parent(user_three) is False

        project.update_osf_group(osf_group, 'admin')
        assert child.is_admin_parent(user_three) is True
        assert child.is_admin_parent(user_three, include_group_admin=False) is False
        project.remove_osf_group(osf_group)

        child.add_osf_group(osf_group, 'write')
        assert child.is_admin_parent(user_three) is False
        child.update_osf_group(osf_group, 'admin')
        assert child.is_admin_parent(user_three) is True
        assert child.is_admin_parent(user_three, include_group_admin=False) is False


class TestOSFGroupLogging:
    def test_logging(self, project, manager, member):
        group = OSFGroup.objects.create(name='My Lab', creator_id=manager.id)
        assert group.logs.count() == 2
        log = group.logs.last()
        assert log.action == OSFGroupLog.GROUP_CREATED
        assert log.user == manager
        assert log.user == manager
        assert log.params['group'] == group._id

        log = group.logs.first()
        assert log.action == OSFGroupLog.MANAGER_ADDED
        assert log.params['group'] == group._id

        group.make_member(member, Auth(manager))
        group.make_member(member, Auth(manager))
        assert group.logs.count() == 3
        log = group.logs.first()
        assert log.action == OSFGroupLog.MEMBER_ADDED
        assert log.user == manager
        assert log.params['group'] == group._id
        assert log.params['user'] == member._id

        group.make_manager(member, Auth(manager))
        group.make_manager(member, Auth(manager))
        assert group.logs.count() == 4
        log = group.logs.first()
        assert log.action == OSFGroupLog.ROLE_UPDATED
        assert log.user == manager
        assert log.params['group'] == group._id
        assert log.params['user'] == member._id
        assert log.params['new_role'] == MANAGER

        group.make_member(member, Auth(manager))
        group.make_member(member, Auth(manager))
        log = group.logs.first()
        assert group.logs.count() == 5
        assert log.action == OSFGroupLog.ROLE_UPDATED
        assert log.user == manager
        assert log.params['group'] == group._id
        assert log.params['user'] == member._id
        assert log.params['new_role'] == MEMBER

        group.remove_member(member, Auth(manager))
        group.remove_member(member, Auth(manager))
        assert group.logs.count() == 6
        log = group.logs.first()
        assert log.action == OSFGroupLog.MEMBER_REMOVED
        assert log.user == manager
        assert log.params['group'] == group._id
        assert log.params['user'] == member._id

        group.set_group_name('New Name', Auth(manager))
        group.set_group_name('New Name', Auth(manager))
        assert group.logs.count() == 7
        log = group.logs.first()
        assert log.action == OSFGroupLog.EDITED_NAME
        assert log.user == manager
        assert log.params['group'] == group._id
        assert log.params['name_original'] == 'My Lab'

        project.add_osf_group(group, 'write', Auth(manager))
        project.add_osf_group(group, 'write', Auth(manager))
        assert group.logs.count() == 8
        log = group.logs.first()
        assert log.action == OSFGroupLog.NODE_CONNECTED
        assert log.user == manager
        assert log.params['group'] == group._id
        assert log.params['node'] == project._id
        assert log.params['permission'] == 'write'
        node_log = project.logs.first()

        assert node_log.action == NodeLog.GROUP_ADDED
        assert node_log.user == manager
        assert node_log.params['group'] == group._id
        assert node_log.params['node'] == project._id
        assert node_log.params['permission'] == 'write'

        project.update_osf_group(group, 'read', Auth(manager))
        project.update_osf_group(group, 'read', Auth(manager))
        log = group.logs.first()
        assert group.logs.count() == 9
        assert log.action == OSFGroupLog.NODE_PERMS_UPDATED
        assert log.user == manager
        assert log.params['group'] == group._id
        assert log.params['node'] == project._id
        assert log.params['permission'] == 'read'
        node_log = project.logs.first()

        assert node_log.action == NodeLog.GROUP_UPDATED
        assert node_log.user == manager
        assert node_log.params['group'] == group._id
        assert node_log.params['node'] == project._id
        assert node_log.params['permission'] == 'read'

        project.remove_osf_group(group, Auth(manager))
        project.remove_osf_group(group, Auth(manager))
        assert group.logs.count() == 10
        log = group.logs.first()
        assert log.action == OSFGroupLog.NODE_DISCONNECTED
        assert log.user == manager
        assert log.params['group'] == group._id
        assert log.params['node'] == project._id
        node_log = project.logs.first()

        assert node_log.action == NodeLog.GROUP_REMOVED
        assert node_log.user == manager
        assert node_log.params['group'] == group._id
        assert node_log.params['node'] == project._id
