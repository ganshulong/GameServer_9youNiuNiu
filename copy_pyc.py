# coding: utf-8

import os
import compileall
import shutil
import filecmp

root = os.getcwd()

print root


def copy_pyc():
    compileall.compile_dir(root, ddir=".", force=1, quiet=1)
    svn_root = "D:\publish\server"
    basename = os.path.basename(root)
    svn_path = os.path.join(svn_root, basename)

    for r, d, f_list in os.walk(root):
        pyc_list = []
        for f in f_list:
            if f.endswith(".pyc") or f.endswith(".conf") or f.endswith(".sh") or f.startswith("settings"):
                pyc_list.append(f)

        if not pyc_list:
            continue
        sub_dir = os.path.join(svn_path, r.split(basename)[-1].strip('\\'))

        if not os.path.exists(sub_dir):
            os.mkdir(sub_dir)

        for pyc in pyc_list:
            src = os.path.join(r, pyc)
            dest = os.path.join(sub_dir, pyc)
            if not os.path.exists(dest) or not filecmp.cmp(src, dest):
                print pyc
                shutil.copyfile(src, dest)

if __name__ == '__main__':
    copy_pyc()
