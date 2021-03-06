#!/usr/bin/env python3
import argparse
import os
import time
import hashlib
import pathlib
from pygittree import PyGitTree

################# UTILS FUNCTION #################
ROOT_DIR = pathlib.Path(__file__).parent.absolute()

def gen_path(fnames):
    return os.path.join(ROOT_DIR, fnames)

def init(args):
    os.makedirs(".pygit/objects", exist_ok=True)
    os.makedirs(".pygit/refs/heads", exist_ok=True)
    files = ["HEAD", 'index']
    for fname in files:
        with open(os.path.join(ROOT_DIR, f".pygit/{fname}"),  'w') as f:
            if fname == "HEAD":
                f.write("ref: refs/heads/master")
            pass

def in_index(content, fname, blob):
    return f"{fname} {blob}" in content

def gen_blob_dir(blob):
    return blob[:2], blob[2:]

def gen_hash(key):
    return hashlib.sha1(key.encode(encoding="utf-8"))

def regen_hash(blob):
    dirname, fname = gen_blob_dir(blob)
    blobpath = gen_path(f".pygit/objects/{dirname}/{fname}")
    if os.path.isfile(blobpath):
        t = time.time()
        return gen_hash(f"{blob} {t}").hexdigest()
    else:
        return blob

def gen_blob(content, blob):
    dirname, filename = gen_blob_dir(blob)
    dirpath = gen_path(f".pygit/objects/{dirname}")
    filepath = gen_path(f".pygit/objects/{dirname}/{filename}")
    os.makedirs(dirpath, exist_ok=True)
    with open(filepath, "w") as f:
        f.write(content)

def gen_index(fname, content):
    indexpath = gen_path(f".pygit/index")
    with open(indexpath, "r+") as f:
        lines = f.readlines()
        newlines = []
        for line in lines:
            if line != "\n" and fname not in line:
                newlines.append(line)
        newlines.append(f"{fname} {content}\n")
        f.seek(0)
        f.write("".join(newlines))
        f.truncate()

def find_ref_path():
    headpath = gen_path(".pygit/HEAD")
    with open(headpath, "r") as f:
        line = f.readline().replace("ref: ", "")
        return line

def pprint(root):
    print("------")
    print(root.name, root.value)
    print("Children")
    print("".join([f"{child.name} {child.value}" for child in root.children]))
    print("-----")
    for child in root.children:
        pprint(child)
###################################################

def add_helper(fnames):
    fpath = gen_path(fnames)
    if os.path.isfile(fpath):
        with open(fpath, "r") as f:
            lines = "".join(f.readlines())
            blob = gen_hash(lines).hexdigest()
            gen_blob(lines, blob)
            gen_index(fnames, blob)
    elif os.path.isdir(fpath):
        for f in os.listdir(fpath):
            add_helper(os.path.join(fnames, f))

def gen_tree_blob(blob):
    dirname, filename = gen_blob_dir(blob)
    dirpath = gen_path(f".pygit/objects/{dirname}")
    filepath = gen_path(f".pygit/objects/{dirname}/{filename}")
    os.makedirs(dirpath, exist_ok=True)
    with open(filepath, "w") as f:
        pass

def gen_tree_from_path(root, path, value):
    paths = path.split("/")
    for idx in range(len(paths) - 1, 0, -1):
        child = PyGitTree(paths[idx], value.replace("\n", ""))
        parent = PyGitTree(paths[idx - 1])
        parent = root.find(parent) or parent
        if parent.value == "":
            treename = paths[idx - 1]
            blob = gen_hash(f"tree {treename}").hexdigest()
            blob = regen_hash(blob)
            parent.value = blob
            gen_tree_blob(blob)
        parent.add_child(child)
    return parent

def gen_commit_blob(message, root_blob):
    blob = gen_hash(f"{message} {root_blob}").hexdigest()
    dirname, filename = gen_blob_dir(blob)
    gen_tree_blob(blob)
    filepath = gen_path(f".pygit/objects/{dirname}/{filename}")
    refpath = find_ref_path()
    parent = ""
    if refpath != "":
        branchpath = gen_path(f".pygit/{refpath}")
        if os.path.isfile(branchpath):
            with open(branchpath, "r") as f:
                line = f.readline()
                parent = f"\nparent {line}"
    with open(filepath, "w") as f:
        content = f"tree {root_blob}"
        content += parent
        content += f" \n\n{message}"
        f.write(content)
    return blob

def gen_pygittree_history(root):
    if root.children:
        for child in root.children:
            blob = root.value
            dirname, filename = gen_blob_dir(blob)
            with open(gen_path(f".pygit/objects/{dirname}/{filename}"), "a") as f:
                ftype = "tree" if child.children else "blob"
                f.write(f"{ftype} {child.value} {child.name}\n")
            gen_pygittree_history(child)

def set_branch(commit_blob):
    with open(gen_path(".pygit/HEAD"), "r") as f:
        ref = f.read().replace("ref: ", "")
        filepath = gen_path(f".pygit/{ref}")
        with open(filepath, "w") as f:
            f.write(commit_blob)

def commit_helper(message):
    root = PyGitTree()
    blob = gen_hash("tree root").hexdigest()
    blob = regen_hash(blob)
    root.value = blob
    gen_tree_blob(blob)
    with open(gen_path(".pygit/index"), "r") as f:
        lines = f.readlines()
        for line in lines:
            path, value = line.split(" ")
            child = gen_tree_from_path(root, path, value)
            root.add_child(child)

    gen_pygittree_history(root)
    commit_blob = gen_commit_blob(message, root.value)
    set_branch(commit_blob)


def commit(args):
    message = args.message
    commit_helper(message)


def add(args):
    files = args.file
    add_helper(files)

if __name__ == '__main__':
    argparse = argparse.ArgumentParser()
    subparsers = argparse.add_subparsers(help="Subcommand help")

    initparser = subparsers.add_parser("init", help="Initialize a .pygit repo")
    initparser.set_defaults(func=init)
    addparser = subparsers.add_parser("add", help="Add file to be tracked")
    addparser.add_argument('file')
    addparser.set_defaults(func=add)
    commitparser = subparsers.add_parser("commit", help="Stage changes")
    commitparser.add_argument("-m", "--message", dest="message", help="Adding a commit message")
    commitparser.set_defaults(func=commit)

    arguments = argparse.parse_args()
    arguments.func(arguments) 