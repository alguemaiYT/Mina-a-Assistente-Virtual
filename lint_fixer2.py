import re

def fix_file(path):
    with open(path, "r") as f:
        lines = f.readlines()

    out_lines = []
    for line in lines:
        if line.endswith(" \n"):
            line = line.rstrip() + "\n"
        if line == " \n" or line == "  \n" or line == "    \n" or line == "        \n":
            line = "\n"
        out_lines.append(line)

    with open(path, "w") as f:
        f.writelines(out_lines)

fix_file("src/utils/academic_db.py")
fix_file("src/utils/tts_client.py")
