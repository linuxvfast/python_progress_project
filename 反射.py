__author__ = 'progress'

class Foo(object):
    def __init__(self):
        self.name = 'linux'

    def func(self):
        return 'func'

obj = Foo()
print(obj.name)
print(hasattr(obj,'name'))
print(getattr(obj,'name'))
setattr(obj,'age',12)
print(getattr(obj,'age'))
# delattr(obj,'age')
# print(getattr(obj,'age'))
