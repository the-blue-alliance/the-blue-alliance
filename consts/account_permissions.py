class AccountPermissions(object):
    SEE_ADMIN = 0
    MUTATE_DATA = 1
    ADMIN_USERS = 2
    NOT_REAL = 3

    descriptions = {
        SEE_ADMIN: 'Can access the admin panel.',
        MUTATE_DATA: 'Can mutate data.',
        ADMIN_USERS: 'Can administer user permissions.',
        NOT_REAL: 'A fake permission.'
    }
