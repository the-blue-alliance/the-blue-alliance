from BeautifulSoup import NavigableString

def recurseUntilString(node):
    """
    Digs through HTML that Word made worse.
    Written to deal with http://www2.usfirst.org/2011comp/Events/cmp/matchresults.html
    """
    if node.string is not None:
        return node.string
    if isinstance(node, NavigableString):
        return node
    if hasattr(node, 'contents'):
        for content in node.contents:
            result = recurseUntilString(content)
            result = result.strip().replace('\r', '').replace('\n', '').replace('  ', ' ')
            if result is not None and result != "":
                return result
    return None