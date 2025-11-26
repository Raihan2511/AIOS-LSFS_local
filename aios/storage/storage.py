# /home/sysadm/Raihan/AIOS-LSFS_local/aios/storage/storage.py
import os

import pickle

import zlib
import json

from .filesystem.lsfs import LSFS

from cerebrum.storage.apis import StorageResponse

class StorageManager:
    def __init__(self, root_dir, use_vector_db=True, filesystem_type="lsfs"):
        self.use_vector_db = use_vector_db
        self.filesystem_type = filesystem_type
        self.root_dir = root_dir
        # self.root_dir = os.path.abspath(root_dir)
        os.makedirs(self.root_dir, exist_ok=True)
        if filesystem_type == "lsfs":
            self.filesystem = LSFS(root_dir, use_vector_db)

    def address_request(self, agent_request):
        result = self.filesystem.address_request(agent_request)
        # --- FIX: PREVENT SERVER CRASH ---
        # The StorageResponse Pydantic model demands a string.
        # If result is a list (from retrieve) or dict (from share), convert it.
        if not isinstance(result, str):
            try:
                # Pretty print JSON for better readability in terminal
                result = json.dumps(result, indent=2)
            except:
                result = str(result)
        return StorageResponse(
            response_message=result,
            finished=True
        )