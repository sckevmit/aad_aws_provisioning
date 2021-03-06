"""
Utility functions for AWS IAM role-based activities
"""
import logging
import json
import boto3
from botocore.exceptions import ClientError
from provisioner.exceptions import TrustRoleExistsError, RoleNotFoundError

__logger__ = logging.getLogger(__name__)
__iam_client__ = boto3.client('iam')

def add_trust_role(federated_role_template_file, saml_provider_arn, role_name, role_description):
    "Adds a role with the federated identity provider set to `saml_provider_arn`"
    try:
        role_definition_json = json.load(open(federated_role_template_file))
        role_definition_json["Statement"][0]["Principal"]["Federated"] = saml_provider_arn
        role_definition = json.dumps(role_definition_json)
        response = __iam_client__.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=role_definition,
            Description=role_description
        )
        return response["Role"]["Arn"]
    except FileNotFoundError:
        __logger__.error("Unable to locate template file %s", federated_role_template_file)
        raise
    except ClientError as client_error:
        if client_error.response['Error']['Code'] == 'EntityAlreadyExists':
            __logger__.warning("SAML provider already exists...")
            raise TrustRoleExistsError(role_name)
        else:
            __logger__.error("Something went wrong creating the Trust Role: %s", client_error)
            raise

def look_up_role(role_name):
    """
    Look up a role based on it's noame
    """
    try:
        response = __iam_client__.get_role(RoleName=role_name)
        return response
    except ClientError as client_error:
        if client_error.response['Error']['Code'] == 'NoSuchEntity':
            __logger__.warning("Role '%s' not found...", role_name)
            raise RoleNotFoundError(role_name)
        else:
            __logger__.error("Unable to find role %s: %s", role_name, client_error)
            raise
