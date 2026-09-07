from packaging.version import Version
from ruamel.yaml import YAML

yaml = YAML()
yaml.explicit_start = True
yaml.indent(sequence=4, offset=2)
yaml.preserve_quotes = True
yaml.width = 4096

def update_version(filename: str, keyname: str, latest_version: str):  # pyright: ignore[reportUnknownParameterType]
    try:
        with open(file=filename, mode='r') as f:
            data = yaml.load(stream=f)
    except FileNotFoundError:
        return 'file_not_found', None

    keys = keyname.split(sep='.')
    temp = data

    for key in keys[:-1]:
        temp = temp[key]

    target_key = keys[-1]
    if target_key not in temp:
        return 'key_not_found', None

    current_version = temp[target_key]

    parsed_current = Version(version=str(current_version))
    parsed_latest = Version(version=str(latest_version))

    if parsed_current < parsed_latest:
        temp[keys[-1]] = latest_version
        with open(file=filename, mode='w') as f:
            yaml.dump(data, stream=f)
        return 'updated', current_version
    elif parsed_current > parsed_latest:
        return 'newer', current_version
    else:
        return 'equal', current_version
