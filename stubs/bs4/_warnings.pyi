class GuessedAtParserWarning(UserWarning):
    MESSAGE: str

class UnusualUsageWarning(UserWarning): ...

class MarkupResemblesLocatorWarning(UnusualUsageWarning):
    GENERIC_MESSAGE: str
    URL_MESSAGE: str
    FILENAME_MESSAGE: str

class AttributeResemblesVariableWarning(UnusualUsageWarning, SyntaxWarning):
    MESSAGE: str

class XMLParsedAsHTMLWarning(UnusualUsageWarning):
    MESSAGE: str
