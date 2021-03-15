import re


class ParserInputException(Exception):
    pass


class ParserBase(object):
    """
    Provides a basic structure for parsing pages.
    Parsers are not allowed to return Model objects, only dictionaries.
    """

    @classmethod
    def parse(self, html):
        """
        Given a chunk of HTML, return a (result dictionary, more_pages) tuple
        """
        raise NotImplementedError("No parse method!")

    @classmethod
    def _recurseUntilString(self, node):
        """
        Digs through HTML that Word made worse.
        Written to deal with http://www2.usfirst.org/2011comp/Events/cmp/matchresults.html
        """
        from bs4 import NavigableString
        if node.string is not None:
            return re.sub('\s+', ' ', node.string.replace(u'\xa0', ' ')).strip()  # remove multiple whitespaces
        if isinstance(node, NavigableString):
            return node
        if hasattr(node, 'contents'):
            results = []
            for content in node.contents:
                result = self._recurseUntilString(content)
                if result is not None:
                    result = result.strip().replace('\r', '').replace('\n', '').replace('  ', ' ')
                if result is not None and result != "":
                    results.append(result)
            if results != []:
                return ' '.join(results)
        return None

    @classmethod
    def _html_unescape(cls, html):
        import HTMLParser
        h = HTMLParser.HTMLParser()
        return h.unescape(html)

    @classmethod
    def _html_unescape_items(cls, d):
        """
        Unescapes HTML in a dict
        """
        import HTMLParser
        h = HTMLParser.HTMLParser()
        for key, value in d.items():
            try:
                d[key] = h.unescape(value)
            except TypeError:
                continue
