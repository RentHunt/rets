from rets.http.parsers.parse_object import parse_object
from rets.http.parsers.parser_compact import CompactParser
from rets.http.parsers.parser_standard_xml import StandardXmlParser

__all__ = ['parse_object', 'parser_factory', 'CompactParser', 'StandardXmlParser']


def parser_factory(format_):
    try:
        return {'COMPACT-DECODED': CompactParser, 'STANDARD-XML': StandardXmlParser}[
            format_
        ]

    except KeyError:
        raise ValueError('This format is not supported')
