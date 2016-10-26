class AccountPermissions(object):
    REVIEW_MEDIA = 1
    REVIEW_OFFSEASON_EVENTS = 2
    REVIEW_APIWRITE = 3

    permissions = {
        REVIEW_MEDIA: {
            "name": "REVIEW_MEDIA",
            "description": "Can review (accept/reject) media suggestions",
        },
        REVIEW_OFFSEASON_EVENTS: {
            "name": "REVIEW_OFFSEASON_EVENTS",
            "description": "Can accept and create offseason events from suggestions"
        },
        REVIEW_APIWRITE: {
            "name": "REVIEW_APIWRITE",
            "description": "Can review and grant requests for trusted API tokens"
        }
    }
