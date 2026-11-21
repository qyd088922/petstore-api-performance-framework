# -*- coding: utf-8 -*-
"""Pet 宠物接口封装（Swagger 中的 /pet 分组）。"""
import os

from common.base_client import BaseClient


class PetApi(BaseClient):
    """只暴露业务语义方法，不关心 HTTP 细节。

    功能测试：PetApi()            -> 静默模式
    压测：    PetApi(reporter=...) -> 自动埋点并桥接 Locust
    """

    def find_pets_by_status(self, status="available"):
        return self.get("/pet/findByStatus", params={"status": status})

    def find_pets_by_tags(self, tags):
        return self.get("/pet/findByTags", params={"tags": ",".join(tags)})

    def get_pet(self, pet_id):
        return self.get("/pet/%s" % pet_id)

    def create_pet(self, payload):
        return self.post("/pet", payload=payload)

    def update_pet(self, payload):
        return self.put("/pet", payload=payload)

    def update_pet_with_form(self, pet_id, name=None, status=None):
        data = {}
        if name is not None:
            data["name"] = name
        if status is not None:
            data["status"] = status
        return self.post("/pet/%s" % pet_id, data=data)

    def delete_pet(self, pet_id):
        return self.delete("/pet/%s" % pet_id)

    def upload_pet_image(self, pet_id, file_path, metadata=None):
        """上传宠物图片（multipart/form-data）。"""
        with open(file_path, "rb") as fh:
            files = {"file": (os.path.basename(file_path), fh, "image/png")}
            data = {"additionalMetadata": metadata} if metadata else None
            return self.post("/pet/%s/uploadImage" % pet_id, data=data, files=files)
