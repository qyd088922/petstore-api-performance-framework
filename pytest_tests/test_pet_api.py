# -*- coding: utf-8 -*-
"""pytest 功能用例 + Allure 报告注解（复用同一 PetApi 服务层）。"""
import allure
import pytest


@allure.feature("Pet 宠物模块")
class TestPetApi:

    @allure.story("按状态查询")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_find_by_status(self, pet_api):
        with allure.step("请求 available 状态的宠物列表"):
            resp = pet_api.find_pets_by_status("available")
        with allure.step("校验响应"):
            assert resp.status_code == 200
            assert isinstance(resp.body, list)
            assert len(resp.body) > 0

    @allure.story("新增与回查")
    def test_create_and_get(self, pet_api, data):
        pet_id = data.unique_id()
        payload = data.pet_payload(pet_id)
        pet_api.create_pet(payload)
        try:
            resp = pet_api.get_pet(pet_id)
            assert resp.status_code == 200
            assert resp.body["name"] == payload["name"]
        finally:
            pet_api.delete_pet(pet_id)

    @allure.story("异常场景")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize("pet_id", [987654321987654321])
    def test_get_not_found(self, pet_api, pet_id):
        resp = pet_api.get_pet(pet_id)
        assert resp.status_code == 404
        assert resp.body["code"] == 1
