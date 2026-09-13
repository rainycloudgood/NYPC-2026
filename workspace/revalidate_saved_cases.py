import argparse,glob,os,re,statistics,subprocess,sys,time

HERE=os.path.dirname(os.path.abspath(__file__));OUT=os.path.join(HERE,'outputs')
EXE=os.path.join(HERE,'public1_offline_optimizer.exe')
ap=argparse.ArgumentParser();ap.add_argument('--pid',required=True);ap.add_argument('--sub',required=True)
args=ap.parse_args();sub=os.path.join(HERE,args.sub);rows=[]
for ip in sorted(glob.glob(os.path.join(OUT,f'midval_{args.pid}_*.in'))):
 inp=open(ip).read();tag=os.path.basename(ip)[:-3]+'_re';gp=os.path.join(OUT,tag+'.grid');op=gp+'.out'
 st=time.perf_counter();p=subprocess.run([sys.executable,sub],input=inp,text=True,capture_output=True,check=True)
 ms=(time.perf_counter()-st)*1000;open(gp,'w').write(p.stdout)
 q=subprocess.run([EXE,ip,gp,op,'0','0','1'],text=True,capture_output=True,check=True)
 m=re.search(r'START cost=(\d+) E=(\d+) D=(\d+) L=(\d+)',q.stderr);z=tuple(map(int,m.groups()));rows.append((z,ms))
cost=[x[0][0] for x in rows]
print('pid',args.pid,'n',len(rows),'over100',sum(x>100000 for x in cost),'L',sum(x[0][3]>0 for x in rows),
      'median',int(statistics.median(cost)),'max',max(cost),'runtime_max_ms',round(max(x[1] for x in rows),1),
      'runtime_med_ms',round(statistics.median(x[1] for x in rows),1))
