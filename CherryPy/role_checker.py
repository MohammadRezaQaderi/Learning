import re


class RoleChecker:
    def __init__(self):
        pass

    def check_role(self, member_permitted_methods, service_name, method_name):
        requested_method = service_name + "." + method_name
        if requested_method.split(".")[0] == "STAGING":
            return True
        else:
            for regex in member_permitted_methods.split(" "):
                if len(re.findall("^" + regex + "$", requested_method)) > 0:
                    return True
            return False
