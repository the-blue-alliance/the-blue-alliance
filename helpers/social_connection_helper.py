

class SocialConnectionHelper(object):

    @classmethod
    def group_by_type(cls, connections):
        conns_by_type = {}
        for conn in connections:
            slug_name = conn.slug_name
            if slug_name in conns_by_type:
                conns_by_type[slug_name].append(conn)
            else:
                conns_by_type[slug_name] = [conn]
        return conns_by_type
