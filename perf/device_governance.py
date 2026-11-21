# -*- coding: utf-8 -*-
"""设备绑定压测的数据治理：批量激活 + 自动解绑。

思路：把"设备"建模为 Petstore 的 pet 资源（id 即设备号），
压测前置批量激活（创建）设备并绑定，压测后置自动解绑并回收（删除），
避免脏数据累积，保证多轮压测可重复执行。
"""
from api.pet_api import PetApi
from common.data_factory import DataFactory
from common.logger import get_logger
from config.perf_config import HTTP_HOST

log = get_logger("petstore.device")


class DeviceGovernance(object):
    def __init__(self, host=HTTP_HOST, batch_size=20):
        self.api = PetApi(host=host)
        self.batch_size = batch_size
        self.activated_ids = []

    def setUp(self):
        """前置：批量激活设备（创建 pet），返回设备 id 列表。"""
        self.activated_ids = []
        for _ in range(self.batch_size):
            payload = DataFactory.pet_payload(status="available")
            resp = self.api.create_pet(payload)
            if resp is not None and resp.body:
                self.activated_ids.append(resp.body["id"])
        log.info("批量激活设备 %d 台" % len(self.activated_ids))
        return self.activated_ids

    def bind(self, device_id):
        """绑定：更新设备状态为 sold，模拟占用。"""
        payload = DataFactory.pet_payload(pet_id=device_id, status="sold")
        return self.api.update_pet(payload)

    def tearDown(self):
        """后置：自动解绑并回收设备，保证数据治理闭环。"""
        released = 0
        for device_id in self.activated_ids:
            resp = self.api.delete_pet(device_id)
            if resp is not None and resp.ok:
                released += 1
        log.info("自动解绑并回收设备 %d 台" % released)
        self.activated_ids = []
        return released

    def __enter__(self):
        self.setUp()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.tearDown()
        return False
