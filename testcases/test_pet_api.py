# -*- coding: utf-8 -*-
"""Pet 接口测试用例。"""
import os

from testcases.base_case import BaseCase


class TestPetApi(BaseCase):

    def test_01_find_pets_by_status(self):
        """按状态查询宠物列表"""
        resp = self.pet_api.find_pets_by_status("available")
        self.assert_status(resp)
        self.assertIsInstance(resp.body, list)
        self.assertGreater(len(resp.body), 0)
        self.assertTrue(all(p.get("status") == "available" for p in resp.body[:20]))

    def test_02_get_pet_by_id(self):
        """根据 ID 查询宠物详情"""
        listed = self.pet_api.find_pets_by_status("available")
        self.assert_status(listed)
        pet_id = listed.body[0]["id"]

        resp = self.pet_api.get_pet(pet_id)
        self.assert_status(resp)
        self.assert_body_dict(resp)
        self.assertEqual(resp.body["id"], pet_id)

    def test_03_create_and_get_pet(self):
        """新增宠物后按 ID 回查"""
        pet_id = self.data.unique_id()
        payload = self.data.pet_payload(pet_id)

        created = self.pet_api.create_pet(payload)
        self.assert_status(created)
        self.assertEqual(created.body["id"], pet_id)
        self.addCleanup(self.pet_api.delete_pet, pet_id)

        fetched = self.pet_api.get_pet(pet_id)
        self.assert_status(fetched)
        self.assertEqual(fetched.body["name"], payload["name"])
        self.assertEqual(fetched.body["status"], "available")

    def test_04_update_pet(self):
        """修改宠物名称和状态并验证生效"""
        pet_id = self.data.unique_id()
        self.assert_status(self.pet_api.create_pet(self.data.pet_payload(pet_id)))
        self.addCleanup(self.pet_api.delete_pet, pet_id)

        updated = self.data.pet_payload(pet_id, name="updated_pet", status="sold")
        resp = self.pet_api.update_pet(updated)
        self.assert_status(resp)

        fetched = self.pet_api.get_pet(pet_id)
        self.assert_status(fetched)
        self.assertEqual(fetched.body["name"], "updated_pet")
        self.assertEqual(fetched.body["status"], "sold")

    def test_05_get_pet_not_found(self):
        """查询不存在的宠物应返回 404"""
        resp = self.pet_api.get_pet(987654321987654321)
        self.assert_status(resp, 404)
        self.assert_body_dict(resp)
        self.assertEqual(resp.body.get("code"), 1)

    def test_06_upload_pet_image(self):
        """上传宠物图片（multipart 封装验证）"""
        pet_id = self.data.unique_id()
        self.assert_status(self.pet_api.create_pet(self.data.pet_payload(pet_id)))
        self.addCleanup(self.pet_api.delete_pet, pet_id)

        image_path = self.data.temp_image()
        self.addCleanup(os.remove, image_path)

        resp = self.pet_api.upload_pet_image(pet_id, image_path, "automation")
        self.assert_status(resp)
        self.assertIn("upload", resp.body.get("message", "").lower())
