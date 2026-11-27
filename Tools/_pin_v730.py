# -*- coding: utf-8 -*-
# _pin_v730.py - rewrite the six male/E04 take pins in mv_rebuild_v730.py
import io

P = r"C:\Users\sjs20\Desktop\FluxGroup\Tools\mv_rebuild_v730.py"
s = io.open(P, encoding="utf-8").read()

MOVES = [
    ("C01_carver_face", r"media\MV\mv0001\v730-clips\C01_male_B_cloud768.mp4"),
    ("D01_carver_words", r"media\MV\mv0001\v730-clips\D01_male_B_cloud768.mp4"),
    ("B01_weary", r"media\MV\mv0001\v730-clips\B01_male_B_cloud768.mp4"),
    ("E01c_first_line", r"media\MV\mv0001\v730-clips\E01c_male_B_cloud768.mp4"),
    ("D03b_direct_gaze", r"media\MV\mv0001\v730-clips\D03b_v2_B_cloud768.mp4"),
    ("E04_replay_faces", r"media\MV\mv0001\v730-clips\E04_gaze_B_cloud768.mp4"),
]

lines = s.split("\n")
hit = set()
for i, line in enumerate(lines):
    for key, newtail in MOVES:
        marker = '"%s": r"' % key
        if line.lstrip().startswith(marker):
            head = line.split('r"')[0]
            comment = ""
            if "  #" in line:
                comment = "  #" + line.split("  #", 1)[1]
            lines[i] = head + 'r"C:\\Users\\sjs20\\Desktop\\FluxGroup\\' + newtail + '"' + comment + "  # v730 pin"
            hit.add(key)
if len(hit) != len(MOVES):
    raise SystemExit("MISSING PINS: %s" % (set(k for k, _ in MOVES) - hit))
io.open(P, "w", encoding="utf-8").write("\n".join(lines))
print("PINS-OK", sorted(hit))
