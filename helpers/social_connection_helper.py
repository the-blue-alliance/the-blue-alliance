

class SocialConnectionHelper(object):

    @classmethod
    def group_by_type(cls, connections):
        conns_by_type = {}
        for conn in connections:
            conn_type = conn.social_type_enum
            if conn_type in conns_by_type:
                conns_by_type[conn_type].append(conn)
            else:
                conns_by_type[conn_type] = [conn]
        return conns_by_type
