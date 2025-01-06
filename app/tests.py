import unittest
import os
import shutil
import zlib
import hashlib
import subprocess
from pathlib import Path

class TestGitImplementation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.test_dir = "test_git"
        os.mkdir(cls.test_dir)
        os.chdir(cls.test_dir)

    @classmethod
    def tearDownClass(cls):
        os.chdir("..")
        shutil.rmtree(cls.test_dir)

    def setUp(self):
        if os.path.exists(".git"):
            shutil.rmtree(".git")
        self.run_command("python3 ../main.py init")

    def run_command(self, command):
        """Run a shell command and return its output."""
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Command failed: {command}\n{result.stderr}")
        return result.stdout

    def test_init(self):
        """Test initializing a new Git repository."""
        self.assertTrue(os.path.exists(".git"))
        self.assertTrue(os.path.exists(".git/objects"))
        self.assertTrue(os.path.exists(".git/refs"))
        self.assertTrue(os.path.exists(".git/HEAD"))

        with open(".git/HEAD", "r") as f:
            self.assertEqual(f.read().strip(), "ref: refs/heads/main")

    def test_hash_object(self):
        """Test hashing a file and storing it as a blob."""
        test_file = "test_file.txt"
        with open(test_file, "w") as f:
            f.write("Hello, Git!")

        self.run_command(f"python3 ../main.py hash-object -w {test_file}")

        with open(test_file, "rb") as f:
            raw = f.read()
        header = f"blob {len(raw)}\x00"
        expected_hash = hashlib.sha1((header.encode("ascii") + raw)).hexdigest()

        object_path = f".git/objects/{expected_hash[:2]}/{expected_hash[2:]}"
        self.assertTrue(os.path.exists(object_path))

        with open(object_path, "rb") as f:
            compressed = f.read()
            decompressed = zlib.decompress(compressed)
            self.assertEqual(decompressed, header.encode("ascii") + raw)

    def test_cat_file(self):
        """Test retrieving a blob's content using its hash."""
        test_file = "test_file.txt"
        content = "Hello, Git!"
        with open(test_file, "w") as f:
            f.write(content)

        self.run_command(f"python3 ../main.py hash-object -w {test_file}")

        with open(test_file, "rb") as f:
            raw = f.read()
        header = f"blob {len(raw)}\x00"
        expected_hash = hashlib.sha1((header.encode("ascii") + raw)).hexdigest()

        output = self.run_command(f"python3 ../main.py cat-file -p {expected_hash}")
        self.assertEqual(output.strip(), content)

    def test_invalid_command(self):
        """Test handling of an invalid command."""
        with self.assertRaises(RuntimeError) as context:
            self.run_command("python3 ../main.py invalid-command")
        self.assertIn("Unknown command", str(context.exception))

    def test_file_not_found(self):
        """Test handling of a file not found error."""
        with self.assertRaises(RuntimeError) as context:
            self.run_command("python3 ../main.py hash-object -w nonexistent.txt")
        self.assertIn("File Not found", str(context.exception))

if __name__ == "__main__":
    unittest.main()
