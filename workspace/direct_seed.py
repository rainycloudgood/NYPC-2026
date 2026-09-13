# 혼잡-0 시드 생성기: 각 열이 자기 굴로 햄스터 직투 (병합 없음 -> 반송 0)
# E는 크지만 D=0, bounces=0에서 출발해 SA가 '혼잡 없는' 쪽으로 재분배하도록.
# usage: python direct_seed.py <테스트번호> <R>
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from optimizer import read_input

idx = int(sys.argv[1])
R = int(sys.argv[2])
C, T, M, A, B = read_input(idx)
assert C <= R <= C + 20

body = ['X'] * (R * C)
for c in range(C):
    if A[c] > 0:
        body[c] = f'{R}D'   # (1,c) 햄스터 -> 굴 c 직투 (거리 R>=2)

dst = os.path.join(HERE, 'outputs', f'seed_{idx}_direct_r{R}.txt')
with open(dst, 'w') as f:
    f.write(str(R) + '\n')
    for r in range(R):
        f.write(' '.join(body[r * C:(r + 1) * C]) + '\n')
print(dst)
