# 기존 출력에 맨 아래 'D' 통과 행을 1줄 추가한 시드 생성 (R -> R+1)
# 기본비용이 2배가 되는 대신 배선 공간이 늘어난다. 굴을 겨냥한 햄스터의
# 거리를 +1 보정하고, 옛 R행의 다람쥐 D는 새 통과 행을 거쳐 굴로 간다(+1턴).
#
# usage: python make_seed_taller.py <테스트번호>  ->  outputs/seed_<i>_r<R+1>.txt
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
idx = int(sys.argv[1])
path = os.path.join(HERE, 'outputs', f'output_{idx}.txt')
out = open(path).read().split()
R = int(out[0])
# 입력에서 C 파악
inp = open(rf'C:\Users\<user>\Downloads\input_{idx}.txt').read().split()
C = int(inp[0])
body = out[1:]
assert len(body) == R * C

new_body = []
for r in range(1, R + 1):
    for c in range(C):
        tok = body[(r - 1) * C + c]
        if tok != 'X' and tok[0].isdigit():
            i = 0
            while tok[i].isdigit():
                i += 1
            dist, d = int(tok[:i]), tok[i:]
            if d == 'D' and r + dist == R + 1:  # 굴 직투였다면 거리 +1
                tok = f'{dist + 1}D'
        new_body.append(tok)
new_body += ['D'] * C  # 새 통과 행

dst = os.path.join(HERE, 'outputs', f'seed_{idx}_r{R + 1}.txt')
with open(dst, 'w') as f:
    f.write(str(R + 1) + '\n')
    for r in range(R + 1):
        f.write(' '.join(new_body[r * C:(r + 1) * C]) + '\n')
print(dst)
