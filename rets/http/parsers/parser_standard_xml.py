from collections import OrderedDict, defaultdict
from itertools import zip_longest
from typing import Iterable, Sequence, Tuple, Union
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import XML, Element
from io import StringIO

from requests import Response

from rets.errors import RetsParseError, RetsApiError
from rets.http.data import Metadata, SearchResult, SystemMetadata
from rets.http.parsers.base_parser import Parser, ResponseLike


class StandardXmlParser(Parser):
    @classmethod
    def parse_xml(cls, response: ResponseLike) -> dict:
        it = ET.iterparse(StringIO(response.content.decode('utf-8')))

        for _, el in it:
            if '}' in el.tag:
                el.tag = el.tag.split('}', 1)[1]
        root = it.root

        reply_code, reply_text = cls._parse_rets_status(root)
        if reply_code and reply_text != "Operation Successful":
            raise RetsApiError(reply_code, reply_text, response.content)

        return root

    @classmethod
    def parse_capability_urls(cls, response: Response) -> dict:
        raise NotImplementedError

    @classmethod
    def parse_metadata(cls, response: Response) -> Sequence[Metadata]:
        raise NotImplementedError

    @classmethod
    def parse_system(cls, response: Response) -> SystemMetadata:
        raise NotImplementedError

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

        response_elem = elem.find('RETS-RESPONSE')
        if response_elem is None:
            return {}

        property_elem = response_elem.findall('PropertyDetails')

        data = tuple([cls._parse_property_details(d).get("PropertyDetails") for d in property_elem])

        return SearchResult(
            count=count,
            max_rows=elem.find('MAXROWS') is not None,
            data=data,
        )

    @classmethod
    def _parse_rets_status(cls, root: dict) -> Tuple[int, str]:
        """
        If RETS-STATUS exists, the client must use this instead
        of the status from the body-start-line
        """
        rets_status = root.find('RETS-STATUS')
        elem = rets_status if rets_status is not None else root
        return int(elem.get('ReplyCode')), elem.get('ReplyText')

    @classmethod
    def _parse_property_details(cls, t: Element) -> dict:
        # Ref: https://stackoverflow.com/a/10076823/4979620
        d = {t.tag: {} if t.attrib else None}
        children = list(t)
        if children:
            dd = defaultdict(list)
            for dc in map(cls._parse_property_details, children):
                for k, v in dc.items():
                    dd[k].append(v)
            d = {t.tag: {k: v[0] if len(v) == 1 else v for k, v in dd.items()}}
        if t.attrib:
            d[t.tag].update((k, v) for k, v in t.attrib.items())
        if t.text:
            text = t.text.strip()
            if children or t.attrib:
                if text:
                    d[t.tag]['#text'] = text
            else:
                d[t.tag] = text

        return d
