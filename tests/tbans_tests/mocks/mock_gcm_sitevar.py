import json

from models.sitevar import Sitevar


def stub_gcm_sitevar():
    gcm_sitevar = Sitevar(
        id='gcm.serverKey',
        values_json=json.dumps({
            'gcm_key': 'abcd',
        })
    )
    gcm_sitevar.put()
