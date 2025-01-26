import sys
import os
import zlib
from pathlib import Path
import hashlib
import time


def cat_file(file_hash):
    """
    Reads and decompresses a Git object from the .git/objects directory and prints its contents.

    :param file_hash: The SHA-1 hash of the object to retrieve.
    :raises RuntimeError: If the file hash is not provided or if the file does not exist.
    """
    if not file_hash:
        raise RuntimeError("File Hash not passed in command")

    file_dir = file_hash[:2]  # Extract the first two characters for the directory
    hash_name = file_hash[2:]  # Remaining characters for the file name
    path_to_hash = f".git/objects/{file_dir}/{hash_name}"
    file = Path(path_to_hash)

    if file.exists():
        with open(path_to_hash, 'rb') as f:
            raw = f.read()
            data = zlib.decompress(raw)  # Decompress Git object
            content = data.split(b'\0')[1].decode('ascii').rstrip('\n')
            print(content, end="")
    else:
        raise RuntimeError("File Not found")
    
def store_blob(sha, raw):
    """
    Stores a raw Git object in the .git/objects directory.

    :param sha: The SHA-1 hash of the object to store.
    :param raw: The raw content to be compressed and stored.
    """
    git_path = os.path.join(os.getcwd(), ".git", "objects")
    sub_folder = sha[:2]
    file_name = sha[2:]
    
    path = os.path.join(git_path, sub_folder)
    os.makedirs(path, exist_ok=True)
    
    with open(os.path.join(path, file_name), "wb") as f:
        compressed = zlib.compress(raw)
        f.write(compressed)
    
    
def hash_object(file_name, do_print=False):
    """
    Hashes a file and stores it as a Git blob object.

    :param file_name: Path to the file to be hashed.
    :param do_print: Whether to print the resulting hash or not.
    :return: The SHA-1 hash of the stored blob.
    :raises RuntimeError: If the file does not exist.
    """
    file = Path(file_name)
    if file.exists():
        with open(file_name, 'rb') as f:
            raw = f.read()
            header = f"blob {len(raw)}\x00"
            storage = header.encode("ascii") + raw
            sha = hashlib.sha1(storage).hexdigest()
            store_blob(sha, storage)
            if do_print:
                print(sha, end="")
            return sha
    else:
        raise RuntimeError("File Not found")


def ls_tree(param, tree_hash):
    """
    Lists the contents of a Git tree object.

    :param param: Optional parameter to control output format.
    :param tree_hash: The SHA-1 hash of the tree object to list.
    :raises RuntimeError: If the tree object is not found or is invalid.
    """
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
        # BUG FIX: Use sha.hex() instead of re-hashing the 20 bytes
        sha_hex = sha.hex()  
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
    

def traverse_directory(directory="."):

    """
    Recursively traverses a directory and creates entries for Git storage.

    :param directory: Path of the directory to traverse.
    :return: List of tuples containing mode, name, and SHA-1 of each entry.
    """    
    directory = os.path.abspath(directory)
    entries = []
    contents = sorted(
        os.listdir(directory),
        key=lambda x: x if os.path.isfile(os.path.join(directory, x)) else f"{x}/",
    )

    for item in contents:
        if item == ".git":
            continue
        path = os.path.join(directory, item)
        if os.path.isdir(path):
            sha = write_tree(path)
            mode = "40000"
        else:
            # BUG FIX: Avoid printing the hash here to keep output clean
            sha = hash_object(path, do_print=False)
            mode = "100644"
        sha1 = int.to_bytes(int(sha, 16), length=20, byteorder="big")
        entries.append((mode, item, sha1))
    return entries


def write_tree(directory="."):
    """
    Writes the current directory tree as a Git tree object.

    :param directory: The directory to be written to a tree object.
    :return: The SHA-1 hash of the stored tree.
    """
    entries = traverse_directory(directory)
    tree_content = b""
    for mode, name, sha in entries:
        tree_content += f"{mode} {name}\x00".encode('utf-8') + sha
    
    header = f"tree {len(tree_content)}\x00".encode('utf-8') + tree_content
    sha = hashlib.sha1(header).hexdigest()
    store_blob(sha, header)  # Store the tree object
    return sha   
    

def commit_tree(tree_sha, parent_sha, message):
    """
    Creates a Git commit object and stores it in the .git/objects directory.

    :param tree_sha: The SHA-1 of the tree object.
    :param parent_sha: The SHA-1 of the parent commit (optional).
    :param message: The commit message.
    :return: The SHA-1 hash of the commit object.
    """
    author_name = "Coder <coder@example.com>"
    timestamp = int(time.time())
    timezone = time.strftime("%z")

    # Ensure correct commit format
    commit_content = f"\ntree {tree_sha}\n"
    if parent_sha:
        commit_content += f"parent {parent_sha}\n"
    commit_content += f"author {author_name} {timestamp} {timezone}\n"
    commit_content += f"committer {author_name} {timestamp} {timezone}\n\n"
    commit_content += f"{message}\n"

    commit_raw = (
        f"commit {len(commit_content.encode('utf-8'))}".encode("utf-8")
        + b'\0'
        + commit_content.encode("utf-8")
    )

    # Debug print
    print("Commit Content to be Stored:")
    print(commit_raw.decode("utf-8"))

    commit_sha = hashlib.sha1(commit_raw).hexdigest()
    store_blob(commit_sha, commit_raw)
    return commit_sha


def get_commit_state(commit_sha):
    """
    Retrieves and reconstructs the state of the repository at a specific commit.

    :param commit_sha: The SHA-1 hash of the commit to retrieve.
    :return: A dictionary representing the repository state (files and directories).

    Steps performed:
    1. Locate and read the commit object from the .git/objects directory.
    2. Extract the tree SHA from the commit object.
    3. Recursively read the tree object and reconstruct the repository file structure.
    4. Read and return file contents stored in blob objects.
    5. Print the reconstructed repository state.

    :raises RuntimeError: If the commit object, tree object, or blob object is not found.
    """
    # Step 1: Locate and read the commit object
    commit_dir = commit_sha[:2]
    commit_file = commit_sha[2:]
    commit_path = f".git/objects/{commit_dir}/{commit_file}"
    
    if not os.path.exists(commit_path):
        raise RuntimeError(f"Commit {commit_sha} not found in .git/objects")

    with open(commit_path, "rb") as f:
        commit_raw = zlib.decompress(f.read())

    # Step 2: Extract the tree SHA from the commit object
    commit_lines = commit_raw.decode("utf-8").splitlines()
    print(commit_raw.decode("utf-8"))
    tree_sha = None
    for line in commit_lines:
        if line.startswith("tree"):
            tree_sha = line.split()[1]
            break

    if not tree_sha:
        raise RuntimeError("No tree SHA found in commit object")

    # Step 3: Recursively read the tree and reconstruct the file structure
    def read_tree(tree_sha, current_path=""):
        """
        Recursively reads a tree object and reconstructs the directory structure.

        :param tree_sha: The SHA-1 hash of the tree object to read.
        :param current_path: The current directory path (used for recursion).
        :return: A dictionary representing the tree structure (files and directories).

        :raises RuntimeError: If the tree object is not found.
        """
        tree_dir = tree_sha[:2]
        tree_file = tree_sha[2:]
        tree_path = f".git/objects/{tree_dir}/{tree_file}"

        if not os.path.exists(tree_path):
            raise RuntimeError(f"Tree object {tree_sha} not found")

        with open(tree_path, "rb") as f:
            tree_raw = zlib.decompress(f.read())

        _, tree_data = tree_raw.split(b'\x00', 1)
        repo_state = {}

        while tree_data:
            mode, tree_data = tree_data.split(b" ", 1)
            name, tree_data = tree_data.split(b"\x00", 1)
            sha = tree_data[:20]
            tree_data = tree_data[20:]

            mode = mode.decode("utf-8")
            name = name.decode("utf-8")
            # BUG FIX: Convert directly to hex, do NOT re-hash
            sha_hex = sha.hex()
            
            full_path = os.path.join(current_path, name)

            if mode == "40000":  # It's a directory (tree object)
                repo_state[full_path] = read_tree(sha_hex, full_path)
            else:  # It's a file (blob object)
                repo_state[full_path] = read_blob(sha_hex)

        return repo_state

    # Step 4: Read the contents of blob objects
    def read_blob(blob_sha):        
        """
        Reads a blob object and retrieves the file contents.

        :param blob_sha: The SHA-1 hash of the blob object to read.
        :return: The contents of the file as a string.

        :raises RuntimeError: If the blob object is not found.
        """
        blob_dir = blob_sha[:2]
        blob_file = blob_sha[2:]
        blob_path = f".git/objects/{blob_dir}/{blob_file}"

        if not os.path.exists(blob_path):
            raise RuntimeError(f"Blob object {blob_sha} not found")

        with open(blob_path, "rb") as f:
            blob_raw = zlib.decompress(f.read())

        # Extract content after header
        content = blob_raw.split(b"\x00", 1)[1].decode("utf-8")
        return content

    # Step 5: Get the full repository state from the commit tree
    repo_state = read_tree(tree_sha)

    # Step 6: Print the repository state
    for path, content in repo_state.items():
        if isinstance(content, dict):
            print(f"Directory: {path}/")
        else:
            print(f"File: {path}")
            print(content)

    return repo_state


def main():
    print("Logs from your program will appear here!", file=sys.stderr)

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
        # Here we do want to print the resulting hash
        hash_object(file_name, do_print=True)
        
    elif command == "ls-tree":
        if len(sys.argv) == 4:  # `ls-tree --name-only tree_sha`
            param, tree_hash = sys.argv[2], sys.argv[3]
        elif len(sys.argv) == 3:  # `ls-tree tree_sha`
            param, tree_hash = None, sys.argv[2]
        else:
            raise RuntimeError("Invalid arguments for ls-tree command.")
        
        ls_tree(param, tree_hash)
    
    elif command == "write-tree":
        tree_sha = write_tree()
        print("Tree SHA")
        print(tree_sha)
        
    elif command == "commit-tree":
        if "-p" in sys.argv:
            if len(sys.argv) < 6 or sys.argv[3] != "-p" or sys.argv[5] != "-m":
                raise RuntimeError("Invalid arguments for commit-tree command.")
            tree_sha = sys.argv[2]
            parent_sha = sys.argv[4]
            message = sys.argv[6]
        else:
            if len(sys.argv) < 4 or sys.argv[3] != "-m":
                raise RuntimeError("Invalid arguments for commit-tree command.")
            tree_sha = sys.argv[2]
            parent_sha = None
            message = sys.argv[4]

        commit_sha = commit_tree(tree_sha, parent_sha, message)
        print(commit_sha)

    elif command == "show":
        commit_sha = sys.argv[2]
        get_commit_state(commit_sha)
    else:
        raise RuntimeError(f"Unknown command #{command}")


if __name__ == "__main__":
    main()
