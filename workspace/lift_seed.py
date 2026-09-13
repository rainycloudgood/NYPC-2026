# 기존 해를 k행 더 큰 격자로 들어올림 (아래에 통과행 추가).
# 굴을 겨냥한 햄스터 거리(r+dist==R+1)는 +k 보정, 나머지는 그대로.
# 다람쥐 'D' 체인은 새 통과행을 거쳐 굴로 내려간다.
# usage: python lift_seed.py <src_output.txt> <k> <dst.txt>
import sys

src, k, dst = sys.argv[1], int(sys.argv[2]), sys.argv[3]
tok = open(src).read().split()
R = int(tok[0])
body = tok[1:]
C = len(body) // R
assert len(body) == R * C
newR = R + k

new_body = []
for r in range(1, R + 1):
    for c in range(C):
        t = body[(r - 1) * C + c]
        if t != 'X' and t[0].isdigit():
            i = 0
            while t[i].isdigit():
                i += 1
            dist, d = int(t[:i]), t[i:]
            if d == 'D' and r + dist == R + 1:  # 굴 직투 → 거리 +k
                t = f'{dist + k}D'
        new_body.append(t)
new_body += ['D'] * (C * k)  # 통과행 k개

with open(dst, 'w') as f:
    f.write(str(newR) + '\n')
    for r in range(newR):
        f.write(' '.join(new_body[r * C:(r + 1) * C]) + '\n')
print(dst, 'R=', newR)
