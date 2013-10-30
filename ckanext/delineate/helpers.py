class AJAXResponse(object):

    def __init__(self):
        self.success = False
        self.message = ''
        self.json_data = ''

    def to_json(self):
        fields = []

        for field in vars(self):
            fields.append(field)
        
        d = {}
        for attr in fields:
            d[attr] = getattr(self, attr)

        import simplejson
        return simplejson.dumps(d)