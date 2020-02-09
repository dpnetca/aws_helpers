#!/usr/bin/env python

import sys
import helpers


def start_ec2(instance_name):
    instance_list = helpers.find_instance_by_tag("Name", [instance_name])
    result = None
    if len(instance_list) == 1:
        instance_id = instance_list[0]["InstanceId"]
        result = helpers.start_instance(instance_id)
    return result


if __name__ == "__main__":
    print(start_ec2(sys.argv[1]))
