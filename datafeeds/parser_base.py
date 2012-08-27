class ParserBase(object):
	"""
	Provides a basic structure for parsing pages.
	Parsers are not allowed to return Model objects, only dictionaries.
	"""

	@classmethod
	def parse(self, html):
		"""
		Given a chunk of HTML, return a result dictionary.
		"""
		raise NotImplementedError("No parse method!")