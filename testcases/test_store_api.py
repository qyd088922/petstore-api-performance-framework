# -*- coding: utf-8 -*-
"""Store 接口测试用例。"""
from testcases.base_case import BaseCase


class TestStoreApi(BaseCase):

    def test_01_get_inventory(self):
        """查询库存清单"""
        resp = self.store_api.get_inventory()
        self.assert_status(resp)
        self.assert_body_dict(resp)
        self.assertGreater(len(resp.body), 0)

    def test_02_place_and_get_order(self):
        """下单后回查订单"""
        order_id = self.data.unique_id()
        payload = self.data.order_payload(order_id, quantity=3, status="placed")

        placed = self.store_api.place_order(payload)
        self.assert_status(placed)
        self.assert_body_dict(placed)
        self.assertEqual(placed.body["id"], order_id)
        self.assertEqual(placed.body["quantity"], 3)
        self.addCleanup(self.store_api.delete_order, order_id)

        fetched = self.store_api.get_order(order_id)
        self.assert_status(fetched)
        self.assertEqual(fetched.body["status"], "placed")
        self.assertEqual(fetched.body["petId"], payload["petId"])

    def test_03_delete_order(self):
        """删除订单"""
        order_id = self.data.unique_id()
        self.assert_status(self.store_api.place_order(self.data.order_payload(order_id)))

        resp = self.store_api.delete_order(order_id)
        self.assert_status(resp)
        self.assertEqual(str(order_id), str(resp.body.get("message")))
