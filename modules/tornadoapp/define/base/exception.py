'''
Author: hanlinwu
E-mail: hanlinwu@tencent.com
Description: 异常基类
'''


class RequestException(Exception):
    """ 业务异常基类 """

    def __init__(self, code: int, msg: str, *args, data=None):
        super().__init__(*args)
        self.code = code
        self.msg = msg
        self.data = data if data else {}

    def __repr__(self) -> str:
        return f"{self.msg}"


class BaseException(Exception):
    def __init__(self, code, msg, *args, detail="") -> None:
        super().__init__(*args)
        self.code = code
        self.msg = msg
        self.detail = detail

    def __str__(self) -> str:
        return f"{self.msg}"