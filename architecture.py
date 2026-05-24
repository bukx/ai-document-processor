"""AI-Powered Document Processing System — architecture diagram.
Run: python architecture.py  (outputs architecture.png)
"""
from diagrams import Diagram, Cluster, Edge
from diagrams.aws.compute import Lambda
from diagrams.aws.integration import StepFunctions, SQS
from diagrams.aws.ml import Textract, Comprehend
from diagrams.aws.storage import S3
from diagrams.aws.database import Dynamodb
from diagrams.aws.management import Cloudwatch
from diagrams.aws.mobile import APIGateway
from diagrams.onprem.client import Users

graph_attr = {"fontsize": "18", "bgcolor": "white", "pad": "0.6", "splines": "spline"}

with Diagram(
    "AI-Powered Document Processing System",
    filename="architecture",
    show=False,
    direction="LR",
    graph_attr=graph_attr,
):
    users = Users("Uploaders")

    with Cluster("Ingestion"):
        upload_api = APIGateway("Upload API")
        raw = S3("S3\nraw documents")

    with Cluster("Orchestration — Step Functions"):
        sfn = StepFunctions("State Machine\nasync workflow")
        queue = SQS("SQS\nwork queue +\nretry buffer")

    with Cluster("Processing Lambdas (Python)"):
        fn_parse = Lambda("Parse")
        fn_classify = Lambda("Classify")
        fn_route = Lambda("Downstream\nRouting")

    with Cluster("AI / ML"):
        textract = Textract("Textract\nextract text")
        comprehend = Comprehend("Comprehend\nclassify content")

    with Cluster("Output"):
        store = Dynamodb("DynamoDB\nextracted data")
        results = S3("S3\nprocessed output")

    with Cluster("Observability"):
        cw = Cloudwatch("CloudWatch\nmetrics + alarms")

    # ingest
    users >> Edge(label="upload") >> upload_api >> raw
    raw >> Edge(label="event") >> sfn

    # orchestration
    sfn >> queue >> fn_parse
    fn_parse >> Edge(label="OCR") >> textract >> fn_classify
    fn_classify >> Edge(label="NLP") >> comprehend >> fn_route
    fn_route >> store
    fn_route >> results

    # error handling + monitoring
    queue >> Edge(style="dashed", color="firebrick", label="DLQ / retry") >> sfn
    for fn in (fn_parse, fn_classify, fn_route):
        fn >> Edge(style="dotted", color="darkorange") >> cw
    sfn >> Edge(style="dotted", color="darkorange") >> cw
