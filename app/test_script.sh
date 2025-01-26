#!/bin/bash

# Activate the virtual environment
source .venv/bin/activate

# Create a testing directory and navigate into it
TEST_DIR="testing_directory"
mkdir -p $TEST_DIR
cd $TEST_DIR

# Initialize the git repository
echo "Initializing repository..."
python ./../main.py init

# Create a test file and write initial content
echo "hello world" > test.txt

# Write the initial tree and capture the tree SHA
echo "Writing initial tree..."
TREE_SHA=$(python ./../main.py write-tree | tail -n 1)
echo "Tree SHA: $TREE_SHA"

# Create the initial commit and capture the commit SHA
echo "Creating initial commit..."
COMMIT_SHA1=$(python ./../main.py commit-tree $TREE_SHA -m "Initial commit" | tail -n 1)
echo "Initial Commit SHA: $COMMIT_SHA1"

# Show the initial commit dynamically
echo "Showing initial commit..."
python ./../main.py show $COMMIT_SHA1

# Modify the test file
echo "hello world 2" > test.txt

# Write the second tree and capture the new tree SHA
echo "Writing second tree..."
TREE_SHA2=$(python ./../main.py write-tree | tail -n 1)
echo "New Tree SHA: $TREE_SHA2"

# Create the second commit and capture the commit SHA
echo "Creating second commit..."
COMMIT_SHA2=$(python ./../main.py commit-tree $TREE_SHA2 -p $COMMIT_SHA1 -m "Initial commit 2" | tail -n 1)
echo "Second Commit SHA: $COMMIT_SHA2"

# Show the second commit dynamically
echo "Showing second commit..."
python ./../main.py show $COMMIT_SHA2

echo "Script execution completed!"
