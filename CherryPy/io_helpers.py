from communication_helpers import create_message


def create_error_response(status, tracking_code, method_type, error, broker_type, source, member_id):
    return create_message(method=method_type, record={}, broker_type=broker_type, source=source,
                          tracking_code=tracking_code, error_code=status,
                          is_successful=False, error_description=error, member_id=member_id)


def create_success_response(tracking_code, method_type, response, broker_type, source, member_id):
    return create_message(method=method_type, record=response, broker_type=broker_type, source=source,
                          tracking_code=tracking_code, error_code=0,
                          is_successful=True, error_description="", member_id=member_id)


def check_schema(data, schema):
    invalid_field_name = None
    for field in data.keys():
        if field == "_id":
            continue
        if field not in schema.keys():
            invalid_field_name = field

    if invalid_field_name is not None:
        raise InvalidFieldName(invalid_field_name)


def check_full_schema(data, schema):
    schema_keys = set(schema.keys())

    data_keys = set(data.keys())
    if "_id" in data_keys:
        data_keys.remove("_id")

    extra_keys = data_keys - schema_keys
    if len(extra_keys) > 0:
        for k in list(extra_keys):
            del data[k]

    if len(schema_keys - data_keys) > 0:
        for null_key in list(schema_keys - data_keys):
            data[null_key] = None

    return data


def preprocess(data, schema):
    for field in data:
        if data[field] is None and field in schema.keys() and "_null_value" in schema[field].keys():
            data[field] = schema[field]["_null_value"]
        if field in schema.keys() and "_type" in schema[field].keys():
            data[field] = schema[field]["_type"](data[field])
    return data


def field_is_empty(field, _field_name, schema):
    if field is None or field == "" or field == schema[_field_name]["_null_value"]:
        return True
    else:
        return False


class UserInputError(Exception):
    def __init__(self, message, error_code):
        super(UserInputError, self).__init__(message)
        self.error_code = error_code


class DependencyNotMet(UserInputError):
    def __init__(self, message):
        super(DependencyNotMet, self).__init__(message, 801)


class MemberNotFoundError(UserInputError):
    def __init__(self):
        super(MemberNotFoundError, self).__init__("INVALID member_id", 605)


class RequiredFieldError(UserInputError):
    def __init__(self, field_name):
        super(RequiredFieldError, self).__init__("Field %s is required." % field_name, 602)


class InvalidFieldName(UserInputError):
    def __init__(self, field_name):
        super(InvalidFieldName, self).__init__("Field %s is invalid." % field_name, 604)


class ForumNotFoundError(UserInputError):
    def __init__(self):
        super(ForumNotFoundError, self).__init__("INVALID zero id", 901)


class InvalidInputField(UserInputError):
    def __init__(self, field_name):
        super(InvalidInputField, self).__init__("Invalid value for field with name '%s'" % field_name, 603)
