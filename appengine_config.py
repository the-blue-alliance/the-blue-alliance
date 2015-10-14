import tba_config

if tba_config.CONFIG['env'] == 'prod':
    appstats_RECORD_FRACTION = 0.1
else:
    appstats_CALC_RPC_COSTS = True


def webapp_add_wsgi_middleware(app):
    from google.appengine.ext.appstats import recording
    app = recording.appstats_wsgi_middleware(app)
    return app
