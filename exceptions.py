class MalformedDataError(Exception):
    def __init__(self, *args):
        super().__init__(*args)

class MalformedRequestError(Exception):
    def __init__(self, *args):
        super().__init__(*args)

class RequestTooLargeError(Exception):
    def __init__(self, *args):
        super().__init__(*args)

class UnrecognisedCommandError(Exception):
    def __init__(self, *args):
        super().__init__(*args)