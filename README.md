# AI-Powered Document Processing System — Architecture

> Automated document-processing pipeline using Amazon Textract and Comprehend to extract and classify content from uploaded documents.
> Repo: [github.com/bukx/ai-document-processor](https://github.com/bukx/ai-document-processor)

![Architecture](./architecture.png)

## Mermaid view

```mermaid
flowchart LR
    U(["📄 Uploaders"])

    subgraph Ingest["Ingestion"]
        API["Upload API"]
        RAW["S3<br/>raw documents"]
    end

    subgraph Orch["Orchestration — Step Functions"]
        SFN["State Machine<br/>async workflow"]
        SQS["SQS<br/>work queue + retry"]
    end

    subgraph Lambdas["Processing Lambdas (Python)"]
        PARSE["Parse"]
        CLASS["Classify"]
        ROUTE["Downstream Routing"]
    end

    subgraph ML["AI / ML"]
        TEX["Textract<br/>extract text"]
        COMP["Comprehend<br/>classify content"]
    end

    DDB[("DynamoDB<br/>extracted data")]
    OUT["S3<br/>processed output"]
    CW["CloudWatch<br/>metrics + alarms"]

    U -- upload --> API --> RAW
    RAW -- event --> SFN
    SFN --> SQS --> PARSE
    PARSE -- OCR --> TEX --> CLASS
    CLASS -- NLP --> COMP --> ROUTE
    ROUTE --> DDB
    ROUTE --> OUT
    SQS -. DLQ / retry .-> SFN
    PARSE -. logs .-> CW
    CLASS -. logs .-> CW
    ROUTE -. logs .-> CW
    SFN -. logs .-> CW
```

## Components & data flow

| Stage | Service | Responsibility |
|-------|---------|----------------|
| Ingestion | **API Gateway + S3** | Accept document uploads; land raw files in S3, which emits an event. |
| Orchestration | **Step Functions + SQS** | Drive the multi-step workflow; SQS buffers work and absorbs retries for reliable async processing. |
| Extraction | **Textract** | OCR / structured text extraction from each document. |
| Classification | **Comprehend** | NLP classification + entity detection on the extracted text. |
| Compute | **Lambda (Python)** | `parse`, `classify`, `route` functions implement parsing, classification, and downstream routing. |
| Output | **DynamoDB + S3** | Persist extracted/structured data and processed artifacts. |
| Observability | **CloudWatch** | Metrics and alarms surface pipeline health and failures. |

## Design notes
- **Reliability:** Step Functions + SQS decouple stages; failed messages flow to a DLQ and retry without losing work.
- **Error handling:** each state has explicit catch/retry; alarms fire on queue depth, Lambda errors, and state-machine failures.
- **Separation of concerns:** one Lambda per processing responsibility keeps each function small and independently scalable.

## Render the PNG
```bash
python architecture.py   # requires: pip install diagrams  +  graphviz binary
```
