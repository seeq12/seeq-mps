from seeq.sdk.rest import ApiException
from . import print_red


def add_datalab_project_ace(data_lab_project_id, ace_input, items_api):
    if data_lab_project_id:
        try:
            items_api.add_access_control_entry(id=data_lab_project_id, body=ace_input)
        except Exception as error:
            print_red(error.body)


def get_user_group(group_name, user_groups_api):
    try:
        group = user_groups_api.get_user_groups(name_search=group_name)
        assert len(group.items) != 0, 'No group named "%s" was found' % group_name
        assert len(group.items) == 1, 'More that one group named "%s" was found' % group_name
        return group
    except AssertionError as error:
        print_red(error)
    except ApiException as error:
        print_red(error.body)


def get_user(user_name, users_api):
    try:
        user_ = users_api.get_users(username_search=user_name)
        if len(user_.users) == 0:
            raise ValueError(f'No user named {user_name} was found')
        if len(user_.users) > 1:
            raise ValueError(f'More than one user named {user_name} was found')
        return user_
    except AssertionError as error:
        print_red(error)
    except ApiException as error:
        print_red(error.body)
