class ApiCode:
    def __init__(self, ):
        self.status = 200
        self.code = 0
        self.msg = "请求成功"
        self.data = None

    def success(self, data=None, msg='请求成功'):
        self.msg = msg
        self.data = data
        return self

    def unknown_error(self, msg):
        self.code = -1
        self.msg = msg
        return self

    def params_err(self, form):
        self.code = -1
        self.data = dict()
        msg = ""
        for field in form.errors:
            self.data[field] = form.errors[field]
            msg = form.errors[field][0]
        self.msg = msg
        return self
