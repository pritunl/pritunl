provider "aws" {
    access_key = "${var.aws_access_key}"
    secret_key = "${var.aws_secret_key}"
    region = "us-east-1"
}

resource "aws_instance" "db" {
    ami = "ami-9e8f64f3"
    instance_type = "r3.large"
    availability_zone = "us-east-1e"
    vpc_security_group_ids = ["sg-19e03162"]
    subnet_id = "subnet-c1f1a8fc"
    tags = {
        "Name" = "pritunl-stress-db"
    }
}

resource "aws_route53_record" "db" {
    zone_id = "Z5BPZC3LYPA7M"
    name = "sdb.pritunl.net"
    type = "A"
    ttl = "10"
    records = ["${aws_instance.db.private_ip}"]
}

resource "aws_instance" "node" {
    count = 10
    ami = "ami-ab8d66c6"
    instance_type = "c4.large"
    availability_zone = "us-east-1e"
    vpc_security_group_ids = ["sg-48e43533"]
    subnet_id = "subnet-c1f1a8fc"
    tags = {
        "Name" = "pritunl-stress-node${count.index}"
    }
}

resource "aws_route53_record" "node" {
    count = 10
    zone_id = "Z5BPZC3LYPA7M"
    name = "sn${count.index}.pritunl.net"
    type = "A"
    ttl = "10"
    records = ["${element(aws_instance.node.*.private_ip, count.index)}"]
}

resource "aws_route53_record" "node2" {
    zone_id = "Z5BPZC3LYPA7M"
    name = "sn.pritunl.net"
    type = "A"
    ttl = "10"
    records = ["${aws_instance.node.0.public_ip}"]
}

resource "aws_instance" "client" {
    count = 20
    ami = "ami-bb806bd6"
    instance_type = "r3.xlarge"
    availability_zone = "us-east-1e"
    vpc_security_group_ids = ["sg-acfd2cd7"]
    subnet_id = "subnet-c1f1a8fc"
    tags = {
        "Name" = "pritunl-stress-client${count.index}"
    }
}

resource "aws_route53_record" "client" {
    count = 20
    zone_id = "Z5BPZC3LYPA7M"
    name = "sc${count.index}.pritunl.net"
    type = "A"
    ttl = "10"
    records = ["${element(aws_instance.client.*.public_ip, count.index)}"]
}
