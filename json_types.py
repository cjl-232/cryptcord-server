type _JSONPrimitive = bool | int | float | str | None
type _JSONType = _JSONPrimitive | list['_JSONType'] | dict[str, '_JSONType']
type JSONDict = dict[str, _JSONType]