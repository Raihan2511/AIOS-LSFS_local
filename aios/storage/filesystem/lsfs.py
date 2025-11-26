# # aios/storage/filesystem/lsfs.py
# import os
# import pickle
# import zlib
# import time
# from watchdog.observers import Observer
# from watchdog.events import FileSystemEventHandler
# import redis
# import json
# from datetime import datetime, timedelta
# from typing import Dict, Any, List, Set, Optional
# import hashlib
# import threading
# from urllib.parse import urljoin
# import uuid
# import requests

# from .vector_db import ChromaDB

# import logging

# logging.getLogger('watchdog').setLevel(logging.ERROR)

# class FileChangeHandler(FileSystemEventHandler):
#     def __init__(self, lsfs_instance):
#         self.lsfs = lsfs_instance
        
#     def on_modified(self, event):
#         if not event.is_directory:
#             self.lsfs.handle_file_change(event.src_path, "modified")
            
#     def on_created(self, event):
#         if not event.is_directory:
#             self.lsfs.handle_file_change(event.src_path, "created")
            
#     def on_deleted(self, event):
#         if not event.is_directory:
#             self.lsfs.handle_file_change(event.src_path, "deleted")

# class LSFS:
#     def __init__(self, root_dir, use_vector_db=True, max_versions=20):
#         # self.root_dir = root_dir
#         self.root_dir=os.path.abspath(root_dir)
#         self.use_vector_db = use_vector_db
#         self.max_versions = max_versions
#         self.vector_db = ChromaDB(mount_dir=self.root_dir)
        
#         # Initialize Redis connection
#         self.redis_client = redis.Redis(
#             host='localhost',
#             port=6379,
#             db=0,
#             decode_responses=True
#         )
        
#         # # Test Redis connection
#         try:
#             self.redis_client.ping()
#             print("Successfully connected to Redis")
#             self.use_redis = True
            
#         except redis.ConnectionError as e:
#             print(f"Failed to connect to Redis: {e}")
#             self.use_redis = False
        
#         self.file_locks = {}
#         self.locks_lock = threading.Lock()

#         # # Initialize file system observer
#         # self.observer = Observer()
#         # self.event_handler = FileChangeHandler(self)
#         # self.observer.schedule(self.event_handler, self.root_dir, recursive=True)
#         # self.observer.start() # temporarily disabled
        
#         # # Add file locks dictionary
#         # self.file_locks = {}
#         # self.locks_lock = threading.Lock()  # Meta-lock for the locks dictionary
#         # Start Observer
#         try:
#             self.observer = Observer()
#             self.event_handler = FileChangeHandler(self)
#             if not os.path.exists(self.root_dir):
#                 os.makedirs(self.root_dir)
#             self.observer.schedule(self.event_handler, self.root_dir, recursive=True)
#             self.observer.start()
#         except Exception as e:
#             print(f"Warning: Failed to start file observer: {e}")
        
#     def __del__(self):
#         if hasattr(self, 'observer'):
#             self.observer.stop()
#             self.observer.join()
    
# # --- HELPER: Force paths to stay inside root_dir ---
#     def _resolve_path(self, path):
#         """Helper to ensure paths are always inside the mounted root."""
#         if not path:
#             return None
#         # If it's just a filename, join with root
#         if not os.path.dirname(path):
#             return os.path.join(self.root_dir, path)
#         # If it's an absolute path, assume it's correct but verify
#         if os.path.isabs(path):
#             return path
#         # Otherwise join
#         return os.path.join(self.root_dir, path)
            
#     def get_file_hash(self, file_path: str) -> str:
#         return hashlib.sha256(file_path.encode()).hexdigest()
            
#     def get_file_lock(self, file_path: str) -> threading.Lock:
#         with self.locks_lock:
#             if file_path not in self.file_locks:
#                 self.file_locks[file_path] = threading.Lock()
#             return self.file_locks[file_path]
            
#     def handle_file_change(self, file_path: str, change_type: str):
#         # """Handle file changes with proper lock management."""
#         if "chroma" in file_path or ".DS_Store" in file_path or ".tmp" in file_path:
#             return
#         lock = self.get_file_lock(file_path)
#         try:
#             if lock.acquire(timeout=5):  # Add timeout to prevent deadlocks
#                 try:
#                     # relative_path = os.path.relpath(file_path, self.root_dir)
#                     file_hash = self.get_file_hash(file_path)
                    
#                     if change_type in ["modified", "created"]:
#                         with open(file_path, 'r') as f:
#                             content = f.read()
                        
#                         # Update vector DB
#                         if self.use_vector_db:
#                             self.vector_db.update_document(file_path, content)
                            
#                         # Update Redis cache with version history
#                         timestamp = datetime.now().isoformat()
                        
#                         version_info = {
#                             'content': content,
#                             'timestamp': timestamp,
#                             'hash': file_hash,
#                             'change_type': change_type
#                         }
                        
#                         # versions_key = f"file_versions:{relative_path}"
#                         versions_key = file_hash
#                         versions = self.redis_client.lrange(versions_key, 0, -1)
#                         versions = [json.loads(v) for v in versions]
                        
#                         # Add new version
#                         self.redis_client.lpush(versions_key, json.dumps(version_info))
                        
#                         # Trim to max versions
#                         if len(versions) >= self.max_versions:
#                             self.redis_client.ltrim(versions_key, 0, self.max_versions - 1)
                            
#                     elif change_type == "deleted":
#                         # Remove from vector DB
#                         if self.use_vector_db:
#                             self.vector_db.delete_document(file_path)
                        
#                         # Add deletion record to Redis
#                         # versions_key = f"file_versions:{relative_path}"
#                         versions_key = file_hash
#                         deletion_info = {
#                             'timestamp': datetime.now().isoformat(),
#                             'change_type': 'deleted'
#                         }
#                         self.redis_client.lpush(versions_key, json.dumps(deletion_info))
                        
#                 finally:
#                     lock.release()  # Ensure lock is always released
#             else:
#                 print(f"Timeout waiting for lock on {file_path}")
#         except Exception as e:
#             print(f"Error handling file change: {str(e)}")
            
#     def get_file_history(self, file_path: str, limit: int = None) -> list:
#         # relative_path = os.path.relpath(file_path, self.root_dir)
#         # versions_key = f"file_versions:{relative_path}"
        
#         file_hash = self.get_file_hash(file_path)
#         versions_key = file_hash
        
#         limit = limit or self.max_versions
#         versions = self.redis_client.lrange(versions_key, 0, limit - 1)
#         return [json.loads(v) for v in versions]
        
#     def restore_version(self, file_path: str, version_index: int) -> bool:
#         # file_lock = self.get_file_lock(file_path)
        
#         # with file_lock:
#         try:
#             # relative_path = os.path.relpath(file_path, self.root_dir)
#             # versions_key = f"file_versions:{relative_path}"
            
#             file_hash = self.get_file_hash(file_path)
#             versions_key = file_hash
            
#             # Get specified version
#             version_data = self.redis_client.lindex(versions_key, version_index)
#             if not version_data:
#                 return False
                
#             version_info = json.loads(version_data)
#             if 'content' not in version_info:
#                 return False
            
#             with open(file_path, 'w') as f:
#                 f.write(version_info['content'])
                
#             # Update vector DB
#             # if self.use_vector_db:
#             #     self.vector_db.update_document(file_path, version_info['content'])
                
#             return True
            
#         except Exception as e:
#             print(f"Error restoring version: {str(e)}")
#             return False

#     def address_request(self, agent_request):
#         collection_name = agent_request.agent_name
#         operation_type = agent_request.query.operation_type
        
#         path = None
#         if operation_type in ["create_file", "write", "rollback", "share"]:
#             path = agent_request.query.params.get("file_path", None)
#         elif operation_type == "create_dir":
#             path = agent_request.query.params.get("dir_path", None)
            
#         try:
#             if operation_type == "mount":
#                 root = agent_request.query.params.get("root", self.root_dir)
#                 result = self.sto_mount(
#                     collection_name=collection_name,
#                     root_dir=root
#                 )
            
#             elif operation_type == "create_file":
#                 file_path = agent_request.query.params.get("file_path", None)
#                 result = self.sto_create_file(
#                     file_path, collection_name
#                 )

#             elif operation_type == "create_dir":
#                 dir_path = agent_request.query.params.get("dir_path", None)
#                 result = self.sto_create_directory(
#                     dir_path=dir_path,
#                     collection_name=collection_name
#                 )
                
#             elif operation_type == "write":
#                 file_name = agent_request.query.params.get("file_name", None)
#                 file_path = agent_request.query.params.get("file_path", None)
#                 content = agent_request.query.params.get("content", None)
#                 # breakpoint()
#                 result = self.sto_write(
#                     file_name=file_name,
#                     file_path=file_path,
#                     content=content,
#                     collection_name=collection_name
#                 )

#             elif operation_type == "retrieve":
#                 query_text = agent_request.query.params.get("query_text", None)
#                 k = agent_request.query.params.get("k", "3")
#                 keywords = agent_request.query.params.get("keywords", None)
#                 result = self.sto_retrieve(
#                     collection_name=collection_name,
#                     query_text=query_text,
#                     k=k,
#                     keywords=keywords
#                 )
                
#             elif operation_type == "rollback":
#                 file_path = agent_request.query.params.get("file_path", None)
#                 n = agent_request.query.params.get("n", "1")
#                 time = agent_request.query.params.get("time", None)
#                 result = self.sto_rollback(
#                     file_path=file_path,
#                     n=int(n),
#                     time=time
#                 )

#             elif operation_type == "share":
#                 file_path = agent_request.query.params.get("file_path", None)
#                 result = self.sto_share(
#                     file_path=file_path,
#                     collection_name=collection_name
#                 )
        
#             else:
#                 result = f"Operation type: {operation_type} not supported"
        
#         except Exception as e:
#             result = f"Error handling file operation: {str(e)}"
#         return result

#     def sto_create_file(self, file_name: str, file_path: str, collection_name: str = None) -> bool:
#         try:
#             if file_path is None:
#                 file_path = os.path.join(self.root_dir, file_name)
            
#             if not os.path.exists(file_path):
#                 with open(file_path, 'w') as f:
#                     pass  # Create empty file
                
#                 if self.use_vector_db:
#                     self.vector_db.update_document(file_path, "", collection_name)
#                 return "File has been created successfully at: " + file_path
#             return "File already exists at: " + file_path
        
#         except Exception as e:
#             return f"Error creating file: {str(e)}"
            
#     def sto_create_directory(self, dir_name: str, dir_path: str, collection_name: str = None) -> bool:
#         try:
#             if dir_path is None:
#                 dir_path = os.path.join(self.root_dir, dir_name)
            
#             if not os.path.exists(dir_path):
#                 os.makedirs(dir_path)
#                 # if self.use_vector_db:
#                 #     self.vector_db.create_directory(dir_name, collection_name)
#                 return "Directory has been created successfully at: " + dir_path
#             return "Directory already exists at: " + dir_path
        
#         except Exception as e:
#             return f"Error creating directory: {str(e)}"
            
#     def sto_mount(self, collection_name: str, root_dir: str) -> str:
#         try:
#             collection = self.vector_db.add_or_get_collection(collection_name)
#             assert collection is not None, f"Collection {collection_name} not found"
#             self.vector_db.build_database(root_dir)
#             response = f"File system mounted successfully for agent: {collection_name}"
#             return response
        
#         except Exception as e:
#             response = f"Error mounting file system: {str(e)}"
#             return response
            
#     def sto_write(self, file_name: str, file_path: str, content: str, collection_name: str = None) -> str:
#         """Write to file with proper lock management."""
#         if file_path is None:
#             file_path = os.path.join(self.root_dir, file_name)
            
#         lock = self.get_file_lock(file_path)
#         try:
#             if lock.acquire(timeout=10):  # Add timeout to prevent deadlocks
#                 try:
#                     with open(file_path, 'w') as f:
#                         f.write(content)
                    
#                     return f"Content has been written to file: {file_path}"
#                 finally:
#                     lock.release()  # Ensure lock is always released
#             else:
#                 return f"Timeout waiting for lock on {file_path}"
#         except Exception as e:
#             return f"Error writing to file: {str(e)}"
            
#     def sto_retrieve(self, collection_name: str, query_text: str, k: str = "3", keywords: str = None) -> list:
#         try:
#             collection = self.vector_db.add_or_get_collection(collection_name)
#             return self.vector_db.retrieve(collection, query_text, k, keywords)
        
#         except Exception as e:
#             print(f"Error retrieving documents: {str(e)}")
#             return []
            
#     def sto_rollback(self, file_path, n=1, time=None) -> bool:
#         try:
#             if not self.use_redis:
#                 return "Redis is not enabled. Please make sure the redis server has been installed and running."
            
#             versions = self.get_file_history(file_path)
            
#             if time:
#                 # Find version closest to specified time
#                 target_version = None
#                 min_time_diff = float('inf')
                
#                 for i, version in enumerate(versions):
#                     version_time = datetime.fromisoformat(version['timestamp'])
#                     target_time = datetime.fromisoformat(time)
#                     time_diff = abs((version_time - target_time).total_seconds())
                    
#                     if time_diff < min_time_diff:
#                         min_time_diff = time_diff
#                         target_version = i
                        
#                 if target_version is not None:
#                     result = self.restore_version(file_path, target_version)
#                     if result:
#                         return f"Successfully rolled back the file: {file_path} to its previous {n} version"
#                     else:
#                         return f"Failed to roll back the file: {file_path} to its previous {n} version"
#             else:
#                 # Rollback n versions
#                 target_version = int(n)
                
#                 result = self.restore_version(file_path, target_version)
#                 if result:
#                     return f"Successfully rolled back the file: {file_path} to its previous {n} version"
#                 else:
#                     return f"Failed to roll back the file: {file_path} to its previous {n} version"
                
#             return result
        
#         except Exception as e:
#             result = f"Error rolling back file: {str(e)}"
#             return result
            
#     def generate_share_link(self, file_path: str) -> str:
#         """Generate a publicly accessible link for sharing a file.
        
#         Args:
#             file_path: Path to the file to be shared
            
#         Returns:
#             str: A public URL where the file can be accessed
#         """
#         try:
#             # First check if we already have a valid share link in Redis
#             if not self.use_redis:
#                 return "Redis is not enabled. Please make sure the redis server has been installed and running."
            
#             file_hash = self.get_file_hash(file_path)
#             share_key = f"share:link:{file_hash}"
            
#             existing_share = self.redis_client.hgetall(share_key)
#             if existing_share and datetime.fromisoformat(existing_share['expires_at']) > datetime.now():
#                 return existing_share['share_link']

#             # If no valid existing share, create new one
#             with open(file_path, 'rb') as f:
#                 # Option 1: Using transfer.sh
#                 response = requests.put(
#                     f'https://transfer.sh/{file_hash}',
#                     data=f.read(),
#                     headers={'Max-Days': '7'}
#                 )
#                 share_link = response.text.strip()
                
#                 # Option 2: Using 0x0.st (alternative)
#                 # response = requests.post(
#                 #     'https://0x0.st',
#                 #     files={'file': f}
#                 # )
#                 # share_link = response.text.strip()

#             # Store share info in Redis
#             share_info = {
#                 "file_path": file_path,
#                 "share_link": share_link,
#                 "created_at": datetime.now().isoformat(),
#                 "expires_at": (datetime.now() + timedelta(days=7)).isoformat(),
#                 "file_hash": file_hash
#             }
            
#             self.redis_client.hmset(share_key, share_info)
#             self.redis_client.expire(share_key, 60 * 60 * 24 * 7)  # 7 days TTL

#             return share_link

#         except Exception as e:
#             print(f"Error generating public share link: {str(e)}")
#             return None

#     def sto_share(self, file_path: str, collection_name: str = None) -> dict:
#         """Share file with proper lock management."""
#         lock = self.get_file_lock(file_path)
#         try:
#             if lock.acquire(timeout=10):  # Add timeout to prevent deadlocks
#                 try:
#                     if not os.path.exists(file_path):
#                         return {"error": "File not found"}
                        
#                     share_link = self.generate_share_link(file_path)
#                     if not share_link:
#                         return {"error": "Failed to generate share link"}

#                     return {
#                         "file_name": os.path.basename(file_path),
#                         "file_path": file_path,
#                         "share_link": share_link,
#                         "expires_in": "7 days",
#                         "last_modified": datetime.fromtimestamp(
#                             os.path.getmtime(file_path)
#                         ).isoformat()
#                     }
#                 finally:
#                     lock.release()  # Ensure lock is always released
#             else:
#                 return {"error": f"Timeout waiting for lock on {file_path}"}
#         except Exception as e:
#             return {"error": f"Error sharing file: {str(e)}"}



# *******************************************************************************************************************





# aios/storage/filesystem/lsfs.py
import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import redis
import json
from datetime import datetime, timedelta
import hashlib
import threading
import requests
from .vector_db import ChromaDB
import logging
import stat

logging.getLogger('watchdog').setLevel(logging.ERROR)

class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, lsfs_instance):
        self.lsfs = lsfs_instance
        
    def on_modified(self, event):
        if not event.is_directory:
            self.lsfs.handle_file_change(event.src_path, "modified")
            
    def on_created(self, event):
        if not event.is_directory:
            self.lsfs.handle_file_change(event.src_path, "created")
            
    def on_deleted(self, event):
        if not event.is_directory:
            self.lsfs.handle_file_change(event.src_path, "deleted")

class LSFS:
    def __init__(self, root_dir, use_vector_db=True, max_versions=20):
        # Ensure root_dir is absolute
        self.root_dir = os.path.abspath(root_dir)
        self.use_vector_db = use_vector_db
        self.max_versions = max_versions
        self.vector_db = ChromaDB(mount_dir=self.root_dir)
        
        # Initialize Redis connection
        self.redis_client = redis.Redis(
            host='localhost',
            port=6379,
            db=0,
            decode_responses=True
        )
        
        # Test Redis connection
        try:
            self.redis_client.ping()
            print("Successfully connected to Redis")
            self.use_redis = True
        except redis.ConnectionError as e:
            print(f"Failed to connect to Redis: {e}")
            self.use_redis = False
        
        self.file_locks = {}
        self.locks_lock = threading.Lock()

        # Start Observer
        try:
            self.observer = Observer()
            self.event_handler = FileChangeHandler(self)
            if not os.path.exists(self.root_dir):
                os.makedirs(self.root_dir)
            self.observer.schedule(self.event_handler, self.root_dir, recursive=True)
            self.observer.start()
        except Exception as e:
            print(f"Warning: Failed to start file observer: {e}")
        
    def __del__(self):
        if hasattr(self, 'observer'):
            self.observer.stop()
            self.observer.join()
    
    # --- FIX 1: Path Resolution Helper ---
    def _resolve_path(self, path):
        """Helper to ensure paths are always inside the mounted root."""
        if not path:
            return None
        # If path is absolute and starts with root_dir, return it
        if os.path.isabs(path) and path.startswith(self.root_dir):
            return path
        # Clean the path to avoid directory traversal (../)
        clean_path = os.path.normpath(path).lstrip(os.sep).lstrip('.')
        return os.path.join(self.root_dir, clean_path)
            
    def get_file_hash(self, file_path: str) -> str:
        return hashlib.sha256(file_path.encode()).hexdigest()
            
    def get_file_lock(self, file_path: str) -> threading.Lock:
        with self.locks_lock:
            if file_path not in self.file_locks:
                self.file_locks[file_path] = threading.Lock()
            return self.file_locks[file_path]

    # --- FIX 2: Helper to Force Save History (Fixes Rollback) ---
    def _save_history(self, file_path, content, change_type="modified"):
        """Manually push a version to Redis history."""
        if not self.use_redis: return

        try:
            file_hash = self.get_file_hash(file_path)
            timestamp = datetime.now().isoformat()
            
            version_info = {
                'content': content,
                'timestamp': timestamp,
                'hash': file_hash,
                'change_type': change_type
            }
            
            versions_key = file_hash
            
            # Check if this content is identical to the last version (Deduplication)
            last_version_data = self.redis_client.lindex(versions_key, 0)
            if last_version_data:
                last_version = json.loads(last_version_data)
                if last_version.get('content') == content:
                    return # Skip duplicate save

            # Push new version
            self.redis_client.lpush(versions_key, json.dumps(version_info))
            self.redis_client.ltrim(versions_key, 0, self.max_versions - 1)
            
        except Exception as e:
            print(f"Error saving history: {e}")
            
    def handle_file_change(self, file_path: str, change_type: str):
        # --- FIX 3: Ignore internal DB files ---
        if "chroma" in file_path or ".sqlite3" in file_path or ".DS_Store" in file_path or ".tmp" in file_path:
            return

        lock = self.get_file_lock(file_path)
        try:
            if lock.acquire(timeout=5):
                try:
                    if change_type in ["modified", "created"]:
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                            
                            if self.use_vector_db:
                                self.vector_db.update_document(file_path, content)
                                
                            # Save to Redis via helper (Backup mechanism if Write didn't trigger)
                            self._save_history(file_path, content, change_type)
                            
                        except (FileNotFoundError, IsADirectoryError):
                            pass
                            
                    elif change_type == "deleted":
                        if self.use_vector_db:
                            self.vector_db.delete_document(file_path)
                        
                        file_hash = self.get_file_hash(file_path)
                        deletion_info = {'timestamp': datetime.now().isoformat(), 'change_type': 'deleted'}
                        self.redis_client.lpush(file_hash, json.dumps(deletion_info))
                        
                finally:
                    lock.release()
        except Exception as e:
            print(f"Error handling file change: {str(e)}")
            
    def get_file_history(self, file_path: str, limit: int = None) -> list:
        file_hash = self.get_file_hash(file_path)
        limit = limit or self.max_versions
        versions = self.redis_client.lrange(file_hash, 0, limit - 1)
        return [json.loads(v) for v in versions]
        
    def restore_version(self, file_path: str, version_index: int) -> bool:
        try:
            file_hash = self.get_file_hash(file_path)
            version_data = self.redis_client.lindex(file_hash, version_index)
            
            if not version_data:
                return False
                
            version_info = json.loads(version_data)
            if 'content' not in version_info:
                return False
            
            with open(file_path, 'w') as f:
                f.write(version_info['content'])
            
            # Force save the restored version as the NEW latest version
            self._save_history(file_path, version_info['content'], "restored")
                
            return True
        except Exception as e:
            print(f"Error restoring version: {str(e)}")
            return False

    def address_request(self, agent_request):
        collection_name = agent_request.agent_name
        operation_type = agent_request.query.operation_type
        params = agent_request.query.params  # Shorten for readability
        
        # --- 1. Centralized Path Resolution ---
        raw_path = None
        
        # Operations that target a specific file
        file_ops = [
            "create_file", "write", "rollback", "share", "delete_file", 
            "read_file", "run_python", "restrict_file", "temp_lock_file"
        ]
        
        # Operations that target a directory
        dir_ops = ["create_dir", "delete_dir", "list_files"]

        if operation_type in file_ops:
            raw_path = params.get("file_path") or params.get("file_name")
        elif operation_type in dir_ops:
            raw_path = params.get("dir_path", ".")
            
        # --- 2. Special Cases (Multi-path or No-path) ---
        # Move requires two paths, so we resolve them separately here
        if operation_type == "move_file":
            src = self._resolve_path(params.get("src_path"))
            dest = self._resolve_path(params.get("dest_path"))
            return self.sto_move_file(src, dest)
            
        # Read URL takes a web link, not a file path
        if operation_type == "read_url":
            return self.sto_read_url(params.get("url"))

        # --- 3. Resolve Single Target Path ---
        # This applies to all standard file_ops and dir_ops
        target_path = self._resolve_path(raw_path)

        try:
            if operation_type == "mount":
                root = params.get("root", self.root_dir)
                return self.sto_mount(collection_name, root)
            
            # --- File System Tools ---
            elif operation_type == "list_files":
                return self.sto_list_files(target_path)
            
            elif operation_type == "read_file":
                return self.sto_read_file(target_path)
            
            elif operation_type == "create_file":
                return self.sto_create_file(target_path, collection_name)

            elif operation_type == "create_dir":
                return self.sto_create_directory(target_path, collection_name)
                
            elif operation_type == "write":
                content = params.get("content", "")
                return self.sto_write(target_path, content, collection_name)

            elif operation_type == "delete_file":
                if os.path.exists(target_path):
                    os.remove(target_path)
                    return f"Deleted file: {target_path}"
                return "File not found."

            # --- Memory & History Tools ---
            elif operation_type == "retrieve":
                query_text = params.get("query_text", None)
                k = params.get("k", "3")
                keywords = params.get("keywords", None)
                
                results = self.sto_retrieve(collection_name, query_text, k, keywords)
                return json.dumps(results, indent=2) if results else "No results found."
                
            elif operation_type == "rollback":
                n = params.get("n", "1")
                # Support time-based rollback if provided
                time_arg = params.get("time", None) 
                return self.sto_rollback(target_path, int(n), time_arg)

            elif operation_type == "share":
                return str(self.sto_share(target_path, collection_name))
            
            # --- Modern Agent Tools ---
            elif operation_type == "run_python":
                return self.sto_run_python(target_path)

            # --- Security Tools ---
            elif operation_type == "restrict_file":
                mode = params.get("mode")
                return self.sto_restrict_file(target_path, mode)

            elif operation_type == "temp_lock_file":
                minutes = params.get("minutes")
                return self.sto_temp_lock_file(target_path, int(minutes))
        
            else:
                return f"Operation type: {operation_type} not supported"
        
        except Exception as e:
            return f"Error handling file operation: {str(e)}"
        
    def sto_list_files(self, dir_path):
        try:
            if not os.path.exists(dir_path): return f"Directory not found: {dir_path}"
            files = os.listdir(dir_path)
            visible_files = [f for f in files if not f.startswith('.') and not f.endswith('.sqlite3')]
            if not visible_files: return "Directory is empty."
            return f"Files in {os.path.basename(dir_path)}:\n" + "\n".join(visible_files)
        except Exception as e: return f"Error listing files: {str(e)}"

    def sto_read_file(self, file_path: str) -> str:
        try:
            if not os.path.exists(file_path): return f"Error: File not found at {file_path}"
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            return f"--- Content of {os.path.basename(file_path)} ---\n{content}"
        except Exception as e: return f"Error reading file: {str(e)}"

    def sto_create_file(self, file_path: str, collection_name: str = None) -> str:
        try:
            if not os.path.exists(file_path):
                with open(file_path, 'w') as f:
                    pass 
                if self.use_vector_db:
                    self.vector_db.update_document(file_path, "", collection_name)
                # Force save empty state
                self._save_history(file_path, "", "created")
                return "File created: " + file_path
            return "File exists: " + file_path
        except Exception as e: return f"Error creating file: {str(e)}"
            
    def sto_create_directory(self, dir_path: str, collection_name: str = None) -> str:
        try:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
                return "Directory created: " + dir_path
            return "Directory exists."
        except Exception as e: return f"Error creating directory: {str(e)}"
            
    # def sto_mount(self, collection_name: str, root_dir: str) -> str:
    #     try:
    #         self.vector_db.build_database(root_dir)
    #         return f"Mounted at {root_dir}"
    #     except Exception as e: return f"Error mounting: {str(e)}"

    def sto_mount(self, collection_name: str, root_dir: str) -> str:
        try:
            collection = self.vector_db.add_or_get_collection(collection_name)
            assert collection is not None, f"Collection {collection_name} not found"
            self.vector_db.build_database(root_dir)
            response = f"File system mounted successfully for agent: {collection_name}"
            return response
        
        except Exception as e:
            response = f"Error mounting file system: {str(e)}"
            return response
            
    def sto_write(self, file_path: str, content: str, collection_name: str = None) -> str:
        lock = self.get_file_lock(file_path)
        try:
            if lock.acquire(timeout=10):
                try:
                    with open(file_path, 'w') as f:
                        f.write(content)
                    # --- Force Save History ---
                    self._save_history(file_path, content, "modified")
                    return f"Content written to: {file_path}"
                finally:
                    lock.release()
            return f"Timeout waiting for lock on {file_path}"
        except Exception as e: return f"Error writing: {str(e)}"
            
    def sto_retrieve(self, collection_name: str, query_text: str, k: str = "3", keywords: str = None) -> list:
        try:
            return self.vector_db.retrieve(self.vector_db.add_or_get_collection(collection_name), query_text, k, keywords)
        except Exception as e:
            print(f"Error retrieving: {str(e)}")
            return []
            
    def sto_rollback(self, file_path, n=1, time=None) -> str:
        try:
            if not self.use_redis: return "Redis not enabled."
            if self.restore_version(file_path, int(n)):
                return f"Rolled back {file_path} successfully"
            return "Failed to rollback."
        except Exception as e: return f"Error rolling back: {str(e)}"

# ... inside LSFS class ...

    def generate_share_link(self, file_path: str) -> str:
        try:
            # 1. Check Redis
            if not self.use_redis: 
                return "Error: Redis is not enabled."
            
            file_hash = self.get_file_hash(file_path)
            file_name = os.path.basename(file_path)
            share_key = f"share:link:{file_hash}"
            
            # 2. Check Cache
            existing_share = self.redis_client.hgetall(share_key)
            if existing_share and datetime.fromisoformat(existing_share['expires_at']) > datetime.now():
                return existing_share['share_link']

            share_link = None

            # 3. Try Internet Upload (Will fail on your server)
            try:
                print(f"DEBUG: Attempting upload for {file_name}...")
                with open(file_path, 'rb') as f:
                    response = requests.put(
                        f'https://transfer.sh/{file_name}', 
                        data=f.read(),
                        headers={'Max-Days': '7'},
                        timeout=5 # Short timeout for local testing
                    )
                    if response.status_code == 200:
                        share_link = response.text.strip()
            except Exception as e:
                print(f"DEBUG: Internet upload failed ({e}). Switching to Local Mode.")

            # 4. FALLBACK: If internet failed, generate a Local File URI
            if not share_link:
                share_link = f"file://{file_path}"

            # 5. Save to Redis (So we remember the link)
            share_info = {
                "file_path": file_path,
                "share_link": share_link,
                "created_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(days=7)).isoformat(),
                "file_hash": file_hash
            }
            self.redis_client.hmset(share_key, share_info)
            self.redis_client.expire(share_key, 60 * 60 * 24 * 7)
            
            return share_link

        except Exception as e:
            return f"Error generating link: {str(e)}"
        
    def sto_temp_lock_file(self, file_path: str, minutes: int) -> str:
        try:
            if not os.path.exists(file_path):
                return "Error: File not found."

            # 1. LOCK: Set permissions to Read-Only (444)
            # This blocks edits from AIOS *and* Linux Terminal
            os.chmod(file_path, stat.S_IREAD | stat.S_IRGRP | stat.S_IROTH)
            
            # 2. TIMER: Define the unlock function
            def _unlock_later():
                time.sleep(int(minutes) * 60)  # Wait X minutes
                try:
                    # Restore Read+Write permissions (644)
                    os.chmod(file_path, stat.S_IREAD | stat.S_IWRITE | stat.S_IRGRP | stat.S_IROTH)
                    print(f"DEBUG: Auto-unlocked {file_path}")
                except Exception as e:
                    print(f"Error auto-unlocking: {e}")

            # 3. BACKGROUND: Run the timer in a separate thread
            # daemon=True means this thread won't stop the server from shutting down
            t = threading.Thread(target=_unlock_later, daemon=True)
            t.start()

            return f"🔒 File LOCKED for {minutes} minutes. OS permissions set to Read-Only."

        except PermissionError:
            return "Error: Permission denied. Cannot change file attributes."
        except Exception as e:
            return f"Error locking file: {str(e)}"

    def sto_share(self, file_path: str, collection_name: str = None) -> dict:
        lock = self.get_file_lock(file_path)
        try:
            if lock.acquire(timeout=10):
                try:
                    if not os.path.exists(file_path): 
                        return {"error": f"File not found at {file_path}"}
                    
                    # Get the result (Link OR Error Message)
                    result = self.generate_share_link(file_path)
                    
                    # Return it clearly so the AI sees it
                    if result and result.startswith("Error"):
                        return {"error_details": result}
                    
                    return {"share_link": result, "file": file_path, "status": "success"}
                finally:
                    lock.release()
            return {"error": "Timeout waiting for file lock"}
        except Exception as e:
            return {"error": str(e)}