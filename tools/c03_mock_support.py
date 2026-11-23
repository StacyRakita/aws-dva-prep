#!/usr/bin/env python3
"""Add fixed mock exams (D.MOCKS) support to the AWS app, as in the Claude app. Idempotent."""
import os, re

INDEX = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "index.html")
s = open(INDEX, encoding="utf-8").read()
if "D.MOCKS" in s:
    print("mock support already present"); raise SystemExit(0)


def rep(old, new, count=1):
    global s
    c = s.count(old)
    assert c == count, (c, old[:90])
    s = s.replace(old, new)


# 1. build and start an exam from a fixed paper
rep('''function buildExam(){
  var order=Object.keys(D.DOMAINS)''', '''function buildExam(mock){
  if(mock&&D.MOCKS){ var mk=D.MOCKS.filter(function(m){ return m.id===mock; })[0]; if(mk){ var by={}; QB.forEach(function(q){ by[q.id]=q; }); var ql=mk.ids.map(function(i){ return by[i]; }).filter(Boolean); if(ql.length) return ql; } }
  var order=Object.keys(D.DOMAINS)''')
rep('''function startExam(){
  var qs=buildExam(); E={qs:qs,''', '''function startExam(mock){
  var qs=buildExam(mock); E={mock:mock||null,qs:qs,''')
rep("S.exams.push({t:Date.now(),pct:pct,per:per});", "S.exams.push({t:Date.now(),pct:pct,per:per,mock:E.mock||undefined});")

# 2. practice tab: card with the fixed papers and the best and last score of each
mock_card = ("  if(D.MOCKS&&D.MOCKS.length){ h+='<div class=\"card\"><h3>Mock exams</h3><div class=\"muted\">Fixed papers with the C03 domain weights, '+D.EXAM.n+' questions each, including questions with several correct answers. Each paper has the same questions every time, so a better score means you improved, not that you got a luckier draw. Different mocks have different questions.</div>'"
             "+D.MOCKS.map(function(m){ var tries=S.exams.filter(function(e){ return e.mock===m.id; }), best=tries.reduce(function(a,e){ return Math.max(a,e.pct); },-1), last=tries.length?tries[tries.length-1].pct:null; "
             "return '<button class=\"item\" data-mock=\"'+m.id+'\"><span>'+esc(m.name)+'<small>'+m.ids.length+' questions, '+D.EXAM.minutes+' minutes'+(tries.length?' &middot; last '+last+'%, best '+best+'% ('+tries.length+'x)':' &middot; not taken yet')+'</small></span><span class=\"tag '+(best>=D.EXAM.pass?\"ok\":(best>=0?\"bad\":\"\"))+'\">'+(best>=0?best+\"%\":\"start\")+'</span></button>'; }).join(\"\")+'</div>'; }\n")
marker = "  h+='<div class=\"card\"><h3>By domain</h3>'"
rep(marker, mock_card + marker)
rep('main.querySelectorAll("[data-mix]")', 'main.querySelectorAll("[data-mock]").forEach(function(x){ x.onclick=function(){ startExam(x.dataset.mock); }; });\n  main.querySelectorAll("[data-mix]")')

# 3. progress tab shows which paper an exam was
rep("new Date(e.t).toLocaleDateString(\"en-GB\")+'</span>", "new Date(e.t).toLocaleDateString(\"en-GB\")+(e.mock?' &middot; Mock '+e.mock.slice(1):' &middot; random')+'</span>")

# 4. plan days can point at a specific mock (field "mock" in the plan item)
rep('''(p.act==="exam"?'<button class="btn primary grow" data-act="exam">Start the exam</button>':"")''',
    '''(p.act==="exam"?'<button class="btn primary grow" data-mockexam="'+(p.mock||"")+'">Start the exam'+(p.mock&&D.MOCKS?' ('+esc((D.MOCKS.filter(function(m){ return m.id===p.mock; })[0]||{name:""}).name)+')':"")+'</button>':"")''')
rep('main.querySelectorAll("[data-act]").forEach(function(x){ x.onclick=function(){ action(x.dataset.act); }; });\n}\nfunction action(a){',
    'main.querySelectorAll("[data-act]").forEach(function(x){ x.onclick=function(){ action(x.dataset.act); }; });\n  main.querySelectorAll("[data-mockexam]").forEach(function(x){ x.onclick=function(){ startExam(x.dataset.mockexam||undefined); }; });\n}\nfunction action(a){')
open(INDEX, "w", encoding="utf-8").write(s)
print("mock support added")
