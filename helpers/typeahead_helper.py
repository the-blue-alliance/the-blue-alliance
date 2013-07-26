import unicodedata
import re


class TypeaheadHelper(object):
    @classmethod
    def get_search_keys(self, name):
        """
        search keys for a name are generally the first letter of each word
        in the name, with a few exceptions. Also, if the a letter is a
        unicode character like \xfc, it gets changed to "u"
        """
        keys = set()
        name = unicodedata.normalize('NFKD', unicode(name)).strip().lower()
        for word in name.split(' '):
            for letter in word:
                if letter != '':
                    keys.add(letter)
                if re.match('^[\w-]+$', letter) is not None:
                    break  # continue until first alphanumeric character
        return keys
