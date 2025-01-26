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
    os.makedirs(path, exist_ok=True)
    
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
            store_blob(sha,storage)
            print(sha,end="")
            return sha
    else:
        raise RuntimeError("File Not found")


def ls_tree(param, tree_hash):
    # Locate the tree object file
    tree_dir = tree_hash[:2]
    tree_name = tree_hash[2:]
    path_to_tree = f".git/objects/{tree_dir}/{tree_name}"
    
    if not os.path.exists(path_to_tree):
        raise RuntimeError(f"Tree object {tree_hash} not found.")
    
    # Decompress the tree object
    with open(path_to_tree, "rb") as f:
        raw = zlib.decompress(f.read())
    
    # Split header and entries
    if not raw.startswith(b"tree"):
        raise RuntimeError("Provided hash is not a tree object.")
    
    _, binary_data = raw.split(b"\x00", maxsplit=1)
    entries = []

    # Parse entries in the tree object
    while binary_data:
        mode, binary_data = binary_data.split(b" ", maxsplit=1)
        name, binary_data = binary_data.split(b"\x00", maxsplit=1)
        sha = binary_data[:20]
        binary_data = binary_data[20:]

        # Convert to readable format
        mode = mode.decode("ascii")
        name = name.decode("utf-8")
        sha_hex = hashlib.sha1(sha).hexdigest()
        obj_type = "tree" if mode == "40000" else "blob"
        entries.append((mode, obj_type, sha_hex, name))
    
    # Sort entries alphabetically by name
    entries.sort(key=lambda x: x[3])

    # Print results based on the parameter
    if param == "--name-only":
        for _, _, _, name in entries:
            print(name)
    else:
        for mode, obj_type, sha_hex, name in entries:
            # Format matches `git ls-tree` output
            print(f"{mode} {obj_type} {sha_hex}\t{name}")
    

def traverse_directory(directory = "."):
    directory = os.path.abspath(directory)
    entries = []
    contents = sorted(
    os.listdir(directory),
    key=lambda x: x if os.path.isfile(os.path.join(directory, x)) else f"{x}/",
)
    for item in contents:
        if item == ".git":
            continue
        path = os.path.join(directory,item)
        if os.path.isdir(path):
            sha = write_tree(path)
            mode = "40000"
        else:
            sha = hash_object(path)
            mode = "100644"
        sha1 = int.to_bytes(int(sha, 16), length=20, byteorder="big")
        entries.append((mode,item,sha1))
    return entries


def write_tree(directory = "."):
    entries = traverse_directory(directory)
    tree_content = b""
    for mode ,name, sha in entries:
        tree_content += f"{mode} {name}\x00".encode('utf-8') + sha
    
    header = f"tree {len(tree_content)}\x00".encode('utf-8') + tree_content
    sha = hashlib.sha1(header).hexdigest()
    store_blob(sha, header)  # Store the tree object
    return sha   
    



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
        
    elif command == "ls-tree":
        # Handle optional `--name-only` parameter
        if len(sys.argv) == 4:  # Includes `ls-tree`, `--name-only`, and `tree_sha`
            param, tree_hash = sys.argv[2], sys.argv[3]
        elif len(sys.argv) == 3:  # Only includes `ls-tree` and `tree_sha`
            param, tree_hash = None, sys.argv[2]
        else:
            raise RuntimeError("Invalid arguments for ls-tree command.")
        
        ls_tree(param, tree_hash)
    elif command == "write-tree":
        tree_sha = write_tree()
        print("Tree SHA")
        print(tree_sha)
    else:
        raise RuntimeError(f"Unknown command #{command}")


if __name__ == "__main__":
    main()
