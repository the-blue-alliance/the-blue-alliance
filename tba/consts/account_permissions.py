class AccountPermissions(object):
    REVIEW_MEDIA = 1
    REVIEW_OFFSEASON_EVENTS = 2
    REVIEW_APIWRITE = 3
    REVIEW_DESIGNS = 4
    REVIEW_EVENT_MEDIA = 5
    OFFSEASON_EVENTWIZARD = 6

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
        },
        REVIEW_DESIGNS: {
            "name": "REVIEW_DESIGNS",
            "description": "Can link CAD models and Behind the Design blog posts to team robot profiles"
        },
        REVIEW_EVENT_MEDIA: {
            "name": "REVIEW_EVENT_MEDIA",
            "description": "Can approve media (non-match video) linked to events"
        },
        OFFSEASON_EVENTWIZARD: {
            "name": "OFFSEASON_EVENTWIZARD",
            "description": "Can use the eventwizard for any offseason event",
        },
    }
