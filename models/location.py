from google.appengine.ext import ndb


class Location(ndb.Model):
    """
    Used for storing location information for a Team or Event
    """
    name = ndb.StringProperty()  # Name of the place, like "Leland High School" or "San Jose State Event Center"
    formatted_address = ndb.StringProperty()  # Like '6677 Camden Ave, San Jose, CA 95120, USA"
    lat_lng = ndb.GeoPtProperty()  # Latitude/longitude
    street_number = ndb.StringProperty()  # Like ""6677
    street = ndb.StringProperty()  # Like "Camden Avenue"
    city = ndb.StringProperty()  # Like "San Jose"
    state_prov = ndb.StringProperty()  # Like "California"
    state_prov_short = ndb.StringProperty()  # Like "CA"
    country = ndb.StringProperty()  # Like "United States"
    country_short = ndb.StringProperty()  # Like "US"
    postal_code = ndb.StringProperty()  # String because it can be like "95126-1215"
