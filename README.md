# Distributed-File-System NFS mode
This is my Distributed File System implementation for CS7NS1 module
ID : 17313666
Built with Python, it contains the following : 

°File Server: Responsible for the distribution of files.

°Directory Server: Responsible for mapping global files and file servers.

°Client API : Clien API with cache service on client side. 

°Lock server : Responsible for granting and revoking locks on files.

# Requirements : 

°Python 3 : Important libraries

            °web.py : http://webpy.org/ (HTML template used in fileserver : http://webpy.org/docs/0.3/tutorial#templating)
	 
            °http.server : https://docs.python.org/3/library/http.server.html
	    

# How to run : 

Run : 
fileserver.py in master 
rundirectoryserver.py in Tests
runlockserver.py in Tests
then run :
client.py in master


            
