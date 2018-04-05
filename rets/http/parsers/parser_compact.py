from collections import OrderedDict
from itertools import zip_longest
from typing import Iterable, Sequence, Tuple, Union
from xml.etree.ElementTree import XML, Element

from requests import Response

from rets.errors import RetsParseError, RetsApiError
from rets.http.data import Metadata, SearchResult, SystemMetadata
from rets.http.parsers.base_parser import Parser, ResponseLike


class CompactParser(Parser):

    @classmethod
    def parse_xml(cls, response: ResponseLike) -> Element:
        root = XML(response.content)

        reply_code, reply_text = cls._parse_rets_status(root)
        if reply_code and reply_text != "Operation Successful":
            raise RetsApiError(reply_code, reply_text, response.content)

        return root

    @classmethod
    def parse_capability_urls(cls, response: Response) -> dict:
        elem = cls.parse_xml(response)
        response_elem = elem.find('RETS-RESPONSE')
        if response_elem is None:
            return {}

        raw_arguments = response_elem.text.strip().split('\n')
        return dict((s.strip() for s in arg.split('=', 1)) for arg in raw_arguments)

    @classmethod
    def parse_metadata(cls, response: Response) -> Sequence[Metadata]:
        elem = cls.parse_xml(response)
        metadata_elems = [e for e in elem.findall('*') if e.tag.startswith('METADATA-')]
        if metadata_elems is None:
            return ()

        def parse_metadata_elem(elem: Element) -> Metadata:
            """ Parses a single <METADATA-X> element """
            return Metadata(
                type_=elem.tag.split('-', 1)[1],
                resource=elem.get('Resource'),
                class_=elem.get('Class'),
                data=tuple(cls._parse_data(elem)),
            )

        return tuple(
            parse_metadata_elem(metadata_elem) for metadata_elem in metadata_elems
        )

    @classmethod
    def parse_system(cls, response: Response) -> SystemMetadata:
        elem = cls.parse_xml(response)
        metadata_system_elem = cls._find_or_raise(elem, 'METADATA-SYSTEM')
        system_elem = cls._find_or_raise(metadata_system_elem, 'SYSTEM')
        comments_elem = metadata_system_elem.find('COMMENTS')
        return SystemMetadata(
            system_id=system_elem.get('SystemID'),
            system_description=system_elem.get('SystemDescription'),
            system_date=metadata_system_elem.get('Date'),
            system_version=metadata_system_elem.get('Version'),
            # Optional fields
            time_zone_offset=system_elem.get('TimeZoneOffset'),
            comments=comments_elem and (comments_elem.text or None),
        )

    @classmethod
    def parse_search(cls, response: Response) -> SearchResult:
        try:
            elem = cls.parse_xml(response)
        except RetsApiError as e:
            if e.reply_code == 20201:  # No records found
                return SearchResult(0, False, ())

            raise

        count_elem = elem.find('COUNT')
        if count_elem is not None:
            count = int(count_elem.get('Records'))
        else:
            count = None

        try:
            data = tuple(cls._parse_data(elem))
        except RetsParseError:
            data = None

        return SearchResult(
            count=count,
            # python xml.etree.ElementTree.Element objects are always considered false-y
            max_rows=elem.find('MAXROWS') is not None,
            data=data,
        )

    @classmethod
    def _parse_rets_status(cls, root: Element) -> Tuple[int, str]:
        """
        If RETS-STATUS exists, the client must use this instead
        of the status from the body-start-line
        """
        rets_status = root.find('RETS-STATUS')
        elem = rets_status if rets_status is not None else root
        return int(elem.get('ReplyCode')), elem.get('ReplyText')

    @classmethod
    def _parse_data(cls, elem: Element) -> Iterable[dict]:
        """
        Parses a generic container element enclosing a single COLUMNS and multiple DATA elems, and
        returns a generator of dicts with keys given by the COLUMNS elem and values given by each
        DATA elem. The container elem may optionally contain a DELIMITER elem to define the delimiter
        used, otherwise a default of '\t' is assumed.

        <RETS ReplyCode="0" ReplyText="Success">
            <DELIMITER value="09"/>
            <COLUMNS>	LIST_87	LIST_105	LIST_1	</COLUMNS>
            <DATA>	2016-12-01T00:08:10	5489015	20160824051756837742000000	</DATA>
            <DATA>	2016-12-01T00:10:02	5497756	20160915055426038684000000	</DATA>
            <DATA>	2016-12-01T00:10:26	5528935	20161123230848928777000000	</DATA>
            <DATA>	2016-12-01T00:10:52	5528955	20161123234916869427000000	</DATA>
            <DATA>	2016-12-01T00:14:31	5530021	20161127221848669500000000	</DATA>
        </RETS>
        """
        delimiter = cls._parse_delimiter(elem)

        columns_elem = cls._find_or_raise(elem, 'COLUMNS')
        columns = cls._parse_data_line(columns_elem, delimiter)

        data_elems = elem.findall('DATA')

        return (
            OrderedDict(zip_longest(columns, cls._parse_data_line(data, delimiter)))
            for data in data_elems
        )

    @classmethod
    def _find_or_raise(cls, elem: Element, child_elem_name: str) -> Element:
        child = elem.find(child_elem_name)
        if child is None:
            raise RetsParseError('Missing %s element' % child_elem_name)

        return child

    @classmethod
    def _parse_data_line(cls, elem: Element, delimiter: str = '\t') -> Sequence[str]:
        # DATA elems using the COMPACT format and COLUMN elems all start and end with delimiters
        return elem.text.split(delimiter)[1:-1]

    @classmethod
    def _parse_delimiter(cls, elem: Element) -> str:
        delimiter_elem = elem.find('DELIMITER')
        if delimiter_elem is None:
            return '\t'

        return chr(int(delimiter_elem.get('value')))
