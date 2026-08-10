from icmplib import ping

def run(config):
    target = config.get("target", None)
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
        "target": target,
        "sent": result.packets_sent,
        "received": result.packets_received,
        "avg_latency": result.avg_rtt / 1000
    }
