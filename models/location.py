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

    # Google Maps stuff
    place_id = ndb.StringProperty()  # Google Maps place ID
    place_details = ndb.JsonProperty()  # Entire Place Details result from Google in case it comes in handy

    def __init__(self, *args, **kw):
        self._city_state_country = None
        super(Location, self).__init__(*args, **kw)

    @property
    def country_short_if_usa(self):
        if self.country == 'United States':
            return 'USA'
        else:
            return self.country

    @property
    def city_state_country(self):
        if not self._city_state_country:
            location_parts = []
            if self.city:
                location_parts.append(self.city)
            if self.state_prov_short:
                location_parts.append(self.state_prov_short)
            if self.country_short_if_usa:
                location_parts.append(self.country_short_if_usa)
            self._city_state_country = ', '.join(location_parts)
        return self._city_state_country
