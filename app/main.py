import sys
import os
import zlib
from pathlib import Path

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
        
        
    else:
        raise RuntimeError(f"Unknown command #{command}")


if __name__ == "__main__":
    main()
