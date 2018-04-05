from abc import abstractclassmethod
from typing import Iterable, Sequence, Tuple, Union
from xml.etree.ElementTree import XML, Element

from requests import Response
from requests_toolbelt.multipart.decoder import BodyPart

from rets.http.data import Metadata, SearchResult, SystemMetadata

ResponseLike = Union[Response, BodyPart]


class Parser:
    @abstractclassmethod
    def parse_xml(cls, response: ResponseLike) -> Element:
        pass

    @abstractclassmethod
    def parse_capability_urls(cls, response: Response) -> dict:
        """
        Parses the list of capability URLs from the response of a successful Login transaction.

        The capability url list is the set of functions or URLs to which the Login grants access.
        A capability consists of a key and a URL. The list returned from the server in the login
        reply must include URLs for Search, Login, and GetMetadata, and optionally may include
        URLs for Action, ChangePassword, GetObject, LoginComplete, Logout, ServerInformation,
        and Update.

        <RETS ReplyCode="0" ReplyText="Success">
            <RETS-RESPONSE>
                MemberName=member_name
                User=user_id,user_level,user_class,agent_code
                Broker=RETSOFFIC
                MetadataVersion=01.09.02991
                MetadataTimestamp=2016-11-24T05:24:06Z
                MinMetadataTimestamp=2016-11-24T05:24:06Z
                Login=/rets2_1/Login
                Search=/rets2_1/Search
                GetMetadata=/rets2_1/GetMetadata
                GetObject=/rets2_1/GetObject
                Logout=/rets2_1/Logout
            </RETS-RESPONSE>
        </RETS>
        """
        pass

    @abstractclassmethod
    def parse_metadata(cls, response: Response) -> Sequence[Metadata]:
        """
        Parse the information from a GetMetadata transaction.

        <RETS ReplyCode="0" ReplyText="Success">
            <METADATA-RESOURCE Date="2016-11-24T05:24:06Z" Version="01.09.02991">
                <COLUMNS>	ResourceID	StandardName	</COLUMNS>
                <DATA>	ActiveAgent	ActiveAgent	</DATA>
                <DATA>	Office	Office	</DATA>
                <DATA>	OpenHouse	OpenHouse	</DATA>
                <DATA>	Property	Property	</DATA>
                <DATA>	RentalSchedule	RentalSchedule	</DATA>
            </METADATA-RESOURCE>
        </RETS>
        """
        pass

    @abstractclassmethod
    def parse_system(cls, response: Response) -> SystemMetadata:
        """
        Parse the server system information from a SYSTEM GetMetadata transaction.

        <RETS ReplyCode="0" ReplyText="Success">
            <METADATA-SYSTEM Date="2016-11-24T05:24:06Z" Version="01.09.02991">
                <SYSTEM SystemDescription="ARMLS" SystemID="az" TimeZoneOffset="-06:00"/>
                <COMMENTS/>
            </METADATA-SYSTEM>
        </RETS>
        """
        pass

    @abstractclassmethod
    def parse_search(cls, response: Response) -> SearchResult:
        pass
