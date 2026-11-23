#!/usr/bin/env python3
"""Rewrite the AWS plan for DVA-C03: 21 days (23 Nov to 13 Dec 2026), exam on 14 Dec. Idempotent."""
import json, os, re

INDEX = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "index.html")
ser = lambda d: json.dumps(d, ensure_ascii=False).replace("</", "<\\/")

BG = "https://docs.aws.amazon.com/bedrock/latest/userguide/"
AC = "https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/"
ECR = "https://docs.aws.amazon.com/AmazonECR/latest/userguide/"
ECS = "https://docs.aws.amazon.com/AmazonECS/latest/developerguide/"
S3 = "https://docs.aws.amazon.com/AmazonS3/latest/userguide/"
CF = "https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/"
EXAM_GUIDE = "https://docs.aws.amazon.com/aws-certification/latest/developer-associate-03/developer-associate-03.html"


def day(title, videos=(), theory=(), quiz=(), target=40, tasks="", act="", read=()):
    p = {"title": title, "videos": [list(v) for v in videos], "theory": list(theory), "quiz": list(quiz),
         "target": target, "tasks": tasks, "act": act}
    if read:
        p["read"] = [list(r) for r in read]
    return p


PLAN = [
    day("IAM, CLI/SDK and S3 (basics, security)",
        [("IAM & AWS CLI", 58), ("AWS CLI, SDK, IAM Roles & Policies", 26), ("Amazon S3 Introduction", 49), ("Advanced Amazon S3", 23), ("Amazon S3 Security", 49)],
        ["iam", "cli-sdk", "s3"], ["iam", "cli-sdk", "s3"], 40),
    day("EC2, load balancing, Auto Scaling, RDS and ElastiCache (the lighter day: watch at 1.5 to 2x)",
        [("EC2 Fundamentals", 80), ("EC2 Instance Storage", 56), ("ELB + ASG", 96), ("RDS + Aurora + ElastiCache", 64)],
        ["ec2", "storage", "elb-asg", "rds"], ["ec2", "storage", "elb-asg", "rds"], 45),
    day("Lambda (task 1.2): configuration, events, errors, VPC, concurrency",
        [("Lambda: intro, invocations, events, destinations, permissions, env vars, monitoring", 92), ("Lambda: VPC, performance, layers, concurrency, versions, URLs, limits", 92)],
        ["lambda"], ["lambda"], 45),
    day("API Gateway, Cognito, Step Functions and AppSync",
        [("API Gateway", 82), ("Cognito", 39), ("Other Serverless: Step Functions & AppSync", 58)],
        ["apigw", "cognito", "stepfunctions"], ["apigw", "cognito", "stepfunctions"], 40),
    day("DynamoDB (task 1.3) and advanced identity (STS). Do not skip DynamoDB: the exam guide merged its skills but kept the weight",
        [("DynamoDB", 106), ("Advanced Identity", 23)],
        ["dynamodb", "iam-adv"], ["dynamodb", "iam-adv"], 40),
    day("SQS, SNS, Kinesis, EventBridge and other services (decoupling, event-driven patterns)",
        [("SQS, SNS & Kinesis", 102), ("AWS Other Services", 34)],
        ["messaging", "other"], ["messaging", "other"], 40),
    day("Checkpoint 1: domain 1 review (development)",
        theory=["limits"], tasks="No new material. Run the due reviews, then Practice → Weak topics until your weakest topics are above 75%. Re-read Key numbers.",
        act="weak", target=50),
    day("Security: KMS, Secrets Manager, SSM, encryption (task 2.2) and CloudFront with presigned URLs and signing (skill 2.1.4)",
        [("AWS Security & Encryption", 89), ("CloudFront", 49)],
        ["security", "cloudfront"], ["security", "presigned", "cloudfront"], 45,
        read=[("S3 presigned URLs: who signs, expiry, GET and PUT", 20, S3 + "using-presigned-url.html"),
              ("CloudFront signed URLs and signed cookies", 20, CF + "private-content-signed-urls.html")]),
    day("NEW in C03: securing AI services (task 2.3), part 1: access, private connectivity, Guardrails, logs",
        quiz=["ai"], target=25,
        read=[("Amazon Bedrock Guardrails: policy types and how to use them", 25, BG + "guardrails.html"),
              ("Guardrails: the prompt attack filter", 10, BG + "guardrails-prompt-attack.html"),
              ("Bedrock and interface VPC endpoints (AWS PrivateLink)", 15, BG + "vpc-interface-endpoints.html"),
              ("Bedrock model invocation logging", 15, BG + "model-invocation-logging.html"),
              ("CloudWatch Logs: mask sensitive log data", 15, "https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/mask-sensitive-log-data.html")]),
    day("NEW in C03: securing AI services (task 2.3), part 2: agents, human approval, AI-assisted development",
        quiz=["ai"], target=25,
        read=[("What is Amazon Bedrock AgentCore: the components", 15, AC + "what-is-bedrock-agentcore.html"),
              ("AgentCore Runtime sessions and isolation", 10, AC + "runtime-sessions.html"),
              ("AgentCore Gateway and Policy", 20, AC + "gateway.html"),
              ("Bedrock Agents: return of control", 10, BG + "agents-returncontrol.html"),
              ("Bedrock Agents: action groups and confirmation", 10, BG + "agents-action-add.html")]),
    day("Containers and artifacts (tasks 3.1 and 3.3): ECR, Dockerfile, ECS, EKS, Fargate",
        [("ECS, ECR & Fargate", 71)], ["ecs"], ["containers", "ecs"], 40,
        read=[("ECR lifecycle policies", 15, ECR + "LifecyclePolicies.html"),
              ("ECR tag immutability", 5, ECR + "image-tag-mutability.html"),
              ("ECS deployment circuit breaker", 10, ECS + "deployment-circuit-breaker.html"),
              ("Lambda functions from container images", 10, "https://docs.aws.amazon.com/lambda/latest/dg/images-create.html")]),
    day("Infrastructure as code and testing (task 3.2): CloudFormation, SAM, CDK, test events, mock APIs",
        [("CloudFormation", 71), ("SAM", 35), ("CDK", 26)],
        ["cfn", "sam", "cdk"], ["cfn", "sam", "cdk"], 40),
    day("CI/CD and deployment strategies (task 3.3): CodeBuild, CodeDeploy, CodePipeline, Elastic Beanstalk",
        [("AWS CICD", 91), ("Elastic Beanstalk", 59)],
        ["cicd", "beanstalk", "patterns"], ["cicd", "beanstalk"], 40),
    day("Checkpoint 2: first full exam simulator",
        theory=["exam"], tasks="In the app: Practice → Exam simulator (65 questions, 130 minutes, no pauses). Then go through every mistake in the Mistake notebook (Progress tab) and read the notes for each weak topic.",
        act="exam", target=0),
    day("Troubleshooting and observability (domain 4 is 22% in C03): CloudWatch, X-Ray, CloudTrail",
        [("CloudWatch, X-Ray, CloudTrail", 108)],
        ["monitoring", "troubleshoot"], ["monitoring"], 45),
    day("Optimization (task 4.3): concurrency, caching with ElastiCache, DAX and CloudFront, messaging, memory and compute",
        theory=["lambda", "dynamodb", "rds", "cloudfront"], quiz=["lambda", "dynamodb", "rds", "messaging"], target=40),
    day("Optimization and the rest: Route 53, VPC (watch at 2x or only read the notes)",
        [("VPC Fundamentals", 25), ("Route 53 (watch at 2x or only read the theory)", 82)],
        ["vpc", "r53", "limits"], ["vpc", "r53"], 35),
    day("Weak topics and the mistake notebook",
        theory=["limits"], tasks="Practice → Weak topics until the weakest topics are above 80%. Then Practice → Mistakes. Re-watch the two weakest course sections at 1.5x.",
        act="weak", target=50),
    day("The course practice test, then review every wrong answer",
        [("Practice Test - AWS Certified Developer Associate (course)", 130)],
        tasks="Do the course practice test in one sitting. The course is still based on DVA-C02, so do not worry about questions on AI security or containers here. Review every wrong answer, then Practice → Mistakes in the app.",
        target=0),
    day("Checkpoint 3: second full exam simulator",
        theory=["exam"], tasks="Take a second full exam. Aim for 80% or more. Fix the gaps with Weak topics and the notes.",
        act="exam", target=0,
        read=[("Official DVA-C03 exam guide: read the tasks once more and tick off what you know", 20, EXAM_GUIDE)]),
    day("Final review, no new material",
        theory=["limits", "exam"], quiz=[], target=40,
        tasks="Do the due reviews. Re-read Key numbers and Exam tips. Re-read the AI security and container questions you missed. Prepare what you need for the exam day and sleep well. The exam is tomorrow."),
]
assert len(PLAN) == 21


def main():
    s = open(INDEX, encoding="utf-8").read()
    m = re.search(r"var D = (\{.*?\});\n", s, re.S)
    raw = m.group(1)
    D = json.loads(raw)
    assert ser(D) == raw
    for p in PLAN:
        for g in p["theory"]:
            assert g in D["GROUPS"], g
        for t in p["quiz"]:
            assert t in D["TOPICS"], t
    D["PLAN"] = PLAN
    s = s.replace("var D = " + raw + ";\n", "var D = " + ser(D) + ";\n", 1)

    # a "Read" card for plan days that point at AWS documentation (links open in the Telegram browser)
    marker = "  if(hasT&&D.GM){ var rl=readingList(p.theory);"
    if "p.read&&p.read.length" not in s:
        assert s.count(marker) == 1
        card = ("  if(p.read&&p.read.length){ h+='<div class=\"card\"><h3>'+(nn++)+'. Read (AWS documentation)</h3>'+p.read.map(function(r){ return '<a class=\"item\" data-ext=\"'+esc(r[2])+'\" href=\"'+esc(r[2])+'\" target=\"_blank\" rel=\"noopener\" style=\"text-decoration:none;color:inherit\"><span>'+esc(r[0])+'</span><span class=\"muted\">'+r[1]+' min</span></a>'; }).join(\"\")+'<div class=\"muted\" style=\"margin-top:6px\">About '+p.read.reduce(function(a,r){ return a+r[1]; },0)+' min. These are the official pages the questions are based on.</div></div>'; }\n")
        s = s.replace(marker, card + marker, 1)
        bind = "  main.innerHTML=h;\n  var b; if((b=main.querySelector('[data-go]')))"
        assert s.count(bind) == 1
        s = s.replace(bind, "  main.innerHTML=h;\n  main.querySelectorAll(\"[data-ext]\").forEach(function(a){ a.onclick=function(e){ if(tg&&tg.openLink){ e.preventDefault(); try{ tg.openLink(a.dataset.ext); }catch(x){ window.open(a.dataset.ext,\"_blank\"); } } }; });\n  var b; if((b=main.querySelector('[data-go]')))", 1)
    open(INDEX, "w", encoding="utf-8").write(s)
    print("plan: %d days, %d of them with AWS documentation reading" % (len(PLAN), sum(1 for p in PLAN if p.get("read"))))


if __name__ == "__main__":
    main()
