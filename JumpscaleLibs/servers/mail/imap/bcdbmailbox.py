import mailbox
import io
import time
from gevent.lock import Semaphore
from collections import defaultdict
from ..handleMail import store_message, object_to_message

locks = defaultdict(Semaphore)


class BCDBMailbox(mailbox.Mailbox):
    def __init__(self, models, obj, create=False):
        self._models = models
        self._obj = obj

    def _get_folder_object(self, name):
        if name.lower() == "inbox":
            name = "inbox"
        folders = self._models.folder.find(name=name)
        if folders:
            return folders[0]
        return None

    def iterkeys(self):
        for key in sorted(self._models.message.find_ids(folder=self._obj.name)):
            yield key

    def get_sequences(self):
        return self._obj.sequences

    def remove(self, key):
        self._models.message.delete(key)

    def set_sequences(self, seq):
        self._obj.mtime = int(time.time())
        self._obj.sequences = seq
        self._obj.save()

    def add(self, message):
        msg = store_message(self._models.message, message, self._obj.name, False, False)
        return msg.id

    def get_file(self, key):
        message = self.get_message(key)
        file = io.BytesIO()
        file.write(str(message).encode())
        file.seek(0)
        return file

    def subscribe(self):
        self._obj.subscribed = True
        self._obj.save()

    def unsubscribe(self):
        self._obj.subscribed = False
        self._obj.save()

    def __len__(self):
        return self._models.message.count(folder=self._obj.name)

    def pack(self):
        pass  # we don't need this in our implementation

    def close(self):
        pass

    def get_message(self, key):
        obj = self.get_object(key)
        message = object_to_message(obj)
        return message

    def get_message_mtime(self, key):
        query = "select mtime from {} where id = ?;".format(self._models.message.index.sql_table_name)
        cursor = self._models.message.query(query, [key])
        mtime = cursor.fetchone()[0]
        return mtime

    def get_object(self, key):
        return self._models.message.get(key)

    def get_uid(self, key):
        return self._obj.id, key

    def get_uid_vv(self):
        return self._obj.id

    def set_uid(self, key, uid_vv, uid):
        return self._obj.id, key

    @property
    def mtime(self):
        return self._obj.mtime

    def list_folders(self):
        folders = []
        for folder in self._models.folder.find():
            folders.append(folder.name)
        return folders

    def list_subfolders(self, folder_name, values=None):
        query = "select * from {} WHERE name LIKE {} and name NOT LIKE {}".format(
            self._models.folder.index.sql_table_name, "'%" + folder_name + "%'", "'" + folder_name + "'"
        )
        return self._models.folder.query(query, values)

    def query_folder(self, fields, extra="", values=None):
        query = "select {} from {} ".format(",".join(fields), self._models.folder.index.sql_table_name)
        query += extra
        return self._models.folder.query(query, values)

    def lock(self):
        locks[self._obj.name].acquire()

    def unlock(self):
        locks[self._obj.name].release()

    def get_messages(self, query):
        if query:
            return self._models.message.query(
                "SELECT * FROM {} {}".format(self._models.message.index.sql_table_name, query)
            )
        return self._models.message.find()

    def rename_folder(self, old_name, new_name):
        folder = self._models.folder.find(name=old_name)
        messages = self._models.message.find(folder=old_name)
        folder[0].name = new_name
        folder[0].save()
        for message in messages:
            message.folder = new_name
            message.save()

    def remove_folder(self, folder_name):
        messages = self._models.message.find(folder=folder_name)
        folder = self._models.folder.find(name=folder_name)
        folder[0].delete()
        for message in messages:
            message.delete()


class BCDBMailboxdir(BCDBMailbox):
    def __init__(self, models):
        self._models = models

    def get_folder(self, name):
        folder = self._get_folder_object(name)
        if folder:
            return BCDBMailbox(self._models, folder)
        raise mailbox.NoSuchMailboxError(name)

    def create(self, name):
        folder = self._models.folder.new()
        folder.name = name
        folder.save()
        return BCDBMailbox(self._models, folder)
