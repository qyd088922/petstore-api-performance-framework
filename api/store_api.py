# -*- coding: utf-8 -*-
"""Store 商店订单接口封装（Swagger 中的 /store 分组）。"""
from common.base_client import BaseClient


class StoreApi(BaseClient):
    def get_inventory(self):
        return self.get("/store/inventory")

    def place_order(self, payload):
        return self.post("/store/order", payload=payload)

    def get_order(self, order_id):
        return self.get("/store/order/%s" % order_id)

    def delete_order(self, order_id):
        return self.delete("/store/order/%s" % order_id)
