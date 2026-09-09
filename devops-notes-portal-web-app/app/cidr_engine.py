import ipaddress
from typing import Dict, List, Any, Optional, Tuple

CLOUD_SPECS = {
    "aws": {
        "name": "Amazon Web Services (AWS VPC)",
        "reserved_count": 5,
        "min_vpc_prefix": 16,
        "max_vpc_prefix": 28,
        "min_subnet_prefix": 16,
        "max_subnet_prefix": 28,
        "reserved_rules": [
            {"offset": 0, "title": "Network Address", "desc": "First IP of the CIDR block. Required for network identification; cannot be assigned to an instance."},
            {"offset": 1, "title": "AWS VPC Router", "desc": "Reserved by AWS for the default virtual router inside the VPC / subnet."},
            {"offset": 2, "title": "AWS DNS Server", "desc": "Reserved for DNS resolution (AmazonProvidedDNS / Route 53 Resolver). Base IP + 2."},
            {"offset": 3, "title": "Future AWS Use", "desc": "Reserved by AWS for future configuration or internal management functions."},
            {"offset": -1, "title": "Broadcast Address", "desc": "Last IP in the CIDR block. Although AWS VPC does not support broadcast routing, this address remains strictly reserved."}
        ]
    },
    "azure": {
        "name": "Microsoft Azure (VNet)",
        "reserved_count": 5,
        "min_vpc_prefix": 8,
        "max_vpc_prefix": 29,
        "min_subnet_prefix": 8,
        "max_subnet_prefix": 29,
        "reserved_rules": [
            {"offset": 0, "title": "Network Address", "desc": "First IP of the subnet. Reserved for protocol identification."},
            {"offset": 1, "title": "Azure Default Gateway", "desc": "Assigned to the Azure default gateway for routing traffic out of the subnet."},
            {"offset": 2, "title": "Azure DNS (Primary)", "desc": "Mapped to Azure default DNS service for virtual network name resolution."},
            {"offset": 3, "title": "Azure DNS (Secondary)", "desc": "Mapped to secondary Azure internal DNS resolution services."},
            {"offset": -1, "title": "Broadcast Address", "desc": "Last IP of the subnet range. Reserved for network broadcast semantics."}
        ]
    },
    "gcp": {
        "name": "Google Cloud Platform (GCP VPC)",
        "reserved_count": 4,
        "min_vpc_prefix": 8,
        "max_vpc_prefix": 29,
        "min_subnet_prefix": 8,
        "max_subnet_prefix": 29,
        "reserved_rules": [
            {"offset": 0, "title": "Network Address", "desc": "First IP of the subnet. Reserved for network ID."},
            {"offset": 1, "title": "GCP Default Gateway", "desc": "Assigned to the subnet default gateway for VPC routing."},
            {"offset": -2, "title": "Second-to-Last Reserved", "desc": "Reserved by Google Cloud for internal routing or future management capabilities."},
            {"offset": -1, "title": "Broadcast Address", "desc": "Last IP of the subnet range. Reserved."}
        ]
    },
    "rfc": {
        "name": "Traditional RFC 1918 / On-Premise",
        "reserved_count": 2,
        "min_vpc_prefix": 1,
        "max_vpc_prefix": 32,
        "min_subnet_prefix": 1,
        "max_subnet_prefix": 32,
        "reserved_rules": [
            {"offset": 0, "title": "Network Address", "desc": "Standard RFC 791 network identifier for routing tables."},
            {"offset": -1, "title": "Broadcast Address", "desc": "Standard RFC 791 directed broadcast address for the local subnet."}
        ]
    }
}

def int_to_bin_octet(val: int) -> str:
    return format(val, "08b")

def ip_to_binary_string(ip_str: str) -> str:
    octets = ip_str.split(".")
    return ".".join([int_to_bin_octet(int(o)) for o in octets])

def calculate_cidr_details(cidr_str: str, cloud_provider: str = "aws") -> Dict[str, Any]:
    """Calculates complete mathematical, binary, and cloud-reserved parameters for any CIDR."""
    clean_cidr = cidr_str.strip()
    if "/" not in clean_cidr:
        clean_cidr += "/24"
    
    try:
        network = ipaddress.IPv4Network(clean_cidr, strict=False)
    except Exception as e:
        raise ValueError(f"Invalid IPv4 CIDR '{cidr_str}': {str(e)}")

    cloud = CLOUD_SPECS.get(cloud_provider.lower(), CLOUD_SPECS["aws"])
    prefix_len = network.prefixlen
    host_bits = 32 - prefix_len
    total_ips = 2 ** host_bits
    
    # Calculate usable IPs based on prefix and cloud reservations
    if prefix_len >= 31:
        usable_ips = 0 if prefix_len == 32 else (2 if cloud_provider == "rfc" else 0)
        reserved_count = total_ips - usable_ips
    else:
        reserved_count = cloud["reserved_count"]
        usable_ips = max(0, total_ips - reserved_count)

    # Netmask & Wildcard mask
    netmask = str(network.netmask)
    wildcard = str(network.hostmask)
    
    # Octet breakdown
    ip_octets = str(network.network_address).split(".")
    mask_octets = netmask.split(".")
    
    binary_ip = ip_to_binary_string(str(network.network_address))
    binary_mask = ip_to_binary_string(netmask)
    binary_wildcard = ip_to_binary_string(wildcard)

    # Full 32-bit array representation with network/host markers
    bit_breakdown = []
    bit_counter = 0
    for octet_idx, octet_str in enumerate(binary_ip.split(".")):
        for char_idx, bit in enumerate(octet_str):
            is_net_bit = bit_counter < prefix_len
            bit_breakdown.append({
                "bit": bit,
                "index": bit_counter,
                "octet": octet_idx + 1,
                "is_network": is_net_bit,
                "type": "Network Bit" if is_net_bit else "Host Bit"
            })
            bit_counter += 1

    # First and Last IP ranges
    first_ip = str(network.network_address)
    last_ip = str(network.broadcast_address)
    
    if prefix_len <= 30:
        first_usable = str(network.network_address + (cloud["reserved_count"] if cloud_provider != "rfc" else 1))
        last_usable = str(network.broadcast_address - (1 if cloud_provider in ["aws", "azure", "gcp", "rfc"] else 0))
    else:
        first_usable = "N/A"
        last_usable = "N/A"

    # Step-by-step Mathematical Derivations
    math_steps = [
        {
            "step": 1,
            "title": "Calculate Host Bits",
            "formula": f"32 - {prefix_len} = {host_bits} host bits",
            "explanation": f"IPv4 addresses are 32 bits long. With a /{prefix_len} prefix, {prefix_len} bits define the network, leaving {host_bits} bits for host addressing."
        },
        {
            "step": 2,
            "title": "Calculate Total IP Addresses",
            "formula": f"2^{host_bits} = {total_ips:,} total IPs",
            "explanation": f"Raising 2 to the power of host bits gives the exact total capacity of this CIDR block."
        },
        {
            "step": 3,
            "title": f"Deduct {cloud['name']} Reserved IPs",
            "formula": f"{total_ips:,} total - {reserved_count} reserved = {usable_ips:,} usable host IPs",
            "explanation": f"{cloud['name']} automatically reserves {reserved_count} specific addresses for internal routing, DNS, broadcast, and VPC management."
        }
    ]

    # Step 4: Subnet Division Formula
    if prefix_len < 30:
        example_sub_prefix = min(30, max(prefix_len + 1, 24 if prefix_len < 24 else prefix_len + 2))
        borrowed = example_sub_prefix - prefix_len
        sub_count = 2 ** borrowed
        sub_total_ips = 2 ** (32 - example_sub_prefix)
        sub_usable_ips = max(0, sub_total_ips - reserved_count)
        math_steps.append({
            "step": 4,
            "title": f"Subnet Division (Example: /{example_sub_prefix} Subnets)",
            "formula": f"2^({example_sub_prefix} - {prefix_len}) = 2^{borrowed} = {sub_count:,} Subnets",
            "explanation": f"Borrowing {borrowed} bits creates {sub_count:,} separate /{example_sub_prefix} subnets, each providing {sub_total_ips:,} total IPs ({sub_usable_ips:,} usable host IPs in {cloud['name']})."
        })

    # Specific Reserved IP list
    reserved_ips = []
    if total_ips >= 8:
        for rule in cloud["reserved_rules"]:
            offset = rule["offset"]
            if offset >= 0:
                ip_val = str(network.network_address + offset)
            else:
                ip_val = str(network.broadcast_address + (offset + 1))
            
            reserved_ips.append({
                "ip": ip_val,
                "title": rule["title"],
                "description": rule["desc"],
                "offset": f"Offset: {offset}" if offset >= 0 else f"End Offset: {offset}"
            })

    # RFC 1918 Class Classification
    first_octet = int(ip_octets[0])
    second_octet = int(ip_octets[1])
    
    if first_octet == 10:
        rfc_class = "RFC 1918 Private (Class A: 10.0.0.0/8)"
    elif first_octet == 172 and 16 <= second_octet <= 31:
        rfc_class = "RFC 1918 Private (Class B: 172.16.0.0/12)"
    elif first_octet == 192 and second_octet == 168:
        rfc_class = "RFC 1918 Private (Class C: 192.168.0.0/16)"
    elif first_octet == 100 and 64 <= second_octet <= 127:
        rfc_class = "RFC 6598 Carrier-Grade NAT (100.64.0.0/10)"
    elif first_octet == 127:
        rfc_class = "Loopback (127.0.0.0/8)"
    elif 224 <= first_octet <= 239:
        rfc_class = "Multicast (Class D)"
    else:
        rfc_class = "Public Internet Routable IPv4"

    # Subnet Breakdown Matrix (How many subnets and IPs can be created)
    subnet_matrix = []
    if prefix_len < 30:
        max_child = min(30, prefix_len + 12)
        for child_p in range(prefix_len + 1, max_child + 1):
            borrowed = child_p - prefix_len
            sub_count = 2 ** borrowed
            sub_total_ips = 2 ** (32 - child_p)
            sub_usable_ips = max(0, sub_total_ips - reserved_count)
            dummy_net = ipaddress.IPv4Network(f"0.0.0.0/{child_p}")
            subnet_matrix.append({
                "prefix": child_p,
                "borrowed_bits": borrowed,
                "subnet_count": sub_count,
                "total_ips": sub_total_ips,
                "usable_ips": sub_usable_ips,
                "netmask": str(dummy_net.netmask),
                "wildcard": str(dummy_net.hostmask),
                "formula": f"2^{borrowed} = {sub_count:,} Subnets"
            })

    return {
        "cidr": str(network),
        "ip": str(network.network_address),
        "prefix_len": prefix_len,
        "netmask": netmask,
        "wildcard": wildcard,
        "network_address": first_ip,
        "broadcast_address": last_ip,
        "first_usable": first_usable,
        "last_usable": last_usable,
        "total_ips": total_ips,
        "usable_ips": usable_ips,
        "host_bits": host_bits,
        "network_bits": prefix_len,
        "rfc_class": rfc_class,
        "cloud_provider": cloud_provider,
        "cloud_name": cloud["name"],
        "reserved_count": reserved_count,
        "math_steps": math_steps,
        "reserved_ips": reserved_ips,
        "subnet_matrix": subnet_matrix,
        "binary": {
            "ip": binary_ip,
            "netmask": binary_mask,
            "wildcard": binary_wildcard,
            "bits": bit_breakdown
        }
    }

def get_generated_subnets(parent_cidr: str, target_prefix: int, cloud_provider: str = "aws", limit: int = 100) -> Dict[str, Any]:
    """Generates the exact list of subnets with start/end IP, usable host counts and ranges."""
    parent = ipaddress.IPv4Network(parent_cidr.strip(), strict=False)
    cloud = CLOUD_SPECS.get(cloud_provider.lower(), CLOUD_SPECS["aws"])
    reserved = cloud["reserved_count"]

    if target_prefix <= parent.prefixlen or target_prefix > 32:
        raise ValueError(f"Subnet prefix /{target_prefix} must be greater than parent /{parent.prefixlen}")

    total_possible = 2 ** (target_prefix - parent.prefixlen)
    subnets_gen = parent.subnets(new_prefix=target_prefix)
    
    subnets_list = []
    for idx, sub in enumerate(subnets_gen):
        if idx >= limit:
            break
        total_ips = sub.num_addresses
        usable_ips = max(0, total_ips - reserved) if target_prefix <= 30 else 0
        first_usable = str(sub.network_address + reserved) if target_prefix <= 30 else "N/A"
        last_usable = str(sub.broadcast_address - 1) if target_prefix <= 30 else "N/A"
        subnets_list.append({
            "index": idx + 1,
            "cidr": str(sub),
            "network": str(sub.network_address),
            "broadcast": str(sub.broadcast_address),
            "first_usable": first_usable,
            "last_usable": last_usable,
            "total_ips": total_ips,
            "usable_ips": usable_ips,
            "netmask": str(sub.netmask)
        })

    return {
        "parent_cidr": str(parent),
        "target_prefix": target_prefix,
        "total_possible_subnets": total_possible,
        "returned_count": len(subnets_list),
        "subnets": subnets_list
    }

def find_next_available_subnet(parent_cidr: str, existing_subnets: List[str], target_prefix: int) -> Optional[Dict[str, Any]]:
    """Intelligently calculates the next available non-overlapping subnet inside parent_cidr."""
    parent = ipaddress.IPv4Network(parent_cidr, strict=False)
    if target_prefix <= parent.prefixlen or target_prefix > 32:
        return None

    # Parse existing subnets
    existing_nets = []
    for s in existing_subnets:
        try:
            existing_nets.append(ipaddress.IPv4Network(s.strip(), strict=False))
        except Exception:
            continue

    # Iterate over all possible subnets of target_prefix inside parent
    for candidate in parent.subnets(new_prefix=target_prefix):
        overlap = False
        for ext in existing_nets:
            if candidate.overlaps(ext):
                overlap = True
                break
        if not overlap:
            return {
                "cidr": str(candidate),
                "ip": str(candidate.network_address),
                "prefix": candidate.prefixlen,
                "total_ips": candidate.num_addresses,
                "netmask": str(candidate.netmask)
            }
    return None

def split_subnet(cidr_str: str, target_prefix: Optional[int] = None) -> List[Dict[str, Any]]:
    """Splits a subnet into smaller subnets (e.g. /24 into two /25s)."""
    net = ipaddress.IPv4Network(cidr_str.strip(), strict=False)
    if target_prefix is None:
        target_prefix = net.prefixlen + 1
    if target_prefix <= net.prefixlen or target_prefix > 32:
        raise ValueError(f"Target prefix /{target_prefix} must be greater than current /{net.prefixlen}")

    subnets = list(net.subnets(new_prefix=target_prefix))
    return [{
        "cidr": str(s),
        "network": str(s.network_address),
        "prefix": s.prefixlen,
        "total_ips": s.num_addresses,
        "netmask": str(s.netmask)
    } for s in subnets]

def merge_subnets(subnet_list: List[str]) -> Dict[str, Any]:
    """Attempts to supernet / collapse adjacent subnets into their summary CIDR block."""
    nets = [ipaddress.IPv4Network(s.strip(), strict=False) for s in subnet_list if s.strip()]
    if not nets:
        raise ValueError("No subnets provided for merge")

    collapsed = list(ipaddress.collapse_addresses(nets))
    return {
        "merged_count": len(collapsed),
        "merged_cidrs": [str(c) for c in collapsed],
        "can_merge_single": len(collapsed) == 1
    }

def validate_network(vpc_cidr: str, subnets: List[Dict[str, Any]], cloud_provider: str = "aws") -> List[Dict[str, Any]]:
    """Continuous validation engine for VPC & subnets."""
    issues = []
    cloud = CLOUD_SPECS.get(cloud_provider.lower(), CLOUD_SPECS["aws"])

    try:
        vpc_net = ipaddress.IPv4Network(vpc_cidr.strip(), strict=False)
    except Exception as e:
        return [{"level": "error", "title": "Invalid VPC CIDR", "message": str(e), "remediation": "Provide a valid IPv4 CIDR block such as 10.0.0.0/16."}]

    # Validate VPC Prefix limits for cloud
    if vpc_net.prefixlen < cloud["min_vpc_prefix"]:
        issues.append({
            "level": "warning",
            "title": f"VPC CIDR /{vpc_net.prefixlen} Larger Than Recommended",
            "message": f"{cloud['name']} generally recommends a minimum prefix of /{cloud['min_vpc_prefix']}.",
            "remediation": f"Adjust VPC CIDR to /{cloud['min_vpc_prefix']} or smaller block."
        })
    if vpc_net.prefixlen > cloud["max_vpc_prefix"]:
        issues.append({
            "level": "error",
            "title": f"VPC CIDR /{vpc_net.prefixlen} Too Small",
            "message": f"{cloud['name']} does not support VPC blocks smaller than /{cloud['max_vpc_prefix']}.",
            "remediation": f"Increase VPC size to between /{cloud['min_vpc_prefix']} and /{cloud['max_vpc_prefix']}."
        })

    parsed_subnets = []
    for idx, s in enumerate(subnets):
        s_cidr = s.get("cidr", "").strip()
        s_name = s.get("name", f"Subnet-{idx+1}")
        if not s_cidr:
            continue
        try:
            net = ipaddress.IPv4Network(s_cidr, strict=False)
            parsed_subnets.append({"name": s_name, "net": net, "cidr": s_cidr, "tier": s.get("tier", "private")})
        except Exception as e:
            issues.append({
                "level": "error",
                "title": f"Invalid CIDR in {s_name}",
                "message": f"'{s_cidr}' is not a valid IPv4 subnet: {str(e)}",
                "remediation": "Check IP octet format and prefix length."
            })

    # Check boundaries and containment
    for s in parsed_subnets:
        if not s["net"].subnet_of(vpc_net):
            issues.append({
                "level": "error",
                "title": f"Subnet {s['name']} Out of Range",
                "message": f"Subnet {s['cidr']} does not fit inside parent VPC CIDR {vpc_cidr}.",
                "remediation": f"Change {s['name']} IP address to fall within {vpc_net.network_address} - {vpc_net.broadcast_address}."
            })
        if s["net"].prefixlen > cloud["max_subnet_prefix"]:
            issues.append({
                "level": "error",
                "title": f"Subnet {s['name']} Too Small for {cloud['name']}",
                "message": f"Prefix /{s['net'].prefixlen} has fewer usable addresses than required by cloud infrastructure.",
                "remediation": f"Use /{cloud['max_subnet_prefix']} or larger for cloud subnets."
            })

    # Check overlaps
    for i in range(len(parsed_subnets)):
        for j in range(i + 1, len(parsed_subnets)):
            s1 = parsed_subnets[i]
            s2 = parsed_subnets[j]
            if s1["net"].overlaps(s2["net"]):
                issues.append({
                    "level": "error",
                    "title": f"Subnet Conflict: {s1['name']} & {s2['name']}",
                    "message": f"{s1['name']} ({s1['cidr']}) overlaps with {s2['name']} ({s2['cidr']}).",
                    "remediation": "Adjust subnet base addresses or prefixes so their IP ranges do not intersect."
                })

    return issues

def get_cloud_comparison(cidr_str: str) -> Dict[str, Any]:
    """Generates side-by-side comparative analysis across AWS, Azure, GCP, and RFC."""
    comparison = {}
    for key in ["aws", "azure", "gcp", "rfc"]:
        comparison[key] = calculate_cidr_details(cidr_str, cloud_provider=key)
    return comparison

def generate_terraform_hcl(vpc_name: str, vpc_cidr: str, subnets: List[Dict[str, Any]], cloud_provider: str = "aws") -> str:
    """Generates production Infrastructure as Code (Terraform HCL) for the designed VPC and subnets."""
    provider = cloud_provider.lower()
    clean_name = vpc_name.lower().replace(" ", "-")

    if provider == "aws":
        lines = [
            f"# Terraform Infrastructure for AWS VPC & Subnets: {vpc_name}",
            "terraform {",
            "  required_providers {",
            "    aws = {",
            "      source  = \"hashicorp/aws\"",
            "      version = \"~> 5.0\"",
            "    }",
            "  }",
            "}",
            "",
            f"resource \"aws_vpc\" \"{clean_name}\" {{",
            f"  cidr_block           = \"{vpc_cidr}\"",
            "  enable_dns_support   = true",
            "  enable_dns_hostnames = true",
            "  tags = {",
            f"    Name = \"{vpc_name}\"",
            "    ManagedBy = \"DevOps-CIDR-Architect\"",
            "  }",
            "}",
            "",
            f"resource \"aws_internet_gateway\" \"{clean_name}_igw\" {{",
            f"  vpc_id = aws_vpc.{clean_name}.id",
            "  tags = {",
            f"    Name = \"{vpc_name}-igw\"",
            "  }",
            "}",
            ""
        ]

        for idx, s in enumerate(subnets):
            s_name = s.get("name", f"subnet-{idx+1}").lower().replace(" ", "-")
            s_cidr = s.get("cidr", "")
            s_tier = s.get("tier", "private")
            is_public = s_tier == "public"
            az = s.get("az", "us-east-1a")

            lines.extend([
                f"resource \"aws_subnet\" \"{s_name}\" {{",
                f"  vpc_id                  = aws_vpc.{clean_name}.id",
                f"  cidr_block              = \"{s_cidr}\"",
                f"  availability_zone       = \"{az}\"",
                f"  map_public_ip_on_launch = {str(is_public).lower()}",
                "  tags = {",
                f"    Name = \"{s.get('name', s_name)}\"",
                f"    Tier = \"{s_tier}\"",
                "  }",
                "}",
                ""
            ])
        return "\n".join(lines)

    elif provider == "azure":
        lines = [
            f"# Terraform Infrastructure for Azure Virtual Network: {vpc_name}",
            f"resource \"azurerm_resource_group\" \"rg\" {{",
            f"  name     = \"rg-{clean_name}\"",
            "  location = \"East US\"",
            "}",
            "",
            f"resource \"azurerm_virtual_network\" \"{clean_name}\" {{",
            f"  name                = \"vnet-{clean_name}\"",
            f"  location            = azurerm_resource_group.rg.location",
            f"  resource_group_name = azurerm_resource_group.rg.name",
            f"  address_space       = [\"{vpc_cidr}\"]",
            "  tags = {",
            f"    Environment = \"Production\"",
            "    ManagedBy   = \"DevOps-CIDR-Architect\"",
            "  }",
            "}",
            ""
        ]

        for idx, s in enumerate(subnets):
            s_name = s.get("name", f"subnet-{idx+1}").lower().replace(" ", "-")
            s_cidr = s.get("cidr", "")
            lines.extend([
                f"resource \"azurerm_subnet\" \"{s_name}\" {{",
                f"  name                 = \"{s.get('name', s_name)}\"",
                f"  resource_group_name  = azurerm_resource_group.rg.name",
                f"  virtual_network_name = azurerm_virtual_network.{clean_name}.name",
                f"  address_prefixes     = [\"{s_cidr}\"]",
                "}",
                ""
            ])
        return "\n".join(lines)

    elif provider == "gcp":
        lines = [
            f"# Terraform Infrastructure for Google Cloud VPC: {vpc_name}",
            f"resource \"google_compute_network\" \"{clean_name}\" {{",
            f"  name                    = \"vpc-{clean_name}\"",
            "  auto_create_subnetworks = false",
            "}",
            ""
        ]
        for idx, s in enumerate(subnets):
            s_name = s.get("name", f"subnet-{idx+1}").lower().replace(" ", "-")
            s_cidr = s.get("cidr", "")
            lines.extend([
                f"resource \"google_compute_subnetwork\" \"{s_name}\" {{",
                f"  name          = \"{s_name}\"",
                f"  ip_cidr_range = \"{s_cidr}\"",
                f"  region        = \"us-central1\"",
                f"  network       = google_compute_network.{clean_name}.id",
                "}",
                ""
            ])
        return "\n".join(lines)

    else:
        return f"# Traditional On-Premise Network Plan\n# VPC/Supernet: {vpc_cidr}\n" + "\n".join([f"# Subnet: {s.get('name')} -> {s.get('cidr')}" for s in subnets])

