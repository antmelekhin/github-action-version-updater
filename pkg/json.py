import jmespath, requests
from packaging.version import Version

def get_json(url: str):
    response = requests.get(url)
    return response.json()

def ensure_list(data):  # pyright: ignore[reportUnknownParameterType, reportMissingParameterType]
    '''Return list of elements for processing'''
    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        return [data]

def get_json_by_max_version(url: str, version_keyname: str, filter: str = None):  # pyright: ignore[reportUnknownParameterType]
    json = get_json(url)
    items = ensure_list(data=json)

    if filter:
        items = jmespath.search(filter, items)

    return max(items, key=lambda item: Version(jmespath.search(version_keyname, item)))  # pyright: ignore[reportUnknownLambdaType]
