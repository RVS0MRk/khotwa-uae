"""Read-only source/history secret and dependency audit; never prints secrets.

Usage: python review/audit_release.py --output release-security.json
No credential files, academic reports, network or Git mutations are used.
"""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PRIVATE = re.compile(r'(?:^|/)(?:secret\.txt|\.env(?:$|\.(?!example$))|\.venv|venv|node_modules|__pycache__|\.git)(?:/|$)|FWS310|\.(?:docx?|pptx?|xlsx?)$', re.I)
SECRET = re.compile(rb'gsk_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{24,}|gh[pousr]_[A-Za-z0-9]{25,}|AKIA[A-Z0-9]{16}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|https?://[^\s/@]+:[^\s/@]+@')
SYNTHETIC = {b'gsk_'+b'01234567890123456789', b'gsk_'+b'12345678901234567890'}


def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT)


def scan(data):
    return sum(m.group() not in SYNTHETIC for m in SECRET.finditer(data))


def audit():
    names = git('ls-files','--cached','--others','--exclude-standard','-z').decode().split('\0')
    rows, findings, excluded = [], [], []
    for name in filter(None, names):
        if PRIVATE.search(name):
            excluded.append(name)
            continue
        path = ROOT / name
        if not path.is_file():
            continue
        data = path.read_bytes()
        count = scan(data)
        rows.append({'path':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
        if count:
            findings.append({'area':'candidate source','path':name,'count':count,'values':'suppressed'})
    objects = {}
    private_history_paths = []
    credential_history_paths = []
    for line in git('rev-list','--objects','--all').decode().splitlines():
        oid, _, name = line.partition(' ')
        if name and PRIVATE.search(name):
            private_history_paths.append(name)
            if re.search(r'(?:^|/)(?:secret\.txt|\.env(?:$|\.(?!example$)))(?:/|$)',name,re.I):
                credential_history_paths.append(name)
        if not name or PRIVATE.search(name):
            continue  # Never open private files/reports, even in history.
        objects.setdefault(oid,name)
    process = subprocess.Popen(['git','cat-file','--batch'],cwd=ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
    scanned = 0
    try:
        for oid,name in objects.items():
            process.stdin.write((oid+'\n').encode());process.stdin.flush()
            header = process.stdout.readline().decode().strip().split()
            if len(header)!=3:
                raise RuntimeError('Invalid git object header')
            _,kind,size=header
            data=process.stdout.read(int(size));process.stdout.read(1)
            if kind!='blob':
                continue
            scanned += 1
            count=scan(data)
            if count:
                findings.append({'area':'git history','path':name,'object':oid,'count':count,'values':'suppressed'})
    finally:
        process.stdin.close();process.wait(timeout=10)
    ignored={name:subprocess.run(['git','check-ignore','-q',name],cwd=ROOT).returncode==0
             for name in ('secret.txt','.env','.venv/','node_modules/','outputs/.demo-signing-key','outputs/private.pdf')}
    return {'head':git('rev-parse','HEAD').decode().strip(),'branch':git('branch','--show-current').decode().strip(),
            'source_files_scanned':len(rows),'history_blobs_scanned':scanned,'private_candidates_excluded_without_reading':excluded,
            'findings':findings,'ignore_rules':ignored,'source_inventory':rows,
            'private_history_files_excluded_without_reading':len(set(private_history_paths)),
            'potential_credential_filenames_in_history':sorted(set(credential_history_paths)),
            'secret_values_printed':False,'academic_reports_opened':False,
            'scope':'Known credential/private-key patterns, candidate source and reachable nonprivate Git blobs. Not a guarantee of detecting arbitrary unknown secrets.'}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);args=parser.parse_args()
    report=audit();Path(args.output).write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('Source files:',report['source_files_scanned'],'history blobs:',report['history_blobs_scanned'],'potential credential findings:',len(report['findings']))
    print('Ignore rules:',all(report['ignore_rules'].values()),'; credential values suppressed; no academic reports opened')
    print('Potential credential filenames in history:',len(report['potential_credential_filenames_in_history']))
    raise SystemExit(1 if report['findings'] or report['potential_credential_filenames_in_history'] else 0)
