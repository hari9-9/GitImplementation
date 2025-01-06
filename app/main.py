import sys
import os
import zlib
from pathlib import Path
import hashlib


def cat_file(file_hash):
    if not file_hash:
            raise RuntimeError("File Hash not passed in command")
        
    file_dir = file_hash[:2]
    hash_name = file_hash[2:]
    path_to_hash = '.git/objects/'+file_dir+'/'+hash_name
    file = Path(path_to_hash)
    if file.exists():
        with open(path_to_hash,'rb') as f:
            raw = f.read()
            data = zlib.decompress(raw)
            content = data.split(b'\0')[1].decode('ascii').rstrip('\n')
            print(content, end="")
    else:
        raise RuntimeError("File Not found")
    
def store_blob(sha,raw):
    git_path = os.path.join(os.getcwd(),".git/objects")
    sub_folder = sha[:2]
    file_name = sha[2:]
    
    path = os.path.join(git_path,sub_folder)
    os.mkdir(path)
    
    with open(os.path.join(path,file_name),"wb") as f:
        compressed = zlib.compress(raw)
        f.write(compressed)
    
    
def hash_object(file_name):
    file = Path(file_name)
    if file.exists():
        with open(file_name,'rb') as f:
            raw = f.read()
            header = f"blob {len(raw)}\x00"
            storage = header.encode("ascii")+raw
            sha = hashlib.sha1(storage).hexdigest()
            store_blob(sha,raw)
            print(sha,end="")
    else:
        raise RuntimeError("File Not found")
        

def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!", file=sys.stderr)

    # Uncomment this block to pass the first stage
    #
    command = sys.argv[1]
    if command == "init":
        os.mkdir(".git")
        os.mkdir(".git/objects")
        os.mkdir(".git/refs")
        with open(".git/HEAD", "w") as f:
            f.write("ref: refs/heads/main\n")
        print("Initialized git directory")
        
    elif command == "cat-file" and sys.argv[2] == "-p":
        file_hash = sys.argv[3]
        cat_file(file_hash=file_hash)
    
    elif command == "hash-object" and sys.argv[2] == "-w":
        file_name = sys.argv[3]
        hash_object(file_name)
     
    else:
        raise RuntimeError(f"Unknown command #{command}")


if __name__ == "__main__":
    main()
