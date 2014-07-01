import ckan.lib.dictization

import ckan.logic.action
import ckan.logic.schema
import ckan.lib.dictization.model_dictize as model_dictize
import ckan.lib.navl.dictization_functions
import ckan.new_authz as new_authz
import ckan.logic as logic

_check_access = logic.check_access

#from ckan.logic.action.get import organization_list_for_user as core_org_list_for_user
def organization_list_for_user(context, data_dict):
    perm = data_dict.get('permission')
    if perm in ['create_dataset', 'update_dataset', 'delete_dataset']:
        # Create a copy of the data dict, and change the request permission to
        # 'read' which will be granted to all members of a group.
        data_dict = dict(data_dict.items() + {'permission': 'read'}.items())

    #return fb(context, data_dict)
    #return core_org_list_for_user(context, data_dict)
    '''Return the list of organizations that the user is a member of.

    :param permission: the permission the user has against the returned organizations
      (optional, default: ``edit_group``)
    :type permission: string

    :returns: list of dictized organizations that the user is authorized to edit
    :rtype: list of dicts

    '''
    model = context['model']
    user = context['user']

    _check_access('organization_list_for_user',context, data_dict)
    sysadmin = new_authz.is_sysadmin(user)

    orgs_q = model.Session.query(model.Group) \
        .filter(model.Group.is_organization == True) \
        .filter(model.Group.state == 'active')

    if not sysadmin:
        # for non-Sysadmins check they have the required permission

        permission = data_dict.get('permission', 'edit_group')

        roles = ckan.new_authz.get_roles_with_permission(permission)

        if not roles:
            return []
        user_id = new_authz.get_user_id_for_username(user, allow_none=True)
        if not user_id:
            return []

        q = model.Session.query(model.Member) \
            .filter(model.Member.table_name == 'user') \
            .filter(model.Member.capacity.in_(roles)) \
            .filter(model.Member.table_id == user_id)

        group_ids = []
        for row in q.all():
            group_ids.append(row.group_id)

        if not group_ids:
            return []

        orgs_q = orgs_q.filter(model.Group.id.in_(group_ids))

    orgs_list = model_dictize.group_list_dictize(orgs_q.all(), context)
    return orgs_list