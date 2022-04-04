class Multiplexer:
    def __init__(self):
        self.mapping = {
            "INTERNAL": {
                "ADMIN": "BF_INTERNAL",
                "MEMBER": "BF_INTERNAL",
                "OPERATOR": "BF_INTERNAL",
                "FREE": "BF_INTERNAL",
                "MARKETING": "BF_INTERNAL",
            },
            "ADMIN": {
                "ADMIN": "BF_ADMIN",
                "MEMBER": None,
                "OPERATOR": "BF_OPERATOR",
                "FREE": None,
                "MARKETING": None,
            },
            "CLUB": {
                "ADMIN": "BF_MEMBER",
                "MEMBER": "BF_MEMBER",
                "OPERATOR": "BF_MEMBER",
                "FREE": "BF_FREE",
                "MARKETING": "BF_MEMBER",
            },
            "BI": {
                "ADMIN": "BF_ADMIN",
                "MEMBER": None,
                "OPERATOR": None,
                "FREE": None,
                "MARKETING": None,
            },
            "ALGO": {
                "ADMIN": None,
                "MEMBER": None,
                "OPERATOR": None,
                "FREE": None,
                "MARKETING": None,
            },
            "SITE": {
                "ADMIN": "BF_ADMIN",
                "MEMBER": "BF_MEMBER",
                "OPERATOR": "BF_MEMBER",
                "FREE": "BF_FREE",
                "MARKETING": "BF_MEMBER",
            },
            "MARKETING": {
                "ADMIN": "BF_ADMIN",
                "MEMBER": None,
                "OPERATOR": "BF_OPERATOR",
                "FREE": None,
                "MARKETING": "BF_MARKETING",
            },
            "BARSAM": {
                "ADMIN": "BF_BARSAM",
                "MEMBER": None,
                "OPERATOR": None,
                "FREE": None,
                "MARKETING": None,
            },

        }

    def is_internal(self, source, member_category):
        return self.check_role(member_category=member_category, role="BF_INTERNAL", source=source)

    def is_admin(self, source, member_category):
        return self.check_role(member_category=member_category, role="BF_ADMIN", source=source)

    def is_member(self, source, member_category):
        return self.check_role(member_category=member_category, role="BF_MEMBER", source=source)

    def is_free(self, source, member_category):
        return self.check_role(member_category=member_category, role="BF_FREE", source=source)

    def is_algo(self, source, member_category):
        return self.check_role(member_category=member_category, role="BF_ALGO", source=source)

    def is_bi(self, source, member_category):
        return self.check_role(member_category=member_category, role="BF_BI", source=source)

    def is_operator(self, source, member_category):
        return self.check_role(member_category=member_category, role="BF_OPERATOR", source=source)

    def is_marketer(self, source, member_category):
        return self.check_role(member_category=member_category, role="BF_MARKETING", source=source)

    def is_barsam(self, source, member_category):
        return self.check_role(member_category=member_category, role="BF_BARSAM", source=source)

    def check_role(self, member_category, role, source):
        if source.upper() not in self.mapping.keys():
            return False

        destination = self.mapping[source.upper()][member_category.upper()]

        if destination == role:
            return True
        else:
            return False
