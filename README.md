# **Mini Git Implementation - Python**

Welcome to the **Mini Git Implementation** repository! This project is a simplified version of Git, built using **Python**, that mimics core Git functionalities such as creating blobs, trees, commits, and retrieving repository states.

---

## **🚀 Project Overview**

This project aims to provide a basic understanding of Git internals by implementing key features such as:

- Storing files as blobs.
- Writing directory structures as tree objects.
- Committing changes with parent tracking.
- Retrieving and reconstructing repository states from commits.

It provides CLI-based commands similar to Git for interacting with the repository.

---

## **🛠 Tech Stack**

The project is built using the following technologies:

- **Python** (Core functionality)
- **Zlib** (Compression of Git objects)
- **Hashlib** (SHA-1 hashing for object identification)
- **Bash** (Testing automation via script)

---

## **✨ Features**

1. **Git-like Initialization**  
   - Initialize a new repository similar to `git init`.
   - Creates `.git` directory to store objects and references.

2. **Blobs (File Storage)**  
   - Store files as compressed blobs using SHA-1 hashes.
   - Retrieve stored content via `cat-file` command.

3. **Tree Objects (Directory Structure)**  
   - Store the entire directory structure as tree objects.
   - Reference blobs to reconstruct file structures.

4. **Commit Creation**  
   - Commit changes by linking tree objects with author information.
   - Support for parent commits to track history.

5. **Repository State Retrieval**  
   - Reconstruct repository structure from any commit.
   - View file and directory contents for a specific commit.

---


