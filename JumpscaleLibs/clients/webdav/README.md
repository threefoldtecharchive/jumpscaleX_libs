# A client for Webdav server 
## How to use it
- ** getting the client 
```
client = j.clients.webdav.get('local', url="<url to the webdav server>", username="<username>", password="<password>") 
```
- ** listing files in webdav server 
```
# list the root dir
client.list()
# or you can list a specific dir
client.list("dir1/dir2")
```
- ** checking dir or file existance
```
client.exists("<file or dir path>")
```
- ** create dir on server
```
client.create_dir("path")
```
- ** get file/dir info
```
client.get_info(path)
```
- ** copy file on the server to another location on the server 
```
client.copy("from", "to")
```
- ** move file on the server to another location on the server
```
client.move("from", "to")
```
- ** download a file/dir from server
```
client.download(remote_path, local_path)
```
- ** upload a file/dir to the server
```
client.upload(remote_path, local_path)
```
- ** sync dir from server to local dir
```
client.sync_to_local(remote_path, local_path)
```