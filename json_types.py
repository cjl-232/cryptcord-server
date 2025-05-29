type _JSONPrimitive = bool | int | float | str | None
type JSONType = _JSONPrimitive | list['JSONType'] | dict[str, 'JSONType']
type JSONDict = dict[str, JSONType]