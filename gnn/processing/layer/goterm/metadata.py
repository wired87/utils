from extract_data.functions.base_request import abase_request
from extract_data.functions.goterm.urls import metadata


async def metadata_term(item, session):
    url = metadata(item)
    content = await abase_request(url=url, session=session)
    if content:
        return content
