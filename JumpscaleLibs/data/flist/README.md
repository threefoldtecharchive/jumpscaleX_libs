# Flist Manipulation 
### we using zflist binary in 0-flist repo
 
 to install it using kosmos
 ```
 j.builders.storage.zflist.install(reset=True)
 ```
 
## create new flist:
### create new flist then put file from local then commit it
```python
new_flist = j.data.flist.new() 
new_flist.put("/sandbox/code/github/test.py","/") 
new_flist.commit("/sandbox/code/app.flist") 
#delete everything in temporary-point
new_flist.close()
```

## open flist and edit on it:
### open flist , put dir from local , commit it
```python
new_flist = j.data.flist.open("/tmp/app.flist") 
new_flist.put_dir ("/tmp/app","/") 
# list all things in flist
new_flist.list_all()
new_flist.commit("/sandbox/code/app2.flist") 
#delete everything in temporary-point
new_flist.close()
```


## upload flist to hub (Guest):
before upload to hub please export  ``ZFLIST_HUB_TOKEN`` on this [example](https://github.com/threefoldtech/0-flist/tree/development-v2-customhub#example)

```python
new_flist = j.data.flist.open("/tmp/app.flist") 
new_flist.put_dir ("/tmp/app","/") 
# list all things in flist
new_flist.list_all()
new_flist.commit("/sandbox/code/app2.flist") 
new_flist.upload("/sandbox/code/app2.flist")
```

Then check it at ```https://playground.hub.grid.tf/guest```