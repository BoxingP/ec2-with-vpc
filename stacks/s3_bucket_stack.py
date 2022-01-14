from aws_cdk import (
    aws_s3 as s3,
    core as cdk
)


class S3BucketStack(cdk.Stack):
    def __init__(self, scope: cdk.Construct, construct_id: str, bucket_name: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        s3_bucket = s3.Bucket(
            self, 'S3Bucket', bucket_name=bucket_name,
            versioned=True,
            removal_policy=cdk.RemovalPolicy.DESTROY,
            auto_delete_objects=False,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL
        )
        s3_bucket.add_lifecycle_rule(
            id="abort-incomplete-multipart-upload",
            abort_incomplete_multipart_upload_after=cdk.Duration.days(3),
            enabled=True
        )
        s3_bucket.add_lifecycle_rule(
            id="transitions-to-glacier",
            transitions=[
                s3.Transition(
                    storage_class=s3.StorageClass.GLACIER,
                    transition_after=cdk.Duration.days(90)
                )
            ],
            noncurrent_version_transitions=[
                s3.NoncurrentVersionTransition(
                    storage_class=s3.StorageClass.GLACIER,
                    transition_after=cdk.Duration.days(90)
                )
            ],
            enabled=True
        )

        cdk.CfnOutput(
            self, 'OutputS3BucketName',
            export_name=construct_id.title().replace('-', '') + 'BucketName', value=s3_bucket.bucket_name
        )
