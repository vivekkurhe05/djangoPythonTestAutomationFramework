from rolepermissions.roles import AbstractUserRole


class Admin(AbstractUserRole):
    available_permissions = {
        'admin_org_data': True,
        'make_payments': True,
        'invite_grantees': True,
        'view_assessments': True,
        'upload_assessment': True,
        'submit_assessment': True
    }


class Manager(AbstractUserRole):
    available_permissions = {
        'admin_org_data': False,
        'make_payments': False,
        'invite_grantees': True,
        'view_assessments': True,
        'upload_assessment': True,
        'submit_assessment': True
    }


class User(AbstractUserRole):
    available_permissions = {
        'admin_org_data': False,
        'make_payments': False,
        'invite_grantees': False,
        'view_assessments': False,
        'upload_assessment': False,
        'submit_assessment': True
    }
