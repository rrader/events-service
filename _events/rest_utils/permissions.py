from abc import ABCMeta, abstractmethod


class Permission(metaclass=ABCMeta):
    @abstractmethod
    def check(self, request):
        pass
