#!/usr/bin/python3

"""
This is not the actual build script. The real "build script" is a small Java
program in the package "net.sourceforge.docfetcher.build". This script merely
compiles and launches the Java builder.
"""

import os, os.path as osp, platform, shutil, sys

is_windows = "windows" in platform.system().lower()
classpath_sep = ";" if is_windows else ":"

os.chdir(osp.dirname(osp.abspath(__file__)))
if osp.isfile("build"):
	print("Can't create build directory, a file with that name already exists.")
	exit(1)

print("Cleaning build directory...")
os.makedirs("build", exist_ok=True)
for filename in os.listdir("build"):
	path = osp.join("build", filename)
	if osp.isfile(path):
		os.remove(path)
	elif osp.isdir(path):
		shutil.rmtree(path)

print("Copying sources to build directory...")
shutil.copytree(
	"src",
	"build/tmp/src-builder",
	ignore = shutil.ignore_patterns(".cvs", ".git", ".svn")
)

# *args -> [string]
def flatten_args(*args):
	args2 = []
	for arg in args:
		if isinstance(arg, (list, tuple)):
			args2 += flatten_args(*arg)
		else:
			args2.append(str(arg))
	return args2

# ([string] | *string) -> int
def call(*args):
    import subprocess as sub
    p = sub.Popen(flatten_args(*args), stdout=sub.PIPE, stderr=sub.PIPE)
    stdout, stderr = p.communicate()
    if p.returncode != 0:
        print(f"Command failed with return code {p.returncode}")
        print("stdout:", stdout.decode())
        print("stderr:", stderr.decode())
    return p.returncode

# Recursively collect library jars
jars = []
for root, dirs, files in os.walk("lib"):
	for filename in files:
		if not filename.endswith(".jar"):
			continue
		jars.append(osp.join(root, filename))

package = "net.sourceforge.docfetcher"
package_path = package.replace(".", "/")

print("Compiling sources...")
compile_paths = [
	osp.join("build/tmp/src-builder", package_path, "build/BuildMain.java")
]
for root, dirs, files in os.walk("build/tmp/src-builder"):
	for filename in files:
		if not filename.endswith(".java"):
			continue
		if filename.startswith("Test") or filename.endswith("Test.java"):
			path = osp.join(root, filename)
			compile_paths.append(path)
call(
	"javac",
	"-source", "1.7",
	"-target", "1.7",
	"-sourcepath", "build/tmp/src-builder",
	"-classpath", classpath_sep.join(jars),
	"-nowarn",
	"-encoding", "utf8", # Needed for some Tika source files
	compile_paths
)

jar_path = "build/tmp/docfetcher-builder.jar"
main_class = package + ".build.BuildMain"

print("Creating builder jar...")
call(
	"jar", "cfe",
	jar_path,
	main_class,
	"-C", "build/tmp/src-builder", "."
)

print("Launching builder...")
print("-" * 40)
jars.append(jar_path)
call(
	"java",
	"-enableassertions", # required by test classes
	"-classpath", classpath_sep.join(jars),
	main_class
)
