"""This is used to build a backup of the current database and send it to GitHub in a
password-protected zip file. The script is launched via cron."""

import configparser
import subprocess
import sys
import tempfile
import time

from git import Repo
from os import chdir, getcwd, remove
from os.path import abspath, basename, dirname, expanduser, isdir, join, normpath
from shutil import copy

temp_dir = tempfile.gettempdir()
target = join(temp_dir, "vortech.sql")

# All the configs are in secret.cfg that must be created in prod server when deploying
config_dir = join(abspath(dirname(__file__)), "../settings")
configpath = abspath(join(normpath(config_dir), "secret.cfg"))

configfile = configparser.ConfigParser()
with open(configpath, "r") as cfg:
    configfile.read_file(cfg)


# 1. Generate the database dump
username = configfile.get("database", "username")
password = configfile.get("database", "password")
with open(target, "w") as out:
    subprocess.check_call(
        ["mysqldump", "-u", username, "-p{}".format(password), "vortech"],
        stdout=out
    )

# 2. Zip it up with a password, as defined in the secret.cfg
zip_password = configfile.get("env", "secret")
zip_path = join(
    temp_dir,
    "vortech-db-{}.zip".format(time.strftime('%Y-%m-%d-%H'))
)
subprocess.check_call(
    ["zip", "--password", zip_password, zip_path, target]
)

# 3. Send it to GitHub of current repository

# 3.1 First, chdir to the vortech-backups repository dir
original_dir = getcwd()
backup_dir = expanduser("/home/vortech/vortech-backups/")
if not isdir(backup_dir):
    print("Backup path does not exist - cannot continue!")
    sys.exit()
chdir(backup_dir)

# 3.2 And copy the ZIP file from temp to here
zip_filename = basename(zip_path)
outbound = join(backup_dir, zip_filename)
copy(zip_path, outbound)

# 3.3 Then do the Git stuff
repo_dir = "."
repo = Repo(repo_dir)
file_list = [outbound]
commit_msg = "Latest database backup"
repo.index.add(file_list)
repo.index.commit(commit_msg)
origin = repo.remote('origin')
# This should use the SSH key, so no login needed
origin.push()

# 3.4 Go back to the original dir
chdir(original_dir)

# 4. Clean-up the files
remove(outbound)
remove(target)
remove(zip_path)
