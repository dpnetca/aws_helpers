#!/usr/bin/env python

import boto3


# TODO refactor this to class
# TODO change find instance to return first matching instance
# TODO add helpers for better deailing with multiple instances
# TODO build tests...
# TODO better comments and error checking


def find_instance_by_tag(tag, value_list):
    """
    Find an EC2 instance based on provided tag name and value

    Returns list, each element of the list is dict representing a single
    instance. The values returned for each instance are a small subset of
    information available that will be used for debugging pruposes, or
    but other automation tasks
    """

    # build boto3 client, filter, and get matching instances
    ec2client = boto3.client("ec2")
    filter = [{"Name": f"tag:{tag}", "Values": value_list}]
    instances = ec2client.describe_instances(Filters=filter)

    # initiate empty list
    instance_list = list()

    # each reservation in the returned list represents once EC2 instance
    for reservation in instances["Reservations"]:
        # the returned "instances" is a list, I have not seen a case where
        # this is more then 1 record deep though, but loop through just in case
        for instance in reservation["Instances"]:
            # initiate empty dict
            instance_dict = {}
            # get select key value pairs
            instance_dict.update(_tags_to_dict(instance["Tags"]))
            instance_dict["InstanceId"] = instance.get("InstanceId")
            instance_dict["PublicIpAddress"] = instance.get("PublicIpAddress")
            instance_dict["state_name"] = deep_get(
                instance, ["State", "Name"], default=None
            )
            instance_list.append(instance_dict)

    return instance_list


def start_instance(instance_id):
    ec2client = boto3.client("ec2")
    result = ec2client.start_instances(InstanceIds=[instance_id])
    return result


def stop_instance(instance_id):
    ec2client = boto3.client("ec2")
    result = ec2client.stop_instances(InstanceIds=[instance_id])
    return result


def find_route53_record(fqdn):
    """
    found the resource record set for fqdn
    TODO allow user to pass in hosted zone name or ID
    """
    r53client = boto3.client("route53")
    hosted_zone_id = find_route53_hosted_zone_id(fqdn)
    response = r53client.list_resource_record_sets(
        HostedZoneId=hosted_zone_id, StartRecordName=fqdn
    )
    # assuming one response return the Public IP else return None
    # TODO better handing for 0 results or multiple results
    result = None
    if len(response["ResourceRecordSets"]) > 0:
        # assume first response is the one we want
        record = response["ResourceRecordSets"][0]
        # TODO what if more then 1 public IP?
        result = record["ResourceRecords"][0]["Value"]  # public IP
    return result


def find_route53_hosted_zone_id(fqdn):
    """
    find the hosted zone ID based on FQDN assumes the zone is the end of FQDN
    in format ABCD.XYZ
    """
    r53client = boto3.client("route53")
    # split FQDN into components
    fqdn_split = fqdn.split(".")
    # combine last two sections for split FQDN to for zone name
    domain = ".".join(fqdn_split[-2:])

    response = r53client.list_hosted_zones_by_name(DNSName=domain)

    # assuming one response return the zone ID else return None
    # TODO better handing 0 or 2+ results
    result = None
    if len(response["HostedZones"]) == 1:
        result = response["HostedZones"][0]["Id"]
    return result


def update_route53_record(fqdn, ip):
    """
    update DNS entry based on passed in FQDN and IP
    TODO allow user to pass in hosted zone name or ID
    """
    r53client = boto3.client("route53")
    hosted_zone_id = find_route53_hosted_zone_id(fqdn)
    change_batch = {
        "Comment": f"update {fqdn} -> {ip}",
        "Changes": [
            {
                "Action": "UPSERT",
                "ResourceRecordSet": {
                    "Name": fqdn,
                    "Type": "A",
                    "TTL": 300,
                    "ResourceRecords": [{"Value": ip}],
                },
            }
        ],
    }
    result = r53client.change_resource_record_sets(
        HostedZoneId=hosted_zone_id, ChangeBatch=change_batch
    )
    return result


def _tags_to_dict(tags):
    """
    convert tags from list if dicts to embeded dict
    """
    result = {}
    for tag in tags:
        result[tag["Key"]] = tag["Value"]

    return {"Tags": result}


def deep_get(dictionary, keys, default=None):
    """
    a safe get function for multi level dictionary
    """
    if dictionary is None:
        return default
    if not keys:
        return dictionary
    return deep_get(dictionary.get(keys[0]), keys[1:])


if __name__ == "__main__":
    print("do not run directly...")
