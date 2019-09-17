import glob
import os.path
import sys

SPLIT_NUM = 4

for fname in glob.glob(sys.argv[1]):
    print(f"Processing {fname}")
    with open(fname) as f:
        words = [w.strip() for w in f.readlines() if w.strip()]
    name, ext = os.path.splitext(fname)
    num_per_file = int(len(words) / SPLIT_NUM)
    cur_offset = 0
    for n in range(SPLIT_NUM):
        if n == SPLIT_NUM - 1:  # last iter
            to_write = words[cur_offset:]
        else:
            to_write = words[cur_offset:cur_offset + num_per_file]
            cur_offset += num_per_file

        with open(name + '_{}of{}{}'.format(n + 1, SPLIT_NUM, ext), 'w') as f:
            for w in to_write:
                f.write(w + '\n')
