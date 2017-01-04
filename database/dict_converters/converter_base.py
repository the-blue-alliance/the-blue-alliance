class ConverterBase(object):
    @classmethod
    def _listify(cls, thing):
        if not isinstance(thing, list):
            return [thing]
        else:
            return thing

    @classmethod
    def _delistify(cls, things):
        if len(things) == 0:
            return None
        if len(things) == 1:
            return things.pop()
        else:
            return things

    @classmethod
    def constructLocation_v3(cls, model):
        """
        Works for teams and events
        """
        has_nl = model.nl and model.nl.city and model.nl.state_prov and model.nl.country
        return {
            'city': model.nl.city if has_nl else model.city,
            'state_prov': model.nl.state_prov if has_nl else model.state_prov,
            'country': model.nl.country if has_nl else model.country,
            'postal_code': model.nl.postal_code if has_nl else model.postalcode,
            'lat': model.nl.lat_lng.lat if has_nl else None,
            'lng': model.nl.lat_lng.lon if has_nl else None,
            'location_name': model.nl.name if has_nl else None,
            'address': model.nl.formatted_address if has_nl else None,
            'gmaps_place_id': model.nl.place_id if has_nl else None,
            'gmaps_url': model.nl.place_details.get('url') if has_nl else None,
        }
