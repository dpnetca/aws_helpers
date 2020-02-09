#!/usr/bin/env python

import sys
import helpers


def update_route53(instance_name):
    instance_list = helpers.find_instance_by_tag("Name", [instance_name])
    result = None
    if len(instance_list) == 1:
        new_public_ip = instance_list[0]["PublicIpAddress"]
        fqdn = helpers.deep_get(instance_list[0], ["Tags", "fqdn"])
        if fqdn:
            old_public_ip = helpers.find_route53_record(fqdn)
            if new_public_ip != old_public_ip:
                result = helpers.update_route53_record(fqdn, new_public_ip)
                update = helpers.find_route53_record(fqdn)
                result = (
                    f"Changed {fqdn} from {old_public_ip} to {new_public_ip}\n"
                    f"Update = {update}"
                )
            else:
                result = (
                    f"No Change, {fqdn} already resolves to {new_public_ip}"
                )
        else:
            result = f"fqdn not defined for instance '{instance_name}'"
    else:
        result = f"instance '{instance_name}' not found"
    return result


if __name__ == "__main__":
    print(update_route53(sys.argv[1]))
