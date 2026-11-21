# -*- coding: utf-8 -*-
"""pytest 全局夹具：复用与 unittest 完全相同的业务 API 对象。

功能测试职责由 pytest 承担，压测职责由 Locust 承担，二者共用 api/ 服务层。
"""
import pytest

from api.pet_api import PetApi
from api.store_api import StoreApi
from api.user_api import UserApi
from common.data_factory import DataFactory


@pytest.fixture(scope="session")
def pet_api():
    return PetApi()


@pytest.fixture(scope="session")
def store_api():
    return StoreApi()


@pytest.fixture(scope="session")
def user_api():
    return UserApi()


@pytest.fixture
def data():
    return DataFactory()
