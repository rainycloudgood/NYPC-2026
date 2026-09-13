"""단일 제출 파일 생성: challenge_submission_cpp_oracle.cpp 의 #include "known_cases.inc"
를 실제 내용으로 치환해 self-contained 한 submission_oracle.cpp 를 만든다.
(채점기는 소스 1개만 받으므로 .inc 를 인라인해야 함)"""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, 'challenge_submission_cpp_oracle.cpp'), encoding='utf-8').read()
inc = open(os.path.join(HERE, 'known_cases.inc'), encoding='utf-8').read()
out = src.replace('#include "known_cases.inc"', inc.rstrip('\n'))
assert '#include "known_cases.inc"' not in out, 'include 치환 실패'
dst = os.path.join(HERE, 'submission_oracle.cpp')
open(dst, 'w', encoding='utf-8', newline='\n').write(out)
print('wrote', dst, f'({len(out)} bytes)')
