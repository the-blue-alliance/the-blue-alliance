appstats_CALC_RPC_COSTS = False
appstats_RECORD_FRACTION = 0.1


def webapp_add_wsgi_middleware(app):
    from google.appengine.ext.appstats import recording
    app = recording.appstats_wsgi_middleware(app)
    return app
