from icmplib import ping, Host


def run(config):
    target = config.get("tgt_ip", None)
    count = int(config.get("count", 1))
    interval = float(config.get("interval", 1))
    timeout = float(config.get("timeout", 2))

    result = ping(
        target,
        count=count,
        interval=interval,
        timeout=timeout,
        privileged=False
    )

    return {
        "tgt_ip": target,
        "sent": result.packets_sent,
        "received": result.packets_received,
        "avg_latency": result.avg_rtt / 1000
    }
