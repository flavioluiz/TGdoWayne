"""Build and verify the review manuscript, preserving the resulting PDF in article/."""
from pathlib import Path
import os,re,shutil,subprocess
R=Path(__file__).resolve().parents[1]
env=dict(os.environ);env['PATH']='/Library/TeX/texbin:'+env.get('PATH','');env['SOURCE_DATE_EPOCH']='1789171200';env['FORCE_SOURCE_DATE']='1'
subprocess.run(['latexmk','-pdf','-interaction=nonstopmode','-halt-on-error','-file-line-error','-pdflatex=pdflatex -no-shell-escape %O %S','-outdir='+str(R/'tmp/article_c12'),'manuscript.tex'],cwd=R/'article',env=env,check=True)
log=(R/'tmp/article_c12/manuscript.log').read_text(errors='replace')
issues=[line for line in log.splitlines() if 'Overfull \\' in line or re.search(r'(Citation|Reference).*undefined|There were undefined|Please.*rerun Biber',line)]
if issues:raise RuntimeError('\n'.join(issues))
shutil.copyfile(R/'tmp/article_c12/manuscript.pdf',R/'article/manuscript.pdf')
print('Manuscript compiled with resolved references and no overfull boxes.')
